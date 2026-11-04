export type Place={name:string;region:string;lat:number;lng:number};
export type Coordinate={lat:number;lng:number};
export type TripPhase='outbound'|'stay'|'return'|'complete';
export type TripSettings={walkKmh:number;stayMinutes:number;returnToStart:boolean;profile?:Profile;customKmh?:number};
export type TripSummary={outboundDuration:number;stayDuration:number;returnDuration:number;outboundDistance:number;returnDistance:number;returnToStart:boolean;travelMode:'walking'|'driving'};
export type Frame=Coordinate&{t:number;distance:number;speed:number;event?:'move'|'signal'|'intersection'|'arrival'|'stay';phase?:TripPhase};
export type Route={id:string;coordinates:[number,number][];distance:number;duration:number;speeds:number[];stops:number[];signals?:number[];signalData?:'loaded'|'unavailable'|'not-requested';name:string;returnRoute?:Route;tripSettings?:TripSettings;destination?:[number,number];tripPoints?:Place[]};
export type Profile='walk'|'cycle'|'city'|'highway'|'custom';
export type Journey={state:string;mode:string;index:number;frame:Frame|null;totalFrames:number;duration:number;totalDistance:number;error:string|null;playbackRate:number;elapsed?:number;phase?:TripPhase;phaseRemaining?:number;acknowledgedSamples?:number;trip?:TripSummary|null};
export type DeviceStatus={holdRefreshes?:number;acknowledgedLocationWrites?:number;state:string;connection:string;simulation:string;device:null|{id:string;name:string;ios:string;build:string;transport:string};lastAcceptedCoordinates:Coordinate|null;error:string|null;serverTime:number;journey:Journey;portableAvailable:boolean;portableObservation:unknown};
export const initialStatus:DeviceStatus={state:'disconnected',connection:'disconnected',simulation:'unknown',device:null,lastAcceptedCoordinates:null,error:null,serverTime:0,journey:{state:'idle',mode:'device',index:0,frame:null,totalFrames:0,duration:0,totalDistance:0,error:null,playbackRate:1},portableAvailable:false,portableObservation:null};
export const clermont={start:{name:'Clermont City Hall',region:'Clermont, Florida',lat:28.5550254,lng:-81.7661906},destination:{name:'Waterfront Park',region:'Clermont, Florida',lat:28.5611545,lng:-81.7597498}} satisfies Record<string,Place>;
export const places:Place[]=[{...clermont.start,name:'Clermont'}, {name:'London',region:'United Kingdom',lat:51.5074,lng:-.1278},{name:'Tokyo',region:'Japan',lat:35.6762,lng:139.6503},{name:'Paris',region:'France',lat:48.8566,lng:2.3522},{name:'Sydney',region:'Australia',lat:-33.8688,lng:151.2093},{name:'Cape Town',region:'South Africa',lat:-33.9249,lng:18.4241}];
export function parseCoordinates(q:string):Place|null{const m=q.trim().match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);if(!m)return null;const lat=Number(m[1]),lng=Number(m[2]);return Math.abs(lat)<=90&&Math.abs(lng)<=180?{name:'Custom location',region:'Coordinates',lat,lng}:null}
export const distanceLabel=(m:number,units='metric')=>units==='imperial'?`${(m/1609.344).toFixed(1)} mi`:`${(m/1000).toFixed(1)} km`;
export const timeLabel=(seconds:number)=>seconds>=3600?`${Math.floor(seconds/3600)}h ${Math.round(seconds%3600/60)}m`:`${Math.max(0,Math.round(seconds/60))} min`;
