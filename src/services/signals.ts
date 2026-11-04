import type {Route} from './types';
import {meters} from './routing';
/** Map data, not live signal phases. Requests are user-triggered and limited to modest route extents. */
export async function loadMappedSignals(route:Route):Promise<Route>{
 const xs=route.coordinates.map(p=>p[0]),ys=route.coordinates.map(p=>p[1]);const west=Math.min(...xs),east=Math.max(...xs),south=Math.min(...ys),north=Math.max(...ys);
 if(east-west>.5||north-south>.5)throw Error('Mapped-signal lookup is limited to a local route. Split this journey into shorter sections.');
 const corridor:[number,number][]=[route.coordinates[0]];let since=0;for(let i=1;i<route.coordinates.length;i++){since+=meters(route.coordinates[i-1],route.coordinates[i]);if(since>=120){corridor.push(route.coordinates[i]);since=0;}}corridor.push(route.coordinates.at(-1)!);if(corridor.length>500)throw Error('Split this journey into shorter sections for a mapped-signal lookup.');
 const query=`[out:json][timeout:12];node["highway"="traffic_signals"](around:30,${corridor.map(c=>`${c[1]},${c[0]}`).join(',')});out body;`;
 let r:Response;try{r=await fetch('https://overpass-api.de/api/interpreter',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({data:query}),signal:AbortSignal.timeout(18000)});}catch{throw Error('Traffic-light lookup is busy or offline. Your route is ready; use planned maneuver pauses or retry later.')}if(!r.ok)throw Error('Mapped signal data is unavailable. Keep using planned maneuver pauses or retry later.');const data=await r.json();if(!Array.isArray(data.elements)||data.remark)throw Error('Signal lookup did not complete. No live-light behavior has been assumed.');
 const cumulative=[0];for(let i=1;i<route.coordinates.length;i++)cumulative.push(cumulative[i-1]+meters(route.coordinates[i-1],route.coordinates[i]));const matches:number[]=[];
 for(const node of data.elements){let best=Infinity,at=0;for(let i=1;i<route.coordinates.length;i++){const a=route.coordinates[i-1],b=route.coordinates[i];const scale=Math.cos(node.lat*Math.PI/180),dx=(b[0]-a[0])*scale,dy=b[1]-a[1];const f=Math.max(0,Math.min(1,((node.lon-a[0])*scale*dx+(node.lat-a[1])*dy)/(dx*dx+dy*dy||1)));const p:[number,number]=[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f],d=meters(p,[node.lon,node.lat]);if(d<best){best=d;at=cumulative[i-1]+meters(a,p)}}if(best<22&&at>15&&at<cumulative.at(-1)!-15)matches.push(at);}
 const sorted=matches.sort((a,b)=>a-b),signals=sorted.filter((d,i)=>i===0||d-sorted[i-1]>35);return{...route,signals,signalData:'loaded'};
}
