import {describe,it,expect} from 'vitest';
import {featurePlace,routeBounds,wrapLongitude} from './map';

describe('map selection coordinates',()=>{
 it('uses a named landmark’s exact point instead of the label click position',()=>{
  expect(featurePlace({properties:{name:'Waterfront Park',class:'park'},geometry:{type:'Point',coordinates:[-81.75975,28.56115]}},{lng:-81.76,lat:28.56})).toMatchObject({name:'Waterfront Park',lng:-81.75975,lat:28.56115});
 });
 it('keeps the clicked position for a road or area label',()=>{
  expect(featurePlace({properties:{name:'West Montrose Street'},geometry:{type:'LineString',coordinates:[[-81.77,28.55],[-81.76,28.55]]}},{lng:-81.765,lat:28.5502})).toMatchObject({name:'West Montrose Street',lng:-81.765,lat:28.5502});
 });
 it('ignores unnamed features and prefers an available English label',()=>{
  expect(featurePlace({properties:{},geometry:{type:'Point',coordinates:[0,0]}},{lat:1,lng:2})).toBeNull();
  expect(featurePlace({properties:{name:'東京','name:en':'Tokyo'},geometry:{type:'Point',coordinates:[139.7,35.6]}},{lat:0,lng:0})?.name).toBe('Tokyo');
 });
 it('normalizes pins selected on repeated world copies',()=>{
  expect(wrapLongitude(540)).toBe(-180);expect(wrapLongitude(-541)).toBe(179);
  expect(featurePlace({properties:{name:'Place'},geometry:{type:'Point',coordinates:[280,28]}},{lng:0,lat:0})?.lng).toBe(-80);
 });
});
describe('route framing',()=>{
 it('frames a Clermont route and a route crossing the international date line',()=>{
  expect(routeBounds([[-81.77,28.55],[-81.76,28.56]])).toEqual([[-81.77,28.55],[-81.76,28.56]]);
  const [[west,south],[east,north]]=routeBounds([[179.8,10],[-179.9,11],[-179.7,10.5]]);
  expect(east-west).toBeCloseTo(.5);expect(south).toBe(10);expect(north).toBe(11);
 });
});
