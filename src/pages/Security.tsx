import {useCallback,useEffect,useState,type FormEvent} from 'react';
import {Link} from 'react-router-dom';
import {Check,KeyRound,LoaderCircle,LogOut,Monitor,ShieldCheck} from 'lucide-react';
import {WorkspaceShell} from './Workspace';
import {accountApi,type Session} from '../services/account';
import {useAuth} from '../hooks/useAuth';

type BrowserSession={id:string;created:number;last_seen:number;expires:number;remember:boolean;current:boolean};
const date=(value:number)=>new Date(value*1000).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});

export default function Security(){
 const auth=useAuth();
 const [sessions,setSessions]=useState<BrowserSession[]>([]),[loading,setLoading]=useState(true);
 const [busy,setBusy]=useState(''),[error,setError]=useState(''),[message,setMessage]=useState('');
 const [current,setCurrent]=useState(''),[password,setPassword]=useState(''),[confirmation,setConfirmation]=useState('');
 const refresh=useCallback(async()=>{
  try{const data=await accountApi<{sessions:BrowserSession[]}>('account/security');setSessions(data.sessions)}
  catch(e){setError((e as Error).message)}finally{setLoading(false)}
 },[]);
 useEffect(()=>{void refresh()},[refresh]);

 async function revoke(id:string){
  setBusy(id);setError('');setMessage('');
  try{const result=await accountApi('account/sessions/'+id+'/revoke',{});setMessage(id==='others'?`${result.revoked} other browser session${result.revoked===1?'':'s'} signed out.`:'That browser has been signed out.');await refresh()}
  catch(e){setError((e as Error).message)}finally{setBusy('')}
 }
 async function changePassword(event:FormEvent){
  event.preventDefault();setError('');setMessage('');
  if(password!==confirmation){setError('The new passwords do not match.');return}
  setBusy('password');
  try{
   const next=await accountApi<Session>('account/password',{currentPassword:current,newPassword:password});
   auth.accept(next);setCurrent('');setPassword('');setConfirmation('');
   setMessage('Password updated. Other browsers are signed out; this browser has a fresh session.');await refresh();
  }catch(e){setError((e as Error).message)}finally{setBusy('')}
 }
 const others=sessions.filter(session=>!session.current);
 return <WorkspaceShell title="Account & security" subtitle="Keep access to your workspace in your hands.">
  <main className="portal-main security-main">
   <section className="security-identity portal-card">
    <span className="security-avatar"><ShieldCheck size={23}/></span>
    <div><span className="eyebrow">YOUR ACCOUNT</span><h2>{auth.session.user?.name}</h2><p>{auth.session.user?.email}</p></div>
    <span className="small-tag">{auth.session.user?.role==='owner'?'Owner access':'Member access'}</span>
   </section>
   {message&&<div className="remote-message security-feedback" role="status"><Check size={16}/>{message}</div>}
   {error&&<div className="error-box" role="alert">{error}</div>}
   <div className="security-grid">
    <section className="portal-card security-password">
     <span className="eyebrow"><KeyRound size={14}/> PASSWORD</span>
     <h2>A fresh start for your sign-in.</h2>
     <p>Changing your password signs out every other browser. This browser stays signed in with a new session.</p>
     <form className="portal-form" onSubmit={event=>void changePassword(event)}>
      <label htmlFor="current-password">Current password<input id="current-password" type="password" autoComplete="current-password" required maxLength={128} value={current} onChange={e=>setCurrent(e.target.value)}/></label>
      <label htmlFor="new-password">New password<input id="new-password" type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)}/><small>Use at least 12 characters. A long, unique passphrase works well.</small></label>
      <label htmlFor="confirm-password">Confirm new password<input id="confirm-password" type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={confirmation} onChange={e=>setConfirmation(e.target.value)}/></label>
      <button className="button primary" disabled={!!busy}>{busy==='password'?<LoaderCircle size={15} className="spin"/>:<KeyRound size={15}/>}Update password</button>
     </form>
     <p className="security-note">Linked home computers keep their separate authorization. Unlink one from <Link to="/remote">Remote Dashboard</Link> to remove its access.</p>
    </section>
    <section className="portal-card security-sessions">
     <div className="portal-section-heading"><h2>Browser sessions</h2><Monitor size={19}/></div>
     <p>Review when browsers signed in and remove access you no longer need. TQIG does not collect an IP address or precise location for this list.</p>
     {loading?<div className="security-loading"><LoaderCircle size={18} className="spin"/>Loading sessions…</div>:<>
      <div className="session-list">{sessions.map(session=><article className="session-row" key={session.id}>
       <Monitor size={20}/><div><strong>{session.current?'This browser':'Another browser'}{session.current&&<span className="small-tag success">CURRENT</span>}</strong>
        <small>Signed in {date(session.created)}</small><small>Last active {date(session.last_seen)}</small>
        <small>{session.remember?'Remembered for up to 30 days':'Standard session'} · expires {date(session.expires)}</small>
       </div>{!session.current&&<button className="text-button" disabled={!!busy} onClick={()=>void revoke(session.id)}>Sign out</button>}
      </article>)}</div>
      <button className="button secondary" disabled={!!busy||!others.length} onClick={()=>void revoke('others')}><LogOut size={15}/>Sign out other browsers</button>
      {!others.length&&<small className="security-note">This is your only active browser session.</small>}
     </>}
    </section>
   </div>
   <p className="portal-footnote"><ShieldCheck size={14}/> Keep your password somewhere safe. Email-based account recovery is not configured in this preview.</p>
  </main>
 </WorkspaceShell>;
}
