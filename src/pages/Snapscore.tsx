import {useMemo,useState,type FormEvent} from 'react';
import {ArrowUpRight,TrendingUp,Target,Plus,ExternalLink,Check,Clock3} from 'lucide-react';
import {WorkspaceShell} from './Workspace';
import {useStored} from '../hooks/useStored';
import {addScore,emptyScoreLog,parseManualScore,readScoreLog,scoreSummary,scoreChartPoints,type ScoreEntry} from '../services/snapscore';

const format=(value:number)=>value.toLocaleString();
const when=(at:number)=>new Date(at).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});

function ScoreChart({entries}:{entries:ScoreEntry[]}){
 const recent=entries.slice(-14);
 if(recent.length<2)return <div className="score-chart-empty"><TrendingUp size={30}/><strong>Your progress starts here.</strong><p>Log two scores to see your trend.</p></div>;
 const points=scoreChartPoints(recent);
 const line=points.map(([x,y],i)=>(i?'L':'M')+x+','+y).join(' ');
 return <><svg className="score-chart" viewBox="0 0 680 206" role="img" aria-label="Trend of your manually logged scores"><defs><linearGradient id="score-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#f4dd70" stopOpacity=".19"/><stop offset="1" stopColor="#f4dd70" stopOpacity="0"/></linearGradient></defs>{[34,104,174].map(y=><path key={y} d={'M24,'+y+'H656'} className="score-chart-grid"/>)}<path d={line+' L656,190 L24,190 Z'} fill="url(#score-fill)"/><path d={line} pathLength="1" className="score-chart-line"/>{points.map(([cx,cy],i)=><circle key={i} cx={cx} cy={cy} r={i===points.length-1?5:3} fill="#f4dd70"/>)}</svg><div className="score-chart-labels"><span>{when(recent[0].at)}</span><span>{when(recent.at(-1)!.at)}</span></div></>;
}

export default function Snapscore(){
 const [stored,setStored]=useStored<unknown>('snapscore',null);
 const log=useMemo(()=>readScoreLog(stored),[stored]),summary=scoreSummary(log);
 const [score,setScore]=useState(''),[goal,setGoal]=useState(log.goal===null?'':String(log.goal)),[error,setError]=useState(''),[saved,setSaved]=useState(false),[resetting,setResetting]=useState(false);
 function submit(e:FormEvent){
  e.preventDefault();setError('');setSaved(false);
  try{const nextScore=parseManualScore(score),nextGoal=goal.trim()?parseManualScore(goal):null;if(nextGoal===0)throw Error('Choose a goal above zero, or leave it blank.');setStored(addScore(log,nextScore,nextGoal));setScore('');setSaved(true)}catch(e){setError((e as Error).message)}
 }
 return <WorkspaceShell title="Snapscore" subtitle="Your activity. Your progress.">
  <main className="portal-main score-page">
   <section className="score-intro"><span className="score-badge"><TrendingUp size={13}/> MANUAL TRACKER</span><h2>A little progress,<br/><em>worth keeping.</em></h2><p>Log the score shown in Snapchat and follow your progress here.</p><div className="score-honesty"><strong>Automatic boosting isn’t available.</strong><span>This tracker does not send Snaps or change your Snapchat score.</span></div></section>
   <div className="score-stats"><article><span>Last logged score</span><strong>{summary.latest===null?'—':format(summary.latest)}</strong><small>{log.entries.length?'Entered by you':'No score logged yet'}</small></article><article><span>Change since first log</span><strong className={summary.change>0?'score-positive':''}>{summary.latest===null?'—':(summary.change>0?'+':'')+format(summary.change)}</strong><small>Based on your manual entries</small></article><article><span>Your goal</span><strong>{log.goal===null?'—':format(log.goal)}</strong><small>{summary.remaining===null?'Optional — set it below':summary.remaining===0?'Your logged score reached the goal':format(summary.remaining)+' to go'}</small></article></div>
   <div className="score-main-grid"><section className="score-panel score-trend"><div className="score-panel-heading"><div><span className="eyebrow">YOUR LOGGED SCORES</span><h3>See how far you’ve come.</h3></div><TrendingUp size={20}/></div><ScoreChart entries={log.entries}/>{log.goal!==null&&summary.latest!==null&&<div className="score-goal"><div><span><Target size={14}/> Logged progress toward your goal</span><strong>{summary.progress}%</strong></div><div className="score-progress" role="progressbar" aria-label="Progress from manually logged scores" aria-valuemin={0} aria-valuemax={100} aria-valuenow={summary.progress}><i style={{width:summary.progress+'%'}}/></div></div>}</section>
    <section className="score-panel score-log"><span className="eyebrow">KEEP IT UP TO DATE</span><h3>Log your score.</h3><p>Find your Snapscore on your Snapchat profile.</p><form onSubmit={submit}><label htmlFor="manual-score">Current Snapscore<input id="manual-score" inputMode="numeric" autoComplete="off" required maxLength={18} value={score} onChange={e=>{setScore(e.target.value);setSaved(false)}} placeholder="e.g. 12,500"/></label><label htmlFor="score-goal">Goal <small>Optional</small><input id="score-goal" inputMode="numeric" autoComplete="off" maxLength={18} value={goal} onChange={e=>{setGoal(e.target.value);setSaved(false)}} placeholder="e.g. 15,000"/></label>{error&&<div className="error-box" role="alert">{error}</div>}<button className="button score-button full" type="submit"><Plus size={16}/>Save score</button>{saved&&<p className="score-saved" role="status"><Check size={14}/>Saved in this browser.</p>}</form><a className="score-open-link" href="https://www.snapchat.com/" target="_blank" rel="noreferrer">Open Snapchat <ArrowUpRight size={14}/></a></section>
   </div>
   <details className="score-panel score-history"><summary><span><Clock3 size={16}/>Your entries <small>{log.entries.length}</small></span><span>View history</span></summary>{log.entries.length?<div className="score-history-list">{[...log.entries].reverse().map((entry,i)=><div key={entry.at+'-'+i}><span>{when(entry.at)}</span><strong>{format(entry.score)}</strong></div>)}</div>:<p>No entries yet. Your first saved score will appear here.</p>}{log.entries.length>0&&<div className="score-reset">{resetting?<><p>Clear the scores saved in this browser?</p><button className="button secondary" onClick={()=>{setStored({...emptyScoreLog,entries:[]});setScore('');setGoal('');setSaved(false);setError('');setResetting(false)}}>Clear scores</button><button className="text-button" onClick={()=>setResetting(false)}>Keep history</button></>:<button className="text-button" onClick={()=>setResetting(true)}>Reset tracker</button>}</div>}</details>
   <section className="score-about"><div><h3>What affects a Snapscore?</h3><p>Snapchat counts activity such as Snaps sent and received and Stories posted, along with other factors. Its exact scoring formula is private, so there’s no guaranteed number of points per action.</p><a href="https://help.snapchat.com/hc/en-us/articles/7012326657044-What-is-a-Snapscore" target="_blank" rel="noreferrer">Read Snapchat’s explanation <ExternalLink size={12}/></a></div><p>Independent manual tracker. No Snapchat login required. Entries stay in this browser and aren’t synced between devices.</p></section>
  </main>
 </WorkspaceShell>;
}
