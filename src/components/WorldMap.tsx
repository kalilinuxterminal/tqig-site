import {useEffect,useId,useRef,useState} from 'react';
import {useReducedMotion} from 'motion/react';
import {Map as LibreMap,Marker,NavigationControl,ScaleControl,FullscreenControl,Popup,setWorkerUrl,type GeoJSONSource,type SymbolLayerSpecification} from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import {Globe2,Navigation2,RotateCcw,Map as MapIcon,Satellite,MapPin,Tags,Route as RouteIcon,Layers2,X} from 'lucide-react';
import type {Place,Route,Coordinate} from '../services/types';
import {featurePlace,routeBounds,wrapLongitude,satelliteSources} from '../services/map';
import {SearchBox} from './SearchBox';

setWorkerUrl(workerUrl);
type Props={selected:Place;onSelect?:(p:Place)=>void;savedPlaces?:Place[];route?:Route|null;vehicle?:Coordinate|null;hero?:boolean;reducedMotion?:boolean;showSelectionCard?:boolean};
type LabelPaint=NonNullable<SymbolLayerSpecification['paint']>;
type Visibility=NonNullable<SymbolLayerSpecification['layout']>['visibility'];
type BaseLabel={id:string;visibility:Visibility;color:LabelPaint['text-color'];halo:LabelPaint['text-halo-color'];haloWidth:LabelPaint['text-halo-width']};

export default function WorldMap({selected,onSelect,savedPlaces,route,vehicle,hero=false,reducedMotion=false,showSelectionCard=true}:Props){
 const systemReducedMotion=useReducedMotion();reducedMotion=reducedMotion||!!systemReducedMotion;
 const host=useRef<HTMLDivElement>(null),map=useRef<LibreMap|null>(null),pin=useRef<Marker|null>(null),car=useRef<Marker|null>(null),endpoints=useRef<Marker[]>([]);
 const callback=useRef(onSelect),current=useRef({selected,route,reducedMotion}),labels=useRef<BaseLabel[]>([]),baseLayers=useRef<{id:string;visibility:Visibility}[]>([]);
 const [error,setError]=useState(''),[loaded,setLoaded]=useState(false),[geoError,setGeoError]=useState(''),[view,setView]=useState<'map'|'satellite'>(()=>{try{return localStorage.getItem('tqig.map-view')==='satellite'?'satellite':'map';}catch{return 'map';}}),[showLabels,setShowLabels]=useState(()=>{try{return localStorage.getItem('tqig.map-labels')!=='false';}catch{return true;}}),[imageryLoading,setImageryLoading]=useState(false),[zoom,setZoom]=useState(14),[layersOpen,setLayersOpen]=useState(false);
 const layerMenu=useRef<HTMLDivElement>(null),layerButton=useRef<HTMLButtonElement>(null),mapPicked=useRef<Coordinate|null>(null),layerId=useId(),selectable=!!onSelect;
 const [searchNear,setSearchNear]=useState<Coordinate|undefined>({lat:selected.lat,lng:selected.lng});
 const imageryErrors=useRef(new Set<string>()),imageryTimer=useRef<ReturnType<typeof setTimeout>|null>(null),imageryPending=useRef(false),satelliteRef=useRef(false);
 callback.current=onSelect;current.current={selected,route,reducedMotion};satelliteRef.current=view==='satellite';

 useEffect(()=>{if(hero)return;try{localStorage.setItem('tqig.map-view',view);localStorage.setItem('tqig.map-labels',String(showLabels));}catch{/* Map preferences still work for this session. */}},[view,showLabels,hero]);
 useEffect(()=>{if(!layersOpen)return;const close=(event:PointerEvent)=>{if(!layerMenu.current?.contains(event.target as Node))setLayersOpen(false);};document.addEventListener('pointerdown',close);return()=>document.removeEventListener('pointerdown',close);},[layersOpen]);
 useEffect(()=>{if(hero)return;const focusSearch=(event:KeyboardEvent)=>{const target=event.target as HTMLElement|null;if(event.key!=='/'||event.altKey||event.ctrlKey||event.metaKey||event.isComposing||target?.closest('input,textarea,select,[contenteditable="true"]'))return;const input=host.current?.parentElement?.querySelector<HTMLInputElement>('.map-search-bar input');if(input){event.preventDefault();input.focus();}};document.addEventListener('keydown',focusSearch);return()=>document.removeEventListener('keydown',focusSearch);},[hero]);
 function chooseOnMap(place:Place){mapPicked.current=place;callback.current?.(place);}
 function centerPin(){map.current?.flyTo({center:[selected.lng,selected.lat],zoom:Math.max(14,map.current.getZoom()),bearing:0,pitch:0,duration:reducedMotion?0:650});}

 function fitRoute(instant=false){const m=map.current,r=current.current.route;if(!m||!r?.coordinates.length)return;const compact=m.getContainer().clientWidth<650;m.fitBounds(routeBounds(r.coordinates),{padding:compact?{left:35,right:85,top:145,bottom:105}:{left:370,right:85,top:100,bottom:Math.min(290,m.getContainer().clientHeight*.3)},duration:instant||current.current.reducedMotion?0:800,maxZoom:16});}

 useEffect(()=>{
  if(!host.current)return;
  let m:LibreMap|undefined,resize:ResizeObserver|undefined,hover:Popup|undefined;
  try{
   m=new LibreMap({container:host.current,style:import.meta.env.VITE_MAP_STYLE||'https://tiles.openfreemap.org/styles/liberty',center:[selected.lng,selected.lat],zoom:hero?11.7:14,attributionControl:{compact:true},renderWorldCopies:!hero,maxZoom:20});map.current=m;
   const instance=m;
   resize=new ResizeObserver(()=>{instance.resize();if(current.current.route)fitRoute(true);});resize.observe(host.current);
   instance.addControl(new NavigationControl({showCompass:!hero,visualizePitch:true}),'bottom-right');
   if(!hero){instance.addControl(new ScaleControl({maxWidth:100,unit:'imperial'}),'bottom-left');instance.addControl(new FullscreenControl({container:host.current.parentElement!}),'bottom-right');}
   instance.on('styleimagemissing',event=>{
    if(instance.hasImage(event.id))return;
    // A neutral point keeps a place visible if the provider has no category icon.
    const size=16,data=new Uint8Array(size*size*4);
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){const d=Math.hypot(x-7.5,y-7.5),i=(y*size+x)*4;if(d>6)continue;const edge=d>4.5;data.set(edge?[244,246,244,255]:[91,115,95,255],i);}
    instance.addImage(event.id,{width:size,height:size,data});
   });
   hover=new Popup({closeButton:false,closeOnClick:false,offset:16,className:'map-place-tooltip'});
   function namedFeature(point:{x:number;y:number}){return instance.queryRenderedFeatures([[point.x-3,point.y-3],[point.x+3,point.y+3]]).find(f=>f.layer.type==='symbol'&&!!featurePlace(f,{lat:0,lng:0}));}
   instance.on('load',()=>{
    if(!hero){
     labels.current=instance.getStyle().layers.filter(l=>l.type==='symbol').map(l=>({id:l.id,visibility:l.layout?.visibility||'visible',color:instance.getPaintProperty(l.id,'text-color'),halo:instance.getPaintProperty(l.id,'text-halo-color'),haloWidth:instance.getPaintProperty(l.id,'text-halo-width')}));
     baseLayers.current=instance.getStyle().layers.filter(l=>l.type!=='symbol').map(l=>({id:l.id,visibility:l.layout?.visibility||'visible'}));
     // Keep the style and all journey overlays mounted when changing the background.
     for(const [id,source] of Object.entries(satelliteSources))instance.addSource(id,source);
     const firstLabel=labels.current[0]?.id;
     instance.addLayer({id:'satellite-global',type:'raster',source:'satellite-global',layout:{visibility:'none'},paint:{'raster-fade-duration':200}},firstLabel);
     instance.addLayer({id:'satellite-us',type:'raster',source:'satellite-us',minzoom:8,layout:{visibility:'none'},paint:{'raster-fade-duration':200}},firstLabel);
    }
    setLoaded(true);setError('');
   });
   instance.on('error',e=>{
    const source='sourceId' in e?String(e.sourceId):'';
    if(source.startsWith('satellite-')){imageryErrors.current.add(source);setImageryLoading(false);setError('Some satellite images couldn’t load. Try Map view or retry satellite.');}
    else if(!hero)setError('Some map details couldn’t load. You can still choose coordinates or retry.');
   });
   instance.on('idle',()=>{if(imageryErrors.current.size===0){setError('');setImageryLoading(false);imageryPending.current=false;if(imageryTimer.current)clearTimeout(imageryTimer.current);}});
   instance.on('zoomend',()=>setZoom(instance.getZoom()));
   instance.on('moveend',()=>{const p=instance.getCenter();setSearchNear(instance.getZoom()<7?undefined:{lat:p.lat,lng:wrapLongitude(p.lng)});});
   instance.on('click',e=>{if(!callback.current)return;const point={lat:e.lngLat.lat,lng:wrapLongitude(e.lngLat.lng)},feature=namedFeature(e.point);chooseOnMap(feature?featurePlace(feature,point)!:{...point,name:'Dropped pin',region:'Map selection'});hover?.remove();setLayersOpen(false);});
   instance.on('mousemove',e=>{if(hero||!callback.current||instance.isMoving())return;const feature=namedFeature(e.point),place=feature&&featurePlace(feature,{lat:e.lngLat.lat,lng:e.lngLat.lng});instance.getCanvas().style.cursor=place?'pointer':'';if(place)hover?.setLngLat(e.lngLat).setText(place.name).addTo(instance);else hover?.remove();});
   instance.on('mouseout',()=>hover?.remove());
  }catch{setError('The map couldn’t open. Search and coordinates remain available.');}
  return()=>{if(imageryTimer.current)clearTimeout(imageryTimer.current);resize?.disconnect();hover?.remove();m?.remove();map.current=null;pin.current=null;car.current=null;setLoaded(false);};
 },[hero]);

 useEffect(()=>{
  const m=map.current;if(!m)return;pin.current?.remove();
  const el=document.createElement('div');el.className=hero?'tq-pin hero-pin':'tq-pin';el.innerHTML='<span></span>';el.setAttribute('role','img');el.setAttribute('aria-label',`Selected pin: ${selected.name}`);el.title=onSelect?'Drag to move your selected location':selected.name;
  const marker=new Marker({element:el,draggable:!!onSelect}).setLngLat([selected.lng,selected.lat]).addTo(m);pin.current=marker;
  marker.on('dragend',()=>{const p=marker.getLngLat();chooseOnMap({name:'Dropped pin',region:'Map selection',lat:p.lat,lng:wrapLongitude(p.lng)});});el.style.display=route?'none':'';
  const picked=mapPicked.current&&Math.abs(mapPicked.current.lat-selected.lat)<1e-8&&Math.abs(mapPicked.current.lng-selected.lng)<1e-8;mapPicked.current=null;
  if(!hero&&!route&&!picked)m.flyTo({center:[selected.lng,selected.lat],zoom:Math.max(13,m.getZoom()),duration:reducedMotion?0:800});
 },[selected,hero,reducedMotion,selectable]);

 useEffect(()=>{
  const m=map.current;if(!m||!loaded||hero)return;const satellite=view==='satellite';
  for(const l of baseLayers.current)if(m.getLayer(l.id))m.setLayoutProperty(l.id,'visibility',satellite?'none':l.visibility);
  for(const id of ['satellite-global','satellite-us'])if(m.getLayer(id))m.setLayoutProperty(id,'visibility',satellite?'visible':'none');
  for(const l of labels.current){if(!m.getLayer(l.id))continue;m.setLayoutProperty(l.id,'visibility',showLabels?l.visibility:'none');m.setPaintProperty(l.id,'text-color',satellite?'#ffffff':l.color);m.setPaintProperty(l.id,'text-halo-color',satellite?'#17252c':l.halo);m.setPaintProperty(l.id,'text-halo-width',satellite?1.6:l.haloWidth);}
  if(!satellite){setImageryLoading(false);imageryPending.current=false;setError('');if(imageryTimer.current)clearTimeout(imageryTimer.current);}
 },[view,showLabels,loaded,hero]);

 useEffect(()=>{
  const m=map.current;if(!m||!loaded)return;const data:GeoJSON.Feature<GeoJSON.LineString>={type:'Feature',properties:{},geometry:{type:'LineString',coordinates:route?.coordinates||[]}};
  if(m.getSource('journey'))(m.getSource('journey') as GeoJSONSource).setData(data);
  else{m.addSource('journey',{type:'geojson',data});m.addLayer({id:'route-glow',type:'line',source:'journey',paint:{'line-color':'#ffffff','line-width':10,'line-opacity':.8},layout:{'line-join':'round','line-cap':'round'}});m.addLayer({id:'route-line',type:'line',source:'journey',paint:{'line-color':'#7742db','line-width':5},layout:{'line-join':'round','line-cap':'round'}});}
  endpoints.current.forEach(p=>p.remove());endpoints.current=[];if(pin.current)pin.current.getElement().style.display=route?'none':'';
  if(route?.coordinates.length){for(const [label,c] of [['A',route.coordinates[0]],['B',route.destination||route.coordinates.at(-1)!]] as const){const el=document.createElement('div');el.className='route-endpoint '+(label==='B'?'destination':'');el.textContent=label;el.setAttribute('role','img');el.setAttribute('aria-label',label==='A'?'Route start':'Route destination');endpoints.current.push(new Marker({element:el}).setLngLat(c).addTo(m));}fitRoute();}
 },[route,loaded,reducedMotion]);

 useEffect(()=>{const m=map.current;if(!m||!vehicle){car.current?.remove();car.current=null;return;}if(!car.current){const el=document.createElement('div');el.className='vehicle-marker';el.innerHTML='<span>↑</span>';el.setAttribute('role','img');el.setAttribute('aria-label','Journey position');car.current=new Marker({element:el}).setLngLat([vehicle.lng,vehicle.lat]).addTo(m);}else car.current.setLngLat([vehicle.lng,vehicle.lat]);},[vehicle]);

 useEffect(()=>{const m=map.current;if(!m||hero)return;const markers=(savedPlaces||[]).filter(p=>p.lat!==selected.lat||p.lng!==selected.lng).map(p=>{const el=document.createElement('button');el.type='button';el.className='saved-map-pin';el.textContent='★';el.title=p.name;el.setAttribute('aria-label',`Saved place: ${p.name}`);el.addEventListener('click',e=>{e.stopPropagation();callback.current?.(p);});return new Marker({element:el}).setLngLat([p.lng,p.lat]).addTo(m);});return()=>markers.forEach(marker=>marker.remove());},[savedPlaces,selected,hero]);

 function waitForImagery(){if(imageryTimer.current)clearTimeout(imageryTimer.current);setImageryLoading(true);imageryPending.current=true;imageryTimer.current=setTimeout(()=>{if(imageryPending.current&&satelliteRef.current){setImageryLoading(false);setError('Satellite images are taking longer than expected. Try Map view or retry.');}},20000);}
 function changeView(next:'map'|'satellite'){if(next===view)return;imageryErrors.current.clear();setError('');setView(next);if(next==='satellite')waitForImagery();}
 function retry(){const m=map.current;if(!m)return;imageryErrors.current.clear();setError('');if(!loaded){m.setStyle(import.meta.env.VITE_MAP_STYLE||'https://tiles.openfreemap.org/styles/liberty');return;}if(view==='satellite'){waitForImagery();m.refreshTiles('satellite-global');m.refreshTiles('satellite-us');}else for(const id of Object.keys(m.getStyle().sources))if(!id.startsWith('satellite-')&&id!=='journey')m.refreshTiles(id);}
 function browserLocation(){setGeoError('');if(!navigator.geolocation){setGeoError('Browser location is unavailable. Select a point on the map.');return;}navigator.geolocation.getCurrentPosition(p=>callback.current?.({name:'Browser location',region:'Map only — not applied to iPhone',lat:p.coords.latitude,lng:p.coords.longitude}),()=>setGeoError('Browser location unavailable. Select a point manually.'),{timeout:10000});}

 return <div className={`world-map ${hero?'hero-world':'explorer-map'} ${view==='satellite'?'satellite-map':''}`}>
  <div ref={host} className="map-canvas"/>
  {!loaded&&!error&&<div className="map-loading"><span className="pulse-dot"/> Opening your map…</div>}
  {!hero&&<>
   {onSelect&&<div className="map-search-bar"><SearchBox shortcut="/" near={searchNear} onSelect={p=>{setLayersOpen(false);callback.current?.(p);}} placeholder="Search for a place or address"/></div>}
   <div ref={layerMenu} className="map-layer-menu" onKeyDown={e=>{if(e.key==='Escape'){e.stopPropagation();setLayersOpen(false);layerButton.current?.focus();}}}>
    <button ref={layerButton} type="button" className="map-layer-trigger" aria-expanded={layersOpen} aria-controls={layerId} onClick={()=>setLayersOpen(!layersOpen)}><Layers2 size={17}/><span>Layers</span></button>
    {layersOpen&&<div className="map-layer-panel" id={layerId}><div className="layer-panel-heading"><strong>Map appearance</strong><button aria-label="Close map layers" onClick={()=>{setLayersOpen(false);layerButton.current?.focus();}}><X size={16}/></button></div><div className="map-view-switch" role="group" aria-label="Map appearance"><button type="button" aria-pressed={view==='map'} onClick={()=>changeView('map')}><span className="layer-swatch street-swatch"><MapIcon size={22}/></span>Street</button><button type="button" aria-pressed={view==='satellite'} disabled={!loaded} onClick={()=>changeView('satellite')}><span className="layer-swatch satellite-swatch"><Satellite size={22}/></span>Satellite</button></div><button type="button" className="map-labels-toggle" aria-pressed={showLabels} disabled={!loaded} onClick={()=>setShowLabels(!showLabels)}><Tags size={16}/> Place & street labels <span className="map-toggle-indicator"/></button><div className="map-extra-actions"><button onClick={()=>{map.current?.flyTo({center:[-25,25],zoom:1.5,duration:reducedMotion?0:800});setLayersOpen(false);}}><Globe2 size={15}/> Explore the world</button>{onSelect&&<button onClick={()=>{browserLocation();setLayersOpen(false);}} title="Use browser location on map only"><Navigation2 size={15}/> Find my browser location</button>}</div><p>Satellite + aerial imagery. Dates and detail vary; global imagery is from 2016–17.</p></div>}
   </div>
   <div className="map-navigation-actions">{route?<button onClick={()=>fitRoute()}><RouteIcon size={16}/> Fit route</button>:<button onClick={centerPin}><RotateCcw size={16}/> Back to pin</button>}</div>
   {!route&&showSelectionCard&&<div className="map-selection-card"><span className="map-selection-icon"><MapPin size={19}/></span><div><small>SELECTED ON MAP</small><strong>{selected.name}</strong><span>{selected.lat.toFixed(5)}, {selected.lng.toFixed(5)}</span>{onSelect&&<em>Tap a place or drag the pin</em>}</div></div>}
   {view==='satellite'&&<div className="map-imagery-note">{imageryLoading?<><span className="pulse-dot"/> Loading imagery…</>:<>Satellite · {zoom>=14?'Detail varies':'Not live'}</>}</div>}
  </>}
  {error&&<div className="map-error" role="status"><span>{error}</span><button onClick={retry}>Retry</button></div>}
  {geoError&&<div className="geo-message" role="status">{geoError}<button aria-label="Dismiss location message" onClick={()=>setGeoError('')}>×</button></div>}
 </div>;
}
