import {useCallback,useReducer} from 'react';
import {selectionReducer} from '../services/selection';
import type {Place} from '../services/types';
export function usePlaceSelection(initial:Place){
 const [state,dispatch]=useReducer(selectionReducer,{current:initial,past:[]});
 const choose=useCallback((place:Place)=>dispatch({type:'choose',place}),[]);
 const undo=useCallback(()=>dispatch({type:'undo'}),[]);
 return {place:state.current,choose,undo,canUndo:state.past.length>0};
}
