import type {Place,Route,Profile,Frame} from './types';
export const meters=(a:[number,number],b:[number,number])=>{const rad=Math.PI/180,dlat=(b[1]-a[1])*rad,dlng=(b[0]-a[0])*rad;const h=Math.sin(dlat/2)**2+Math.cos(a[1]*rad)*Math.cos(b[1]*rad)*Math.sin(dlng/2)**2;return 6371000*2*Math.atan2(Math.sqrt(h),Math.sqrt(Math.max(0,1-h)))};
let lastRequest=0;
export async function fetchRoutes(points:Place[],profile:Profile,signal?:AbortSignal):Promise<Route[]>{
 if(points.length<2||points.length>8)throw Error('Choose a start and destination, with up to six stops.');
 const wait=Math.max(0,1100-(Date.now()-lastRequest));if(wait)await new Promise<void>((resolve,reject)=>{const timer=setTimeout(resolve,wait);signal?.addEventListener('abort',()=>{clearTimeout(timer);reject(new DOMException('Cancelled','AbortError'))},{once:true})});if(signal?.aborted)throw new DOMException('Cancelled','AbortError');lastRequest=Date.now();
 const mode=profile==='walk'?'foot':profile==='cycle'?'bike':'car';
 const base=import.meta.env.VITE_ROUTING_BASE||'https://routing.openstreetmap.de';
 const endpoint=`${base}/routed-${mode}/route/v1/driving/${points.map(p=>`${p.lng},${p.lat}`).join(';')}?overview=full&geometries=geojson&steps=true&annotations=distance,duration,speed&alternatives=${points.length===2}`;
 const r=await fetch(endpoint,{signal:signal||AbortSignal.timeout(20000)});if(!r.ok)throw Error('The road-routing service is unavailable. Try again shortly.');const data=await r.json();if(data.code!=='Ok'||!data.routes?.length)throw Error('No connected road route found for these places. Try closer points on land.');
 return data.routes.slice(0,3).map((raw:any,index:number)=>{const coords=raw.geometry.coordinates as [number,number][];if(coords.length>50000)throw Error('This route is too large. Split it into shorter journeys.');const cumulative=[0];for(let i=1;i<coords.length;i++)cumulative.push(cumulative[i-1]+meters(coords[i-1],coords[i]));const stops:number[]=[];
 for(const leg of raw.legs)for(const step of leg.steps||[]){if(['turn','end of road','roundabout','arrive'].includes(step.maneuver?.type)){const loc=step.maneuver.location as [number,number];let nearest=0,min=Infinity;coords.forEach((c,i)=>{const d=meters(c,loc);if(d<min){min=d;nearest=i}});if(cumulative[nearest]>20&&cumulative[nearest]<cumulative.at(-1)!-20)stops.push(cumulative[nearest]);}}
 return {id:`route-${index}`,coordinates:coords,distance:cumulative.at(-1)!,duration:raw.duration,speeds:raw.legs.flatMap((leg:any)=>leg.annotation?.speed||[]),stops:[...new Set(stops)].sort((a,b)=>a-b),name:raw.legs.map((l:any)=>l.summary).filter(Boolean).join(' → ')||`Road route ${index+1}`};});
}
const distanceCache=new WeakMap<Route,number[]>();
export function pointAt(route:Route,distance:number):[number,number]{let cumulative=distanceCache.get(route);if(!cumulative){cumulative=[0];for(let i=1;i<route.coordinates.length;i++)cumulative.push(cumulative[i-1]+meters(route.coordinates[i-1],route.coordinates[i]));distanceCache.set(route,cumulative)}const target=Math.max(0,Math.min(distance,cumulative.at(-1)!));let low=1,high=cumulative.length-1;while(low<high){const mid=(low+high)>>1;if(cumulative[mid]<target)low=mid+1;else high=mid}const a=route.coordinates[low-1],b=route.coordinates[low],length=cumulative[low]-cumulative[low-1],f=length?(target-cumulative[low-1])/length:0;return[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f]}

export function buildTimeline(route:Route,profile:Profile,customKmh=50,intersectionStops=true,walkKmh=5):Frame[]{
 if(route.coordinates.length<2||route.coordinates.length>50000||route.coordinates.some(c=>!Number.isFinite(c[0])||!Number.isFinite(c[1])||Math.abs(c[0])>180||Math.abs(c[1])>90))throw Error('Route geometry is invalid or too large. Choose a shorter road journey.');
 const cap=({walk:Math.min(8,Math.max(1,walkKmh)),cycle:18,city:50,highway:105,custom:Math.min(160,Math.max(1,customKmh))}[profile])/3.6;
 const lengths=route.coordinates.slice(1).map((p,i)=>meters(route.coordinates[i],p));const total=lengths.reduce((a,b)=>a+b,0);if(total<1)throw Error('Start and destination are too close.');
 const frames:Frame[]=[];let distance=0,t=0,speed=0,segment=0,segmentStart=0,stopIndex=0;
 const signals=intersectionStops&&profile!=='walk'?(route.signals||[]).filter(d=>Number.isFinite(d)&&d>0&&d<total):[];
 const stops=[...(intersectionStops&&profile!=='walk'?route.stops.filter(d=>Number.isFinite(d)&&d>0&&d<total&&!signals.some(s=>Math.abs(s-d)<35)):[]),...signals,total].sort((a,b)=>a-b);
 const add=(v:number,event:Frame['event']='move')=>{const p=pointAt(route,distance);frames.push({lat:p[1],lng:p[0],t,distance,speed:v,event})};add(0);
 while(distance<total-.01){if(t>=28795||frames.length>=29990)throw Error('This journey exceeds the 8-hour simulation limit. Choose a shorter route.');
 while(segment<lengths.length-1&&distance>segmentStart+lengths[segment]){segmentStart+=lengths[segment++];}
 const roadEstimate=route.speeds.length===lengths.length?route.speeds[segment]:cap;
 const limit=Math.min(cap,profile==='walk'||profile==='cycle'?cap:Math.max(2,roadEstimate));
 const stop=stops[stopIndex],remaining=Math.max(0,stop-distance),brake=Math.sqrt(2*1.8*remaining);
 const target=Math.min(limit,brake);speed=Math.max(0,Math.max(speed-1.8,Math.min(target,speed+.9)));
 const step=Math.min(remaining,Math.max(.15,speed));distance+=step;t+=1;add(speed);
 if(stop-distance<.05){distance=stop;const isSignal=signals.some(s=>Math.abs(s-stop)<1);const event:Frame['event']=distance>=total?'arrival':isSignal?'signal':'intersection';frames[frames.length-1]={...frames.at(-1)!,distance,speed:0,event};speed=0;stopIndex++;if(distance<total){const dwell=isSignal?Math.max(8,35-((Math.floor(stop/10)+t)%28)):2;for(let wait=0;wait<dwell;wait++){t+=1;add(0,event);}}}
 }
 frames[frames.length-1]={...frames.at(-1)!,lat:route.coordinates.at(-1)![1],lng:route.coordinates.at(-1)![0],distance:total,speed:0,event:'arrival'};return frames;
}
