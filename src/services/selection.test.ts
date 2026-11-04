import {describe,it,expect} from 'vitest';
import {selectionReducer,coordinateText} from './selection';
import {clermont} from './types';
describe('map selection history',()=>{
 it('undoes a search and pin adjustment without losing their exact coordinates',()=>{
  const initial={current:clermont.start,past:[]};
  const searched=selectionReducer(initial,{type:'choose',place:clermont.destination});
  const adjusted=selectionReducer(searched,{type:'choose',place:{...clermont.destination,lat:28.5612001,name:'Dropped pin'}});
  expect(selectionReducer(adjusted,{type:'undo'}).current).toEqual(clermont.destination);
  expect(selectionReducer(selectionReducer(adjusted,{type:'undo'}),{type:'undo'})).toEqual(initial);
  expect(coordinateText(clermont.start)).toBe('28.555025, -81.766191');
 });
 it('ignores repeated selections and keeps history bounded',()=>{
  let state={current:clermont.start,past:[] as typeof clermont.start[]};
  expect(selectionReducer(state,{type:'undo'})).toBe(state);
  expect(selectionReducer(state,{type:'choose',place:clermont.start})).toBe(state);
  for(let i=1;i<=30;i++)state=selectionReducer(state,{type:'choose',place:{...clermont.start,lng:-81+i/1000}});
  expect(state.past).toHaveLength(15);expect(state.current.lng).toBe(-80.97);
 });
});
