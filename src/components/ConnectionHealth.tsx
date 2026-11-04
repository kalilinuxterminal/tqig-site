import {useState} from 'react';
import {CheckCircle2,Info,LoaderCircle,RefreshCw,TriangleAlert} from 'lucide-react';
import {api,bridgeUrl} from '../services/api';

type Report={checks:{key:string;title:string;state:'pass'|'action'|'info';description:string}[];runtime:{python:string;system:string;helper:string};locationWrites:number};
export function ConnectionHealth({online}:{online:boolean}){
 const [report,setReport]=useState<Report|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function check(){setBusy(true);setError('');try{setReport(await api<Report>('diagnostics'))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section className="connection-health glass">
  <div className="health-heading"><div><span className="eyebrow">A CLEARER CONNECTION</span><h2>Ready to connect?</h2><p>Check the local helper and cable before starting a phone session. This check never changes a location.</p></div><button className="button secondary" disabled={!online||busy} onClick={()=>void check()}>{busy?<LoaderCircle size={15} className="spin"/>:<RefreshCw size={15}/>} {busy?'Checking…':report?'Check again':'Check connection'}</button></div>
  {!online&&<p className="notice">Start the Windows helper and authorize this browser first. <a href={`${bridgeUrl}/authorize`} target="_blank" rel="noreferrer">Open local helper ↗</a></p>}
  {report&&<><div className="health-checks">{report.checks.map(check=><article className={'health-check '+check.state} key={check.key}>{check.state==='pass'?<CheckCircle2 size={18}/>:check.state==='action'?<TriangleAlert size={18}/>:<Info size={18}/>}<div><h3>{check.title}</h3><p>{check.description}</p></div></article>)}</div><details className="health-details"><summary>Connection details</summary><p>TQIG {report.runtime.helper} · {report.runtime.system} · Python {report.runtime.python}</p><p>These are readiness checks. Connect and verify the intended iPhone before using Set Location.</p></details></>}
  {error&&<div className="error-box" role="alert">{error}</div>}
 </section>;
}
