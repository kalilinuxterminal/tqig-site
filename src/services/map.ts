import type {RasterSourceSpecification} from 'maplibre-gl';
import type {Coordinate,Place} from './types';

// The 2016–17 mosaic is CC BY 4.0. Later EOX mosaics have different terms.
export const satelliteSources:Record<string,RasterSourceSpecification>={
 'satellite-global':{type:'raster',tiles:['https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg'],tileSize:256,maxzoom:13,attribution:'<a href="https://s2maps.eu">Sentinel-2 cloudless</a> by <a href="https://maps.eox.at">EOX IT Services GmbH</a> (Contains modified Copernicus Sentinel data 2016 &amp; 2017) · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'},
 'satellite-us':{type:'raster',tiles:['https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}'],tileSize:256,minzoom:8,maxzoom:16,bounds:[-124.8,24.4,-66.9,49.4],attribution:'USDA, <a href="https://www.usgs.gov/programs/national-geospatial-program/national-map">USGS The National Map: Orthoimagery</a>'},
};

export const wrapLongitude=(lng:number)=>((lng+180)%360+360)%360-180;
type NamedFeature={properties?:Record<string,unknown>|null;geometry:{type:string;coordinates?:unknown}};
export function featurePlace(feature:NamedFeature,clicked:Coordinate):Place|null{
 const p=feature.properties||{};
 const name=[p['name:en'],p.name_en,p.name,p.ref].find(v=>typeof v==='string'&&v.trim()) as string|undefined;
 if(!name)return null;
 const point=feature.geometry.type==='Point'?feature.geometry.coordinates:null;
 const coordinate=Array.isArray(point)&&Number.isFinite(point[0])&&Number.isFinite(point[1])?{lng:wrapLongitude(point[0]),lat:point[1]}:clicked;
 const kind=typeof p.class==='string'?p.class.replaceAll('_',' '):'Place';
 return {...coordinate,name:name.trim(),region:kind.charAt(0).toUpperCase()+kind.slice(1)+' · Map selection'};
}

// Unwrap adjacent points so a short journey across ±180° doesn't zoom out to the whole world.
export function routeBounds(coordinates:[number,number][]):[[number,number],[number,number]]{
 if(!coordinates.length)return [[0,0],[0,0]];
 let previous=coordinates[0][0],west=previous,east=previous,south=coordinates[0][1],north=south;
 for(const [lng,lat] of coordinates){const unwrapped=previous+wrapLongitude(lng-previous);west=Math.min(west,unwrapped);east=Math.max(east,unwrapped);south=Math.min(south,lat);north=Math.max(north,lat);previous=unwrapped;}
 return [[west,south],[east,north]];
}
