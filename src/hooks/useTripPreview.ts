import {useEffect,useMemo,useRef,useState} from 'react';
import {sampleTrip,type TripPlan} from '../services/trip';
import type {Route} from '../services/types';
export function useTripPreview(plan:TripPlan|null,outbound:Route|null,back:Route|null,rate:number){
 const [state,setState]=useState('idle'),[elapsed,setElapsed]=useState(0),clock=useRef(0);
 useEffect(()=>{clock.current=0;setElapsed(0);setState('idle')},[plan]);
 useEffect(()=>{if(state!=='playing'||!plan)return;let raf=0,last=performance.now();const end=plan.frames.at(-1)!.t;function tick(now:number){const dt=Math.min(.2,(now-last)/1000);last=now;clock.current=Math.min(end,clock.current+dt*rate);setElapsed(clock.current);if(clock.current>=end){setState('arrived');return}raf=requestAnimationFrame(tick)}raf=requestAnimationFrame(tick);return()=>cancelAnimationFrame(raf)},[state,plan,rate]);
 const frame=useMemo(()=>plan&&outbound?sampleTrip(plan,outbound,back,elapsed):null,[plan,outbound,back,elapsed]);
 return{state,elapsed,frame,start(){if(state!=='paused'){clock.current=0;setElapsed(0)}setState('playing')},pause(){setState('paused')},stop(){setState('stopped');clock.current=0;setElapsed(0)}};
}
