// Sample-aligned multi-stem playback: every track starts at the same AudioContext time, and
// toggles change gains without restarting, so stems never drift apart.

export interface Track {
  key: string;
  url: string;
  gain: number;
}

export class Player {
  private ctx: AudioContext | null = null;
  private readonly cache = new Map<string, Promise<AudioBuffer>>();
  private readonly nodes = new Map<string, { source: AudioBufferSourceNode; gain: GainNode }>();
  private startedAt = 0;
  private offset = 0;
  private duration = 0;
  private token = 0;
  onEnded: (() => void) | null = null;

  private context(): AudioContext {
    this.ctx ??= new AudioContext();
    return this.ctx;
  }

  load(url: string): Promise<AudioBuffer> {
    let buffer = this.cache.get(url);
    if (!buffer) {
      buffer = fetch(url)
        .then((response) => {
          if (!response.ok) throw new Error(`${url}: ${response.status}`);
          return response.arrayBuffer();
        })
        .then((bytes) => this.context().decodeAudioData(bytes));
      buffer.catch(() => this.cache.delete(url));
      this.cache.set(url, buffer);
    }
    return buffer;
  }

  get playing(): boolean {
    return this.nodes.size > 0;
  }

  get time(): number {
    if (!this.ctx || !this.playing) return this.offset;
    return Math.min(this.duration, this.offset + this.ctx.currentTime - this.startedAt);
  }

  async play(tracks: Track[], offset: number, duration: number): Promise<void> {
    this.stop();
    const ctx = this.context();
    if (ctx.state === "suspended") await ctx.resume();
    const token = ++this.token;
    const buffers = await Promise.all(tracks.map((track) => this.load(track.url)));
    if (token !== this.token) return; // a newer play or stop happened while decoding
    this.duration = duration;
    this.offset = Math.max(0, Math.min(offset, duration - 0.05));
    this.startedAt = ctx.currentTime + 0.06;
    tracks.forEach((track, i) => {
      const buffer = buffers[i] as AudioBuffer;
      const source = ctx.createBufferSource();
      const gain = ctx.createGain();
      source.buffer = buffer;
      gain.gain.value = track.gain;
      source.connect(gain).connect(ctx.destination);
      if (this.offset < buffer.duration) source.start(this.startedAt, this.offset);
      this.nodes.set(track.key, { source, gain });
    });
    // Every stem of a combination has the same length, so the first one marks the end.
    const first = [...this.nodes.values()].at(0)?.source;
    if (first) first.onended = () => { if (token === this.token) this.finish(); };
  }

  setGain(key: string, value: number) {
    const node = this.nodes.get(key);
    if (node && this.ctx) node.gain.gain.setTargetAtTime(value, this.ctx.currentTime, 0.015);
  }

  /** Stop and remember the position so the next play can resume from it. */
  stop() {
    this.offset = this.time;
    this.token++;
    for (const { source } of this.nodes.values()) {
      source.onended = null;
      try { source.stop(); } catch { /* already stopped */ }
    }
    this.nodes.clear();
  }

  rewind() {
    this.stop();
    this.offset = 0;
  }

  private finish() {
    this.stop();
    this.offset = 0;
    this.onEnded?.();
  }
}
