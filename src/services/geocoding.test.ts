import {describe,it,expect} from 'vitest';
import {readSearchPlaces} from './geocoding';
const point=(coordinates:unknown,properties:unknown)=>({geometry:{type:'Point',coordinates},properties});
describe('search results',()=>{
 it('preserves the real point and includes an address that distinguishes nearby places',()=>{
  expect(readSearchPlaces({features:[point([-81.7662,28.555],{name:'City Hall',housenumber:'685',street:'West Montrose Street',city:'Clermont',state:'Florida',country:'United States'})]})).toEqual([{name:'City Hall',lat:28.555,lng:-81.7662,region:'685 West Montrose Street, Clermont, Florida, United States'}]);
 });
 it('rejects invalid coordinates, unnamed entries and duplicate results',()=>{
  const valid=point([0,0],{name:'Park'});
  expect(readSearchPlaces({features:[null,point([181,0],{name:'Invalid'}),point([0,'28'],{name:'Invalid'}),point([0,0],{}),valid,valid]})).toHaveLength(1);
 });
 it('rejects a malformed server response instead of presenting invented places',()=>{
  expect(()=>readSearchPlaces({error:'offline'})).toThrow();expect(readSearchPlaces({features:[]})).toEqual([]);
 });
});
