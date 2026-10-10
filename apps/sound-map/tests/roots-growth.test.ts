import { expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
const html=readFileSync(new URL('../../../experiments/silver_page.html',import.meta.url),'utf8');
const source=html.slice(html.indexOf('const rootsPlans'),html.indexOf('// ------------------------------------------------------------ state'));
const {rootsPlan,rootsGrowth,rootsAnchor}=new Function('TAU',source+';return {rootsPlan,rootsGrowth,rootsAnchor}')(Math.PI*2);
const quiet={level:[0,0,0],time_s:[0,.5,1],hz:[null,null,null]};
const sparse={level:[0,1,0,0,0,0,0,0],time_s:[0,.1,.2,.3,.4,.5,.6,.7],hz:Array(8).fill(1000)};
const full={...sparse,level:[.5,.8,1,.6,.9,.7,1,.8],hz:[500,1800,900,2200,1000,800,1700,500]};
test('Roots uses sound to choose head count, size and supporting width',()=>{
 expect(rootsPlan(quiet)).toHaveLength(0);const a=rootsPlan(sparse),b=rootsPlan(full);expect(b.length).toBeGreaterThan(a.length);
 expect(new Set(b.map((h:any)=>h.size)).size).toBeGreaterThan(1);
 for(const h of b){expect(h.size).toBeCloseTo(1.35+1.35*h.intensity);expect(h.width).toBeGreaterThanOrEqual(.72);}
 expect(new Set(b.map((h:any)=>h.angle)).size).toBe(b.length);
});
test('Roots grows progressively with finite geometry and valid faces',()=>{
 const plan=rootsPlan(full),frame={theta_start:3.281};
 expect(rootsGrowth(plan,-1,frame).positions.length).toBe(0);
 const a=rootsGrowth(plan,.35,frame),b=rootsGrowth(plan,Infinity,frame);
 expect(b.positions.length).toBeGreaterThan(a.positions.length);
 expect(Array.from(b.positions as Float32Array).every(Number.isFinite)).toBe(true);
 expect(Array.from(b.indices as Uint32Array).every(i=>i<b.positions.length/3)).toBe(true);
});

test('distinct waveform peaks determine count and softmax changes placement',()=>{
 const signal={level:[0,.4,0,.8,0,1,0],time_s:[0,.1,.2,.3,.4,.5,.6],hz:[]};
 const plan=rootsPlan(signal);expect(plan).toHaveLength(3);
 expect(plan.map((p:any)=>p.time)).toEqual([.1,.3,.5]);
 expect(plan[2].size).toBeGreaterThan(plan[0].size);
 const reversed=rootsPlan({...signal,level:[0,1,0,.8,0,.4,0]});
 expect(plan.map((p:any)=>p.angle)).not.toEqual(reversed.map((p:any)=>p.angle));
});
test('even early growth keeps stems at least 1.2 mm across',()=>{
 const plan=rootsPlan(full).slice(0,1);const mesh=rootsGrowth(plan,plan[0].time+.001,{theta_start:3.281});
 for(let k=0;k<25;k++)for(let j=0;j<6;j++){
 const a=(k*12+j)*3,b=a+18,p=mesh.positions;
 expect(Math.hypot(p[a]-p[b],p[a+1]-p[b+1],p[a+2]-p[b+2])).toBeGreaterThan(1.19999);
 }
});

test('every stem enters the band and overlaps its cup wall',()=>{
 const frame={theta_start:3.281,rootsSurface:new Float32Array([8,0,0,-10,1,0,0,0,9])};
 const plan=rootsPlan(full),data=rootsGrowth(plan,Infinity,frame).positions;
 const stride=(25*12+35*40+11*16)*3;
 for(let j=0;j<plan.length;j++){
  const center=(row:number)=>[0,1,2].map(c=>{let sum=0;for(let n=0;n<12;n++)sum+=data[j*stride+row*12*3+n*3+c]/12;return sum;}) as [number,number,number];
  const start=center(0),onBand=center(4),source=frame.rootsSurface;let closest=Infinity,second=Infinity;
  for(let i=0;i<source.length;i+=3){closest=Math.min(closest,Math.hypot(start[0]-source[i]!,start[1]-source[i+1]!,start[2]-source[i+2]!));second=Math.min(second,Math.hypot(onBand[0]-source[i]!,onBand[1]-source[i+1]!,onBand[2]-source[i+2]!));}
  expect(closest).toBeCloseTo(.65,4);expect(second).toBeLessThan(.00001);
  const end=center(24),pole=j*stride+25*12*3;
  expect(Math.hypot(end[0]-data[pole],end[1]-data[pole+1],end[2]-data[pole+2])).toBeCloseTo(.35,4);
 }
});

test('stalk junctions follow the current band surface',()=>{
 const plan=rootsPlan(full).slice(0,1);
 const band=new Float32Array([8,0,0,-10,1,0,0,0,9]);
 const original=rootsGrowth(plan,Infinity,{theta_start:3.281,rootsSurface:band}).positions;
 const shifted=new Float32Array(band);
 for(let i=1;i<shifted.length;i+=3)shifted[i]!+=1.5;
 const moved=rootsGrowth(plan,Infinity,{theta_start:3.281,rootsSurface:shifted}).positions;
 // Ring four is the stalk's entry point into the actual displayed metal.
 for(let n=0;n<12;n++)expect(moved[(4*12+n)*3+1]!-original[(4*12+n)*3+1]!).toBeCloseTo(1.5,4);
});

test('waveform placements stay on the shoulders outside the open front',()=>{
 const frame={theta_start:3.281,span:5.986};
 const plan=rootsPlan(full),mesh=rootsGrowth(plan,Infinity,frame).positions;
 const stride=(25*12+35*40+11*16)*3;
 for(let j=0;j<plan.length;j++){
  let x=0,z=0;for(let n=0;n<12;n++){x+=mesh[j*stride+(24*12+n)*3]!/12;z+=mesh[j*stride+(24*12+n)*3+2]!/12;}
  const angle=(Math.atan2(-z,x)+2*Math.PI)%(2*Math.PI),arc=(angle-frame.theta_start+2*Math.PI)%(2*Math.PI);
  expect(arc).toBeGreaterThan(.1);expect(arc).toBeLessThan(frame.span-.1);
 }
});


test('each mushroom has a small rounded base bead embedded in the band',()=>{
 const plan=rootsPlan(full).slice(0,1),band=new Float32Array([8,0,0,-10,1,0,0,0,9]);
 const data=rootsGrowth(plan,Infinity,{theta_start:3.281,rootsSurface:band}).positions;
 const north=(25*12+35*40)*3,south=north+10*16*3;
 const center=[(data[north]+data[south])/2,(data[north+1]+data[south+1])/2,(data[north+2]+data[south+2])/2];
 let distance=Infinity;
 for(let i=0;i<band.length;i+=3)distance=Math.min(distance,Math.hypot(center[0]!-band[i]!,center[1]!-band[i+1]!,center[2]!-band[i+2]!));
 expect(distance).toBeLessThan(.00001);
 const radius=(data[north+1]-data[south+1])/2;
 expect(radius).toBeGreaterThanOrEqual(.74999);
 expect(radius).toBeLessThanOrEqual(1.00001);
});