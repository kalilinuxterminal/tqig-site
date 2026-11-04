import type {Place} from './types';
export type PlaceSelection={current:Place;past:Place[]};
export type SelectionAction={type:'choose';place:Place}|{type:'undo'};
export function selectionReducer(state:PlaceSelection,action:SelectionAction):PlaceSelection{
 if(action.type==='undo')return state.past.length?{current:state.past.at(-1)!,past:state.past.slice(0,-1)}:state;
 const next=action.place,old=state.current;
 if(old.lat===next.lat&&old.lng===next.lng&&old.name===next.name&&old.region===next.region)return state;
 return {current:next,past:[...state.past,old].slice(-15)};
}
export const coordinateText=(place:Pick<Place,'lat'|'lng'>)=>`${place.lat.toFixed(6)}, ${place.lng.toFixed(6)}`;
