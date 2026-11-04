import {useState} from 'react';
export function useStored<T>(key:string,fallback:T){
 const [value,setValue]=useState<T>(()=>{try{const data=JSON.parse(localStorage.getItem('tqig.'+key)||'null');if(data===null)return fallback;if(Array.isArray(fallback)){if(!Array.isArray(data))return fallback;return data.filter((v:any)=>{if(!v||typeof v.name!=='string')return false;if(key==='routes')return Array.isArray(v.coordinates)&&v.coordinates.length>1&&v.coordinates.length<50000&&v.coordinates.every((c:any)=>Array.isArray(c)&&c.length===2&&Number.isFinite(c[0])&&Number.isFinite(c[1])&&Math.abs(c[0])<=180&&Math.abs(c[1])<=90)&&Array.isArray(v.stops)&&Array.isArray(v.speeds)&&Number.isFinite(v.distance);return Number.isFinite(v.lat)&&Number.isFinite(v.lng)&&Math.abs(v.lat)<=90&&Math.abs(v.lng)<=180;}) as T;}if(key==='units'&&!['metric','imperial'].includes(data))return fallback;return data as T}catch{return fallback}});
 function set(next:T){setValue(next);try{localStorage.setItem('tqig.'+key,JSON.stringify(next))}catch{/* Preferences remain usable for this session if browser storage is full. */}}
 return[value,set] as const;
}
