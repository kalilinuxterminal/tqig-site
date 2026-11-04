import {useEffect,useState} from 'react';
import {Check,Copy,Undo2} from 'lucide-react';
import type {Place} from '../services/types';
import {coordinateText} from '../services/selection';
export function PlaceQuickActions({place,onUndo,canUndo}:{place:Place;onUndo:()=>void;canUndo:boolean}){
 const [copied,setCopied]=useState(false),[message,setMessage]=useState('');
 useEffect(()=>{setCopied(false);setMessage('');},[place.lat,place.lng]);
 useEffect(()=>{if(!message)return;const timer=setTimeout(()=>{setCopied(false);setMessage('');},3000);return()=>clearTimeout(timer);},[message]);
 async function copy(){try{await navigator.clipboard.writeText(coordinateText(place));setCopied(true);setMessage('Coordinates copied.');}catch{setMessage('Copy is unavailable. Select the coordinates above to copy them.');}}
 return <div className="place-quick-actions"><div><button type="button" onClick={()=>void copy()}>{copied?<Check size={14}/>:<Copy size={14}/>} {copied?'Copied':'Copy coordinates'}</button><button type="button" onClick={onUndo} disabled={!canUndo} aria-label="Undo map selection" title="Go back to your previous map selection"><Undo2 size={14}/> Undo pin</button></div><p role="status">{message}</p></div>;
}
