import {describe,it,expect} from 'vitest';
import {buildTimeline,meters,pointAt} from './routing';
import {parseCoordinates,type Route} from './types';
const route:Route={id:'test',name:'Synthetic Clermont-area road',coordinates:[[-81.766,28.555],[-81.766,28.557],[-81.764,28.557]],distance:390,duration:50,speeds:[8,8],stops:[200]};
describe('road timeline',()=>{
 it('is deterministic and ends at the actual destination',()=>{const a=buildTimeline(route,'city'),b=buildTimeline(route,'city');expect(a).toEqual(b);expect(a.at(-1)).toMatchObject({lat:28.557,lng:-81.764,speed:0});expect(a[0].t).toBe(0)});
 it('keeps monotonic time and distance and respects speed/acceleration limits',()=>{const frames=buildTimeline(route,'city');for(let i=1;i<frames.length;i++){expect(frames[i].t).toBeGreaterThan(frames[i-1].t);expect(frames[i].distance).toBeGreaterThanOrEqual(frames[i-1].distance);expect(frames[i].speed).toBeLessThanOrEqual(50/3.6+.001);expect(frames[i].speed-frames[i-1].speed).toBeLessThanOrEqual(.91)}});
 it('walks more slowly than city driving and pauses at a planned maneuver',()=>{const walk=buildTimeline(route,'walk'),car=buildTimeline(route,'city');expect(walk.at(-1)!.t).toBeGreaterThan(car.at(-1)!.t);expect(car.some((f,i)=>i>0&&f.speed===0&&f.distance<car.at(-1)!.distance)).toBe(true)});
 it('interpolates on the road geometry instead of cutting across the turn',()=>{const corner=meters(route.coordinates[0],route.coordinates[1]);const p=pointAt(route,corner/2);expect(p[0]).toBe(-81.766);expect(p[1]).toBeCloseTo(28.556,5);const p2=pointAt(route,corner+10);expect(p2[1]).toBeCloseTo(28.557,5)});
 it('rejects a zero-distance journey',()=>expect(()=>buildTimeline({...route,coordinates:[[0,0],[0,0]]},'walk')).toThrow());
 it('uses a multi-second planned signal stop without claiming live phases',()=>{const frames=buildTimeline({...route,signals:[180]},'city');const stopped=frames.filter(f=>f.event==='signal');expect(stopped.length).toBeGreaterThan(8);expect(stopped.every(f=>f.speed===0)).toBe(true);expect(new Set(stopped.map(f=>f.distance)).size).toBe(1)});
});
describe('coordinates',()=>{it('accepts signed coordinates and rejects nonfinite or out-of-range values',()=>{expect(parseCoordinates('-33.8,151.2')).toMatchObject({lat:-33.8,lng:151.2});for(const text of ['91,0','0,-181','NaN,4','1,2,3'])expect(parseCoordinates(text)).toBeNull()})});
