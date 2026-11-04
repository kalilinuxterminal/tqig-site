import {useEffect,useId,useRef,useState} from 'react';
import {Search,X,MapPin,LoaderCircle} from 'lucide-react';
import {parseCoordinates,type Place,type Coordinate} from '../services/types';
import {searchPlaces} from '../services/geocoding';

export function SearchBox({onSelect,placeholder='Search a city, address, or coordinates',compact=false,disabled=false,near,shortcut}:{onSelect:(p:Place)=>void;placeholder?:string;compact?:boolean;disabled?:boolean;near?:Coordinate;shortcut?:string}){
 const [q,setQ]=useState(''),[results,setResults]=useState<Place[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[active,setActive]=useState(0),[open,setOpen]=useState(false);
 const id=useId(),root=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  setResults([]);setError('');setBusy(false);setActive(0);
  const coordinate=parseCoordinates(q);if(coordinate){setResults([coordinate]);return;}
  if(q.trim().length<2)return;
  if(/^-?\d+[\d.\s]*,/.test(q)){setError('Latitude: −90 to 90. Longitude: −180 to 180.');return;}
  const controller=new AbortController(),timer=setTimeout(async()=>{
   setBusy(true);
   try{const places=await searchPlaces(q,controller.signal,near);if(controller.signal.aborted)return;setResults(places);if(!places.length)setError('No places found. Try a nearby city or coordinates.');}
   catch{if(!controller.signal.aborted)setError('Search is unavailable. You can still choose a spot on the map.');}
   finally{if(!controller.signal.aborted)setBusy(false);}
  },400);
  return()=>{clearTimeout(timer);controller.abort();};
 },[q,near?.lat,near?.lng]);
 function select(p:Place){onSelect(p);setQ('');setResults([]);setOpen(false);}
 const expanded=!disabled&&open&&!!q&&(results.length>0||!!error);
 return <div ref={root} className={'search '+(compact?'compact':'')} onBlur={e=>{if(!root.current?.contains(e.relatedTarget))setOpen(false);}}>
  <div className="search-input"><Search size={18}/><input disabled={disabled} autoComplete="off" spellCheck={false} aria-label={placeholder} role="combobox" aria-autocomplete="list" aria-keyshortcuts={shortcut} aria-expanded={expanded} aria-controls={id} aria-activedescendant={expanded&&results[active]?`${id}-${active}`:undefined} value={q} placeholder={placeholder} onFocus={()=>setOpen(true)} onChange={e=>{setQ(e.target.value);setOpen(true);}} onKeyDown={e=>{
   if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();setOpen(true);setActive(i=>results.length?(i+(e.key==='ArrowDown'?1:-1)+results.length)%results.length:0);}
   if(e.key==='Enter'){const p=parseCoordinates(q)||results[active];if(p&&open){e.preventDefault();select(p);}}
   if(e.key==='Escape'){e.preventDefault();setOpen(false);}
  }}/>{busy?<LoaderCircle className="spin" size={16}/>:q?<button type="button" aria-label="Clear search" onClick={()=>{setQ('');setOpen(false);root.current?.querySelector('input')?.focus();}}><X size={16}/></button>:<kbd className="search-key-hint" title={shortcut?`Press ${shortcut} to search`:undefined}>{shortcut||'↵'}</kbd>}</div>
  {expanded&&<div className="search-results" id={id} role="listbox" aria-label="Place results">{results.map((p,i)=><button type="button" id={`${id}-${i}`} key={`${p.lat},${p.lng},${i}`} role="option" tabIndex={-1} aria-selected={active===i} onMouseDown={e=>e.preventDefault()} onMouseEnter={()=>setActive(i)} onClick={()=>select(p)}><span className="search-pin"><MapPin size={17}/></span><span>{p.name}<small>{p.region}</small></span><span>↗</span></button>)}{error&&<p role="status">{error}</p>}</div>}
 </div>;
}
