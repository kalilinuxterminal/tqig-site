import {buildTimeline,meters,pointAt} from './routing';
import type {Frame,Profile,Route,TripPhase,TripSettings,TripSummary} from './types';
export type TripPlan={frames:Frame[];summary:TripSummary;mapRoute:Route};
export function buildTripPlan(outbound:Route,back:Route|null,profile:Profile,settings:TripSettings,customKmh=50,stops=true):TripPlan{
 if(!Number.isFinite(settings.stayMinutes)||settings.stayMinutes<0||settings.stayMinutes>240)throw Error('Choose a destination stay from 0 to 240 minutes.');
 if(!Number.isFinite(settings.walkKmh)||settings.walkKmh<1||settings.walkKmh>8)throw Error('Choose a walking speed from 1 to 8 km/h.');
 if(settings.returnToStart&&!back)throw Error('Build the return route before starting this round trip.');
 const outward=buildTimeline(outbound,profile,customKmh,stops,settings.walkKmh);const outLast=outward.at(-1)!;
 const stay=Math.round(settings.stayMinutes*60),homeward=settings.returnToStart&&back?buildTimeline(back,profile,customKmh,stops,settings.walkKmh):[];
 if(homeward.length){if(meters([outLast.lng,outLast.lat],[homeward[0].lng,homeward[0].lat])>20)throw Error('The return route starts on a different road. Adjust the destination and rebuild.');if(meters([outward[0].lng,outward[0].lat],[homeward.at(-1)!.lng,homeward.at(-1)!.lat])>20)throw Error('The return route does not finish near the starting point. Adjust the start and rebuild.');}
 const summary:TripSummary={outboundDuration:outLast.t,stayDuration:stay,returnDuration:homeward.at(-1)?.t||0,outboundDistance:outLast.distance,returnDistance:homeward.at(-1)?.distance||0,returnToStart:settings.returnToStart,travelMode:profile==='walk'?'walking':'driving'};
 const frames:Frame[]=outward.map(f=>({...f,phase:'outbound'}));
 frames[frames.length-1]={...frames.at(-1)!,phase:stay?'stay':homeward.length?'return':'complete',event:stay?'stay':'arrival'};
 if(stay)frames.push({...outLast,t:outLast.t+stay,speed:0,phase:homeward.length?'return':'complete',event:'stay'});
 for(const f of homeward.slice(1))frames.push({...f,t:outLast.t+stay+f.t,distance:outLast.distance+f.distance,phase:'return'});
 frames[frames.length-1]={...frames.at(-1)!,phase:'complete',event:'arrival',speed:0};
 if(frames.length>30000||frames.at(-1)!.t>28800)throw Error('Travel plus stay exceeds the 8-hour / 30,000-sample limit. Shorten the trip or stay.');
 const coordinates=homeward.length&&back?[...outbound.coordinates,...back.coordinates.slice(1)]:outbound.coordinates;
 return{frames,summary,mapRoute:{...outbound,coordinates,destination:outbound.coordinates.at(-1)!,distance:summary.outboundDistance+summary.returnDistance,name:outbound.name+(homeward.length?' · round trip':'')}};
}
export function tripPhase(summary:TripSummary,elapsed:number,complete=false):{phase:TripPhase;remaining:number}{if(complete)return{phase:'complete',remaining:0};if(elapsed<summary.outboundDuration)return{phase:'outbound',remaining:summary.outboundDuration-elapsed};if(elapsed<summary.outboundDuration+summary.stayDuration)return{phase:'stay',remaining:summary.outboundDuration+summary.stayDuration-elapsed};if(summary.returnToStart)return{phase:'return',remaining:Math.max(0,summary.outboundDuration+summary.stayDuration+summary.returnDuration-elapsed)};return{phase:'complete',remaining:0}}
export function sampleTrip(plan:TripPlan,outbound:Route,back:Route|null,elapsed:number):Frame{const frames=plan.frames;let low=0,high=frames.length-1;while(low<high){const mid=(low+high)>>1;if(frames[mid].t<elapsed)low=mid+1;else high=mid}const b=frames[low],a=frames[Math.max(0,low-1)],fraction=b.t===a.t?0:Math.max(0,Math.min(1,(elapsed-a.t)/(b.t-a.t))),distance=a.distance+(b.distance-a.distance)*fraction;
 const {phase}=tripPhase(plan.summary,elapsed,elapsed>=frames.at(-1)!.t);let p:[number,number];if(phase==='stay')p=outbound.coordinates.at(-1)!;else if(phase==='return'&&back)p=pointAt(back,Math.max(0,distance-plan.summary.outboundDistance));else if(phase==='complete')p=plan.summary.returnToStart&&back?back.coordinates.at(-1)!:outbound.coordinates.at(-1)!;else p=pointAt(outbound,distance);
 return{lat:p[1],lng:p[0],t:elapsed,distance,speed:phase==='stay'||phase==='complete'?0:a.speed+(b.speed-a.speed)*fraction,phase,event:phase==='stay'?'stay':phase==='complete'?'arrival':a.event};
}
export function paceLabel(kmh:number,units='metric'){const seconds=Math.round((units==='imperial'?1.609344:1)*3600/kmh);return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')} min/${units==='imperial'?'mi':'km'}`}
