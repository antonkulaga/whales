// Which parts are sounding now, and how fresh each onset is: drives the ripples on the map.

export interface Pulse {
  part: number;
  onset_s: number;
  age_s: number; // 0 at the onset, rising to `lifetime`
}

/** Index of the first value greater than `t` in a sorted array. */
export function upperBound(sorted: number[], t: number): number {
  let low = 0;
  let high = sorted.length;
  while (low < high) {
    const mid = (low + high) >> 1;
    if ((sorted[mid] as number) <= t) low = mid + 1;
    else high = mid;
  }
  return low;
}

/** Onsets in (t − lifetime, t] for every audible part, newest last. */
export function activePulses(onsetsByPart: number[][], t: number, lifetime: number, audible: (part: number) => boolean): Pulse[] {
  const out: Pulse[] = [];
  onsetsByPart.forEach((onsets, part) => {
    if (!audible(part)) return;
    for (let i = upperBound(onsets, t) - 1; i >= 0; i--) {
      const onset = onsets[i] as number;
      const age = t - onset;
      if (age >= lifetime) break;
      out.push({ part, onset_s: onset, age_s: age });
    }
  });
  return out.sort((a, b) => b.age_s - a.age_s);
}

/** A part is "sounding" while t lies inside its placed span on the timeline. */
export function soundingParts(spans: { start_s: number; length_s: number }[], t: number): number[] {
  return spans.flatMap((span, index) => (t >= span.start_s && t < span.start_s + span.length_s ? [index] : []));
}
