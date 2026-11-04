import type {Coordinate,Place} from './types';

export function readSearchPlaces(data:unknown):Place[]{
 if(!data||typeof data!=='object'||!('features' in data)||!Array.isArray(data.features))throw Error('Invalid search response');
 const places:Place[]=[],seen=new Set<string>();
 for(const feature of data.features){
  const c=feature?.geometry?.coordinates,p=feature?.properties;
  if(feature?.geometry?.type!=='Point'||!Array.isArray(c)||!Number.isFinite(c[0])||!Number.isFinite(c[1])||Math.abs(c[0])>180||Math.abs(c[1])>90||!p)continue;
  const name=[p.name,p.street,p.city].find(v=>typeof v==='string'&&v.trim());if(!name)continue;
  const key=`${name}:${c[0]},${c[1]}`;if(seen.has(key))continue;seen.add(key);
  const address=p.street?[p.housenumber,p.street].filter(v=>typeof v==='string').join(' '):'';
  const region=[...new Set([address,p.city,p.state,p.country].filter(v=>typeof v==='string'&&v.trim()&&v!==name))].join(', ');
  places.push({name:name.trim(),region,lat:c[1],lng:c[0]});if(places.length===6)break;
 }
 return places;
}

export async function searchPlaces(query:string,signal:AbortSignal,near?:Coordinate){
 const params=new URLSearchParams({q:query.trim(),limit:'6'});
 if(near&&Number.isFinite(near.lat)&&Number.isFinite(near.lng)){params.set('lat',near.lat.toFixed(6));params.set('lon',near.lng.toFixed(6));}
 const response=await fetch(`https://photon.komoot.io/api/?${params}`,{signal:AbortSignal.any([signal,AbortSignal.timeout(10000)])});
 if(!response.ok)throw Error('Search unavailable');
 return readSearchPlaces(await response.json());
}
