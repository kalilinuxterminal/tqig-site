export type ScoreEntry={score:number;at:number};
export type ScoreLog={initialScore:number|null;goal:number|null;entries:ScoreEntry[]};
export const emptyScoreLog:ScoreLog={initialScore:null,goal:null,entries:[]};
const validTime=(value:number)=>Number.isSafeInteger(value)&&value>0&&value<=8_640_000_000_000_000;
const validScore=(value:unknown):value is number=>typeof value==='number'&&Number.isSafeInteger(value)&&value>=0&&value<=999_999_999_999;

export function readScoreLog(value:unknown):ScoreLog{
 if(!value||typeof value!=='object')return {...emptyScoreLog,entries:[]};
 const raw=value as Partial<ScoreLog>;
 const entries=Array.isArray(raw.entries)?raw.entries.slice(-100).filter((entry):entry is ScoreEntry=>!!entry&&validScore(entry.score)&&validTime(entry.at)).map(({score,at})=>({score,at})).sort((a,b)=>a.at-b.at):[];
 return {initialScore:entries.length?(validScore(raw.initialScore)?raw.initialScore:entries[0].score):null,goal:validScore(raw.goal)&&raw.goal>0?raw.goal:null,entries};
}

export function parseManualScore(value:string):number{
 const clean=value.replace(/[,\s]/g,'');
 if(!/^\d{1,12}$/.test(clean))throw Error('Enter a whole number, such as 12,500.');
 const score=Number(clean);
 if(!validScore(score))throw Error('Enter a valid score.');
 return score;
}

export function addScore(log:ScoreLog,score:number,goal:number|null,at=Date.now()):ScoreLog{
 if(!validScore(score)||goal!==null&&(!validScore(goal)||goal===0)||!validTime(at))throw Error('Check the score and goal, then try again.');
 const clean=readScoreLog(log);
 return {initialScore:clean.initialScore??score,goal,entries:[...clean.entries,{score,at}].slice(-100)};
}

export function scoreSummary(log:ScoreLog){
 const latest=log.entries.at(-1)?.score??null;
 const change=latest!==null&&log.initialScore!==null?latest-log.initialScore:0;
 const remaining=latest!==null&&log.goal!==null?Math.max(0,log.goal-latest):null;
 const progress=latest===null||log.goal===null||log.initialScore===null?0:latest>=log.goal?100:log.goal<=log.initialScore?0:Math.max(0,Math.min(100,Math.round((latest-log.initialScore)/(log.goal-log.initialScore)*100)));
 return {latest,change,remaining,progress};
}

export function scoreChartPoints(entries:ScoreEntry[]):[number,number][]{
 const recent=entries.slice(-14);
 if(!recent.length)return [];
 const low=Math.min(...recent.map(e=>e.score)),span=Math.max(1,Math.max(...recent.map(e=>e.score))-low);
 return recent.map((entry,index)=>[24+index*632/Math.max(1,recent.length-1),174-(entry.score-low)/span*140]);
}
