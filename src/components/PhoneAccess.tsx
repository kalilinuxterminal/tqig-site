import {useCallback,useEffect,useState} from 'react';
import {QRCodeSVG} from 'qrcode.react';
import {Link} from 'react-router-dom';
import {Check,Copy,ExternalLink,LoaderCircle,Smartphone,Square} from 'lucide-react';
import {api,localSession} from '../services/api';

type Access={state:'off'|'starting'|'ready';url:string|null;temporary:boolean;error:string|null;componentInstalled:boolean};
export function PhoneAccess(){
 const [access,setAccess]=useState<Access|null>(null),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[copied,setCopied]=useState(false);
 const refresh=useCallback(async()=>{
  try{
   await localSession();
   setAccess(await api<Access>('phone-access'));
  }catch{
   setAccess(null);
  }
 },[]);
 useEffect(()=>{void refresh();const timer=setInterval(()=>void refresh(),5000);return()=>clearInterval(timer)},[refresh]);
 async function change(start:boolean){setBusy(true);setError('');try{setAccess(await api<Access>('phone-access/'+(start?'start':'stop'),start?{confirm:true}:{}))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 const url=access?.url?access.url+'/remote':null;
 return <section className="portal-card phone-access-card">
  <div className="phone-access-heading">
   <Smartphone size={24}/>
   <div>
    <span className="eyebrow">TAKE THE CONTROLS WITH YOU</span>
    <h2>Open on your main phone</h2>
    <p>Keep the home iPhone plugged in and this PC awake with TQIG running.</p>
   </div>
   <span className={'small-tag '+(url?'success':'')}>{url?'PHONE ACCESS ON':'LOCAL ACCESS ONLY'}</span>
  </div>
  {url?
   <div className="phone-access-live">
    <div className="phone-access-qr"><QRCodeSVG value={url} size={146} level="M" marginSize={2}/></div>
    <div>
     <strong>Scan with the camera on your main phone.</strong>
     <p>Sign in with your TQIG account. The link takes you straight to your home iPhone controls.</p>
     <a href={url} className="phone-access-url" target="_blank" rel="noreferrer">{url}<ExternalLink size={12}/></a>
     <div className="phone-access-actions">
      <button className="button secondary" onClick={()=>void navigator.clipboard.writeText(url).then(()=>{setCopied(true);setTimeout(()=>setCopied(false),2500)}).catch(()=>setError('Copy was unavailable. Select the address above.'))}>{copied?<Check size={14}/>:<Copy size={14}/>} {copied?'Copied':'Copy phone link'}</button>
      <button className="text-button" disabled={busy} onClick={()=>void change(false)}><Square size={13}/>Turn off phone access</button>
     </div>
     <small>The link changes when phone access restarts.</small>
    </div>
   </div>:
   <div className="phone-access-start">
    <label className="checkbox-label"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>Allow a temporary link through Cloudflare. Your TQIG sign-in protects the controls, and Apple pairing files stay on this PC.</label>
    <button className="button primary" disabled={!consent||busy||!access?.componentInstalled} onClick={()=>void change(true)}>{busy?<LoaderCircle size={15} className="spin"/>:<Smartphone size={15}/>} {busy?'Checking secure phone link…':'Enable phone access'}</button>
    {access&&!access.componentInstalled&&<p className="fine-print">Run Setup-Phone-Access.cmd on the home computer to prepare phone access.</p>}
    <p className="fine-print">Remote sign-in requires a unique password of at least 12 characters. <Link to="/account">Update your password</Link></p>
   </div>
  }
  {(error||access?.error)&&<div className="error-box" role="alert">{error||access?.error}</div>}
 </section>;
}
