import { expect, test } from "bun:test";
import { readFileSync } from "node:fs";
const template = readFileSync(new URL("../../../experiments/silver_page.html", import.meta.url), "utf8");
const source = template.slice(template.indexOf("function inlineSpine("), template.indexOf("// The usual audio-reactive move"));
const prep = template.slice(template.indexOf("function prepare("), template.indexOf("// The map:"));
const circular = (v: number[], t: number) => { const x=t/(2*Math.PI)*v.length-.5,j=Math.floor(x),f=x-j; const at=(i:number)=>v[(i%v.length+v.length)%v.length]!;return at(j)*(1-f)+at(j+1)*f; };
const { prepare, inlineSpine, neutralInline, inlineWave, inlineNodes, inlineSupportNodes, sampleSpine, bendSpine } = new Function("circular","TAU",`${prep}\n${source}\nreturn {prepare,inlineSpine,neutralInline,inlineWave,inlineNodes,inlineSupportNodes,sampleSpine,bendSpine}`)(circular,2*Math.PI);
const html=readFileSync(new URL("../demo/silver/index.html",import.meta.url),"utf8");
const piece=JSON.parse(html.match(/<script id="silver-data" type="application\/json">([\s\S]*?)<\/script>/)![1]!).pieces.find((p:any)=>p.id==='inline');
const packed=Buffer.from(piece.positions_f32,'base64');
const positions=new Float32Array(packed.buffer.slice(packed.byteOffset,packed.byteOffset+packed.byteLength));
const ib=Buffer.from(piece.indices,'base64');
const indices=Array.from({length:ib.length/(piece.index_bits/8)},(_,i)=>piece.index_bits===16?ib.readUInt16LE(i*2):ib.readUInt32LE(i*4));
const separated=positions, P=prepare(separated,piece.frame), S=inlineSpine(P,piece.frame), mesh=neutralInline(separated,indices,P,piece.frame,S), Q=prepare(mesh.positions,piece.frame);Q.spine=S;
test('the supplied base keeps its two capped ends separate and is retained exactly',()=>{
 expect(Array.from(mesh.positions.slice(0,positions.length))).toEqual(Array.from(separated));
 let lower=-Infinity,upper=Infinity;
 for(let i=0;i<positions.length;i+=3){const x=positions[i]!,z=positions[i+2]!;
  if(x>-4.9){if(z<10.515)lower=Math.max(lower,z);else upper=Math.min(upper,z);}
 }
 expect(upper-lower).toBeGreaterThan(.09);
 expect(piece.opening_cut.source).toBe('+baseinline.stl');
 expect(piece.opening_cut.gap_mm).toBeGreaterThan(.119);

 expect(Array.from(mesh.indices.slice(0,indices.length))).toEqual(indices);
 const stl=readFileSync(new URL('../demo/silver/media/baseinline-separated.stl',import.meta.url));
 expect(stl.readUInt32LE(80)*3).toBe(indices.length);
 for(let face=0;face<indices.length/3;face++)for(let j=0;j<3;j++)for(let c=0;c<3;c++)expect(positions[indices[face*3+j]!*3+c]).toBe(stl.readFloatLE(84+face*50+12+j*12+c*4));
 const neutral=new Float64Array(Q.n*3),sound=neutral.slice();bendSpine(Q,{wave:[0,0],nodes:[]},4,neutral);bendSpine(Q,{wave:[1,1],nodes:[]},4,sound);
 expect(Array.from(sound.slice(0,positions.length))).toEqual(Array.from(neutral.slice(0,positions.length)));
 // No new tube surface fills the space between the separately capped tips.
 for(let i=S.tubeFirst;i<S.tubeEnd;i++){
   const x=piece.frame.center[0]+neutral[i*3+2]!,z=piece.frame.center[2]-neutral[i*3]!;
   expect(x<=-4.9 || z<=lower || z>=upper).toBe(true);
 }
 const oppositeTip=[] as number[];
 for(let i=0;i<positions.length;i+=3)if(positions[i]!>-4.9&&positions[i+2]!<10.515)oppositeTip.push(i);
 let clearance=Infinity;
 for(let i=S.tubeEnd-64*S.tubeSides;i<S.tubeEnd;i++){
  const x=piece.frame.center[0]+neutral[i*3+2]!,y=piece.frame.center[1]+neutral[i*3+1]!,z=piece.frame.center[2]-neutral[i*3]!;
  for(const j of oppositeTip)clearance=Math.min(clearance,Math.hypot(x-positions[j]!,y-positions[j+1]!,z-positions[j+2]!));
 }
 expect(clearance).toBeGreaterThan(.1);

});
test('the middle line starts and ends at the supplied wire, without extending to the ring tips',()=>{
 const guide=piece.frame.inline_guide;
 expect(S.start).toBeCloseTo(piece.frame.theta_start+piece.frame.span*guide.u_start,10);
 expect(S.span).toBeCloseTo(piece.frame.span*(guide.u_end-guide.u_start),10);
 for(const k of [0,1024]){
   expect(S.centerR[k]).toBe(guide.radius[k]);
   expect(S.centerH[k]).toBe(guide.height[k]);
 }
 const neutral=new Float64Array(Q.n*3);
 bendSpine(Q,{wave:[0,0],nodes:[]},2,neutral);
 for(const k of [0,1024]){
   const first=(S.tubeFirst+k*S.tubeSides)*3;
   let x=0,y=0,z=0;
   for(let j=0;j<S.tubeSides;j++){
     x+=neutral[first+3*j]!/S.tubeSides;
     y+=neutral[first+3*j+1]!/S.tubeSides;
     z+=neutral[first+3*j+2]!/S.tubeSides;
   }
   expect(Math.hypot(x,z)).toBeCloseTo(guide.radius[k],3);
   expect(y).toBeCloseTo(guide.height[k],3);
 }
 expect(Math.abs(S.centerR[1024]-piece.frame.inline_ends[1].radius)).toBeGreaterThan(2);
});
test('every neutral spine sample follows the supplied wire centerline exactly',()=>{
 const guide=piece.frame.inline_guide;
 expect(guide.source).toBe('++baseinline.stl');
 expect(guide.u_start).toBeGreaterThan(.12);
 expect(guide.u_end).toBeGreaterThan(.98);
 expect(S.centerR).toEqual(guide.radius);
 expect(S.centerH).toEqual(guide.height);
 expect(Math.min(...S.centerR)).toBeLessThan(piece.frame.bore[0]); // No hidden bore-clearance offset.
 for(let k=1;k<1024;k++)expect(Math.abs(S.centerR[k+1]-2*S.centerR[k]+S.centerR[k-1])).toBeLessThan(.01);
});
test('only the free wire end curves into the base with a full-width attachment',()=>{
 expect(piece.frame.inline_anchor_gap_mm).toBeGreaterThan(2.6);
 expect(S.anchorEnd-S.anchorFirst).toBe(33*12);
 const neutral=new Float64Array(Q.n*3),sound=neutral.slice();
 bendSpine(Q,{wave:[0,0],nodes:[]},4,neutral);
 bendSpine(Q,{wave:[0,1,0],nodes:[]},4,sound);
 const center=(k:number)=>{
  const xyz=[0,0,0];
  for(let j=0;j<12;j++)for(let c=0;c<3;c++)xyz[c]!+=neutral[3*(S.anchorFirst+12*k+j)+c]!/12;
  return xyz;
 };
 const distance=(a:number[],b:number[])=>Math.hypot(...a.map((x,c)=>x-b[c]!));
 expect(distance(center(0),piece.frame.inline_anchor_stage)).toBeLessThan(.001);
 const wire=[S.centerR[0]*Math.cos(S.start),S.centerH[0],-S.centerR[0]*Math.sin(S.start)];
 expect(distance(center(32),wire)).toBeLessThan(.2);
 const start=center(0),middle=center(16),finish=center(32);
 const chord=[finish[0]!-start[0]!,finish[2]!-start[2]!];
 const bend=Math.abs(chord[0]!*(middle[2]!-start[2]!)-chord[1]!*(middle[0]!-start[0]!))/Math.hypot(...chord);
 expect(bend).toBeGreaterThan(.6); // A visible arc, not a nearly straight strut.
 const leaving=[center(1)[0]!-start[0]!,center(1)[2]!-start[2]!];
 const bandTangent=[-start[2]!,start[0]!];
 const bodyAlignment=(leaving[0]! * bandTangent[0]! + leaving[1]! * bandTangent[1]!)/(Math.hypot(...leaving)*Math.hypot(...bandTangent));
 expect(bodyAlignment).toBeGreaterThan(.8); // The root follows the band's curve as it emerges.
 const tangent=(a:number[],b:number[])=>a.map((x,c)=>x-b[c]!);
 const bridgeTangent=tangent(center(32),center(31)),wireTangent=tangent(
  [S.centerR[1]*Math.cos(S.start+S.span/1024),S.centerH[1],-S.centerR[1]*Math.sin(S.start+S.span/1024)],wire);
 const alignment=bridgeTangent.reduce((sum,x,c)=>sum+x*wireTangent[c]!,0)/(Math.hypot(...bridgeTangent)*Math.hypot(...wireTangent));
 expect(alignment).toBeGreaterThan(.95);
 for(let k=0;k<33;k+=4)for(let j=0;j<6;j++){
  const a=3*(S.anchorFirst+12*k+j),b=a+18;
  expect(distance(Array.from(neutral.slice(a,a+3)),Array.from(neutral.slice(b,b+3)))).toBeCloseTo(1,5);
 }
 for(let i=S.anchorFirst*3;i<S.anchorEnd*3;i++)expect(sound[i]).toBe(neutral[i]);
});
test('bent spine keeps its full one millimetre diameter',()=>{
 const out=new Float64Array(Q.n*3);bendSpine(Q,{wave:[0,1,0,.7,0],nodes:[]},4,out);
 for(let k=0;k<=1024;k+=4)for(let j=0;j<6;j++){
 const a=(S.tubeFirst+k*12+j)*3,b=a+18;
 expect(Math.hypot(out[a]!-out[b]!,out[a+1]!-out[b+1]!,out[a+2]!-out[b+2]!)).toBeCloseTo(1,5);
 }
});
test('connections join sound peaks to the rails and disappear in neutral',()=>{
 const a=new Float64Array(Q.n*3),neutral=a.slice();bendSpine(Q,{wave:[1,1],nodes:[.5]},4,a);bendSpine(Q,{wave:[0,0],nodes:[.5]},4,neutral);
 const u=.5;
 const slot=inlineSupportNodes(S,[1,1],4,[.5]).indexOf(.5);
 for(const rib of S.ribs.filter((r:any)=>r.slot===slot)){
 const center=(k:number)=>{const c=[0,0,0];for(let j=0;j<rib.sides;j++)for(let d=0;d<3;d++)c[d]!+=a[(rib.first+k*rib.sides+j)*3+d]!/rib.sides;return c;};
 const start=center(0),end=center(rib.steps),rail=S.rails[rib.sign<0?0:1];
 expect(Math.hypot(start[0]!,start[2]!)).toBeCloseTo((sampleSpine(S.centerR,u)+4),5);expect(start[1]).toBeCloseTo(sampleSpine(S.centerH,u),5);
 expect(Math.hypot(end[0]!,end[2]!)).toBeCloseTo(sampleSpine(rail.map((p:number[])=>p[0]),u),5);expect(end[1]).toBeCloseTo(sampleSpine(rail.map((p:number[])=>p[1]),u),5);
 for(let k=1;k<(rib.steps+1)*rib.sides;k++)for(let c=0;c<3;c++)expect(neutral[(rib.first+k)*3+c]).toBe(neutral[rib.first*3+c]);
 }
});
test('supplementary supports bound the actual bent spine gaps to four millimetres',()=>{
 const center=(wave:number[],gain:number,u:number)=>{
  const sample=(values:number[])=>{const x=u*(values.length-1),i=Math.floor(x),f=x-i;return values[i]!*(1-f)+values[Math.min(i+1,values.length-1)]!*f;};
  const angle=S.start+S.span*u,r=sample(S.centerR)+gain*sample(wave);
  return [r*Math.cos(angle),sample(S.centerH),-r*Math.sin(angle)];
 };
 for(const sound of [
  {time_s:[0,1],duration_s:1,level:[1,1],hz:[512,512]},
  {time_s:[0,4],duration_s:4,level:[1,1],hz:[8000,8000]},
  {time_s:[0,.4,.6,1],duration_s:1,level:[1,0,0,1],hz:[512,512,512,512]},
 ])for(const gain of [1,2,6]){
  const wave=inlineWave(sound),peaks=inlineNodes(wave),nodes=inlineSupportNodes(S,wave,gain,peaks);
  expect(nodes.length).toBeLessThanOrEqual(S.supportSlots);
  for(const peak of peaks)expect(nodes).toContain(peak);
  const anchors=[0,...nodes,1];
  for(let i=1;i<anchors.length;i++){
   const a=anchors[i-1]!,b=anchors[i]!;let length=0,previous=center(wave,gain,a);
   for(let k=1;k<=128;k++){const p=center(wave,gain,a+(b-a)*k/128);length+=Math.hypot(...p.map((v,c)=>v-previous[c]!));previous=p;}
   expect(length).toBeLessThanOrEqual(S.maxSupportGap+.01);
  }
 }
 expect(inlineSupportNodes(S,[0,0],6,[])).toEqual([]);
});
test('every cross-line has spherical joints at both ends and reveals with playback',()=>{
 const wave=[1,1],nodes=inlineSupportNodes(S,wave,4,[.5]),out=new Float64Array(Q.n*3),neutral=out.slice();
 bendSpine(Q,{wave,nodes:[.5],supportWave:wave,reveal:.5},4,out);
 bendSpine(Q,{wave:[0,0],nodes:[.5],supportWave:wave},4,neutral);
 for(const rib of S.ribs){
  const active=rib.slot<nodes.length&&nodes[rib.slot]<=.5;
  for(let end=0;end<2;end++){
   const joint=rib.joints[end],c=[0,0,0],row=end?rib.steps:0;
   for(let j=0;j<rib.sides;j++)for(let d=0;d<3;d++)c[d]!+=out[(rib.first+row*rib.sides+j)*3+d]!/rib.sides;
   for(let k=0;k<=joint.rings;k++)for(let j=0;j<joint.sides;j++){
    const i=(joint.first+k*joint.sides+j)*3;
    expect(Math.hypot(out[i]!-c[0]!,out[i+1]!-c[1]!,out[i+2]!-c[2]!)).toBeCloseTo(active?.5:0,5);
    for(let d=0;d<3;d++)expect(neutral[i+d]).toBe(neutral[rib.first*3+d]);
   }
  }
 }
 expect(Array.from(out).every(Number.isFinite)).toBe(true);
 expect(Array.from(mesh.indices as Uint32Array).every(i=>i<Q.n)).toBe(true);
});
test('measured frequency sets peak count; silence and unreached audio stay neutral',()=>{
 const sound={time_s:[0,1],duration_s:1,level:[1,1],hz:[1024,1024]};
 const peaks=(v:number[])=>v.filter((x,i)=>i>0&&i<v.length-1&&x>v[i-1]!&&x>=v[i+1]!).length;
 expect(peaks(Array.from(inlineWave(sound)))).toBe(2);expect(inlineNodes(inlineWave(sound))).toHaveLength(2);expect(peaks(Array.from(inlineWave({...sound,hz:[2048,2048]})))).toBe(4);
 expect(Array.from(inlineWave({...sound,level:[0,0]})).every(v=>v===0)).toBe(true);
 expect(Array.from(inlineWave(sound,.4)).slice(430).every(v=>v===0)).toBe(true);
 expect(inlineWave({...sound,hz:[null,null]})[512]).toBe(1);
});
