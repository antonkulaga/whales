/** Shared by the integrated viewer and its regression/benchmark harness. */
export const SILVER_AUDIO_RUNTIME = `
const orchestraFeatures = new Map();
async function measureOrchestra(decoded) {
  // The full timeline is retained; bound its resolution to the ring's 1024 samples.
  // Keep the original 5 ms hop for short recordings and at most 4096 frames for music.
  const channels = Array.from({ length: decoded.numberOfChannels }, (_, i) => decoded.getChannelData(i).slice());
  const workerSource = [
    "const TAU=" + TAU + ",BAND=" + JSON.stringify(BAND) + ",TONALITY_DB=" + TONALITY_DB + ",F=" + JSON.stringify(F) + ";",
    fft.toString(), spectralFrame.toString(), normalise.toString(), analyse.toString(),
    "onmessage=({data})=>{try { const mono=new Float32Array(data.channels[0].length); for(const channel of data.channels) for(let i=0;i<mono.length;i++) mono[i]+=channel[i]/data.channels.length; postMessage({features:analyse(mono,data.rate,4096)}); } catch(error) { postMessage({error:error.message}); }};"
  ].join("\\n");
  const url = URL.createObjectURL(new Blob([workerSource], { type: "text/javascript" }));
  const worker = new Worker(url);
  try {
    return await new Promise((resolve, reject) => {
      worker.onmessage = ({data}) => data.error ? reject(new Error(data.error)) : resolve(data.features);
      worker.onerror = event => reject(new Error(event.message || "The piece could not be measured."));
      worker.postMessage({ channels, rate: decoded.sampleRate }, channels.map(c => c.buffer));
    });
  } finally { worker.terminate(); URL.revokeObjectURL(url); }
}
`;
