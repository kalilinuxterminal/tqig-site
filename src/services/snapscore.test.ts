import {describe,it,expect} from 'vitest';
import {emptyScoreLog,parseManualScore,readScoreLog,addScore,scoreSummary,scoreChartPoints} from './snapscore';

describe('manual Snapscore records',()=>{
 it('accepts copied score formatting and rejects invalid or unsafe values',()=>{
  expect(parseManualScore('12,500')).toBe(12500);
  expect(parseManualScore(' 0 ')).toBe(0);
  for(const invalid of ['', '-1','1.5','1e3','9999999999999','hello'])expect(()=>parseManualScore(invalid)).toThrow();
 });
 it('shows progress only from manually logged scores',()=>{
  expect(scoreSummary(emptyScoreLog).latest).toBeNull();
  let log=addScore(emptyScoreLog,12500,15000,1000);
  expect(scoreSummary(log).progress).toBe(0);
  log=addScore(log,12850,15000,2000);
  expect(scoreSummary(log)).toEqual({latest:12850,change:350,remaining:2150,progress:14});
  log=addScore(log,15100,15000,3000);
  expect(scoreSummary(log).progress).toBe(100);
  expect(scoreSummary(log).remaining).toBe(0);
 });
 it('filters malformed saved data and retains the first baseline across bounded history',()=>{
  expect(readScoreLog('bad')).toEqual(emptyScoreLog);
  const clean=readScoreLog({initialScore:10,goal:100,entries:[{score:-1,at:1},{score:20.5,at:2},{score:30,at:'bad'},{score:40,at:4}]});
  expect(clean.entries).toEqual([{score:40,at:4}]);
  let log=addScore(emptyScoreLog,10,1000,1);
  for(let i=2;i<=110;i++)log=addScore(log,i,1000,i);
  expect(log.entries).toHaveLength(100);
  expect(log.initialScore).toBe(10);
 });
 it('allows correction of a manual entry without inventing positive progress',()=>{
  const log=addScore(addScore(emptyScoreLog,100,200,1),90,200,2);
  expect(scoreSummary(log).change).toBe(-10);
  expect(scoreSummary(log).progress).toBe(0);
  expect(()=>addScore(log,1,-2,3)).toThrow();
 });
 it('keeps increasing, flat and decreasing chart values inside the chart',()=>{
  expect(scoreChartPoints([{score:12500,at:1},{score:12850,at:2}])).toEqual([[24,174],[656,34]]);
  for(const scores of [[1,1],[999999999999,0],[0,999999999999]]){
   const points=scoreChartPoints(scores.map((score,i)=>({score,at:i+1})));
   expect(points.every(([x,y])=>Number.isFinite(x)&&Number.isFinite(y)&&x>=24&&x<=656&&y>=34&&y<=174)).toBe(true);
  }
 });
});
