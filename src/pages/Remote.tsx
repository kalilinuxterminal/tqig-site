import {lazy,Suspense,useEffect,useMemo,useRef,useState,type FormEvent} from 'react';
import {Link,useLocation,useNavigate} from 'react-router-dom';
import {Cable,Link2,MonitorSmartphone,MapPin,Square,Bookmark,ShieldCheck,ArrowUpRight,Footprints,Car,MousePointer2} from 'lucide-react';
import {WorkspaceShell} from './Workspace';
import {accountApi} from '../services/account';
import {api} from '../services/api';
import {useDevice,type DeviceSession} from '../hooks/useDevice';
import {useStored} from '../hooks/useStored';
import {usePlaceSelection} from '../hooks/usePlaceSelection';
import {PlaceQuickActions} from '../components/PlaceQuickActions';
import {ConnectionWizard} from '../components/ConnectionWizard';
import {PhoneAccess} from '../components/PhoneAccess';
import {JourneySimulator} from './JourneySimulator';
import {initialStatus,places,parseCoordinates,type Place,type Route,type Coordinate,type DeviceStatus} from '../services/types';
const WorldMap=lazy(()=>import('../components/WorldMap'));
type Computer={id:string;name:string;online:boolean;last_seen:number;revoked:boolean;status:Partial<DeviceStatus>};
const localComputer=['127.0.0.1','localhost'].includes(location.hostname)&&location.port==='8766';
const sleep=(ms:number)=>new Promise(resolve=>setTimeout(resolve,ms));

function LocalLink({onLinked}:{onLinked:()=>void}){
 const device=useDevice(),[name,setName]=useState('Home computer'),[code,setCode]=useState(''),[confirm,setConfirm]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false),[wizard,setWizard]=useState(false);
 async function link(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{const enrollment=await accountApi('computers/enrollment',{name});setCode(enrollment.code);await api('remote/link',{code:enrollment.code,confirm:true});setCode('');onLinked()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section className="portal-card local-link-card"><div><span className="eyebrow"><Link2 size={13}/> COMPUTER SETUP</span><h3>Set up this computer.</h3><p>Connect your iPhone here, then allow your account to use it from TQIG.</p></div>{device.status.connection!=='connected'?<button className="button secondary" onClick={()=>setWizard(true)}><Cable size={15}/> Connect the iPhone first</button>:<form className="portal-form" onSubmit={e=>void link(e)}><label>Computer name<input required minLength={2} maxLength={60} value={name} onChange={e=>setName(e.target.value)}/></label><label className="checkbox-label"><input type="checkbox" required checked={confirm} onChange={e=>setConfirm(e.target.checked)}/> Allow my TQIG account to control this connected iPhone and share its connection status and selected location with TQIG. Apple pairing files stay on this computer.</label><button className="button primary" disabled={!confirm||busy}>{busy?'Setting up…':'Finish setup'}<ArrowUpRight size={15}/></button></form>}{code&&<p className="fine-print">Setup hasn’t finished. Check the computer connection and try again.</p>}{error&&<div className="error-box" role="alert">{error}</div>}{wizard&&<ConnectionWizard device={device} close={()=>setWizard(false)}/>}</section>;
}

export default function Remote({studio=false}:{studio?:boolean}){
 const page=useLocation(),navigate=useNavigate();
 const targetParams=new URLSearchParams(page.search),target=targetParams.has('lat')&&targetParams.has('lng')?parseCoordinates(targetParams.get('lat')+','+targetParams.get('lng')):null;
 const [computers,setComputers]=useState<Computer[]>([]),[selected,setSelected]=useState(''),[tab,setTab]=useState<'location'|'driving'|'walking'>(studio&&page.pathname.endsWith('/walk')?'walking':studio&&page.pathname.endsWith('/drive')?'driving':'location'),[route,setRoute]=useState<Route|null>(null),[vehicle,setVehicle]=useState<Coordinate|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[accepted,setAccepted]=useState<Partial<DeviceStatus>|null>(null),[showLocal,setShowLocal]=useState(false),[loading,setLoading]=useState(true);
 const {place,choose:setPlace,undo,canUndo}=usePlaceSelection(target?{...target,name:targetParams.get('name')||target.name}:places[0]);
 const working=useRef(false),operation=useRef(0),alive=useRef(true),refreshing=useRef(false);
 const [savedRoutes,setSavedRoutes]=useStored<Route[]>('routes',[]);
 const [savedPlaces,setSavedPlaces]=useStored<Place[]>('favorites',[]),[recentPlaces,setRecentPlaces]=useStored<Place[]>('recents',[]),[units]=useStored<string>('units','metric');
 const placeSaved=savedPlaces.some(p=>p.lat===place.lat&&p.lng===place.lng);
 const loadedTrip=savedRoutes.find(route=>route.id===new URLSearchParams(page.search).get('route'))||null;
 useEffect(()=>{if(studio)setTab(page.pathname.endsWith('/walk')?'walking':page.pathname.endsWith('/drive')?'driving':'location')},[studio,page.pathname]);
 async function refresh(){if(refreshing.current)return;refreshing.current=true;try{const r=await accountApi('computers');if(alive.current)setComputers(r.computers)}catch(e){if(alive.current)setError((e as Error).message)}finally{refreshing.current=false;if(alive.current)setLoading(false)}}
 useEffect(()=>{alive.current=true;void refresh();const timer=setInterval(()=>void refresh(),3000);return()=>{alive.current=false;clearInterval(timer)}},[]);
 const computer=computers.find(c=>c.id===selected)||computers.find(c=>!c.revoked)||null;
 useEffect(()=>{setAccepted(null);setRoute(null);setVehicle(null)},[computer?.id]);
 const status=useMemo<DeviceStatus>(()=>{const s=accepted||computer?.status||{},phone=s.device;return{...initialStatus,...s,serverTime:Date.now()/1000,device:phone?{id:computer!.id,name:phone.name,ios:phone.ios,build:'',transport:phone.transport}:null,journey:{...initialStatus.journey,...s.journey}}},[computer,accepted]);
 const journeyActive=['playing','starting','paused'].includes(status.journey.state);
 const simulationLabel=status.state==='applying'?'Updating target':status.simulation==='command_accepted'?'Simulation active':status.simulation==='clear_sent'?'Reset requested':'Location not confirmed';
 async function act(path:string,body:unknown={}):Promise<DeviceStatus>{
  if(!computer||!computer.online||computer.revoked)throw Error('Your computer is offline. Open TQIG on that computer and try again.');if(working.current&&!['stop','journey/stop','disconnect'].includes(path))throw Error('Please wait for the current change to finish.');const current=++operation.current;working.current=true;setBusy(true);setError('');setMessage('Sending to your iPhone…');
  try{const queued=await accountApi('computers/'+computer.id+'/commands',{action:path,payload:body}),deadline=Date.now()+125000;while(Date.now()<deadline){if(current!==operation.current)throw Error('Command monitoring interrupted by Stop.');await sleep(1000);const result=await accountApi('commands/'+queued.id);if(result.state==='acknowledged'){if(alive.current&&current===operation.current){setAccepted(result.result);if(path==='location'){const applied={...place,...body as Coordinate};setRecentPlaces([applied,...recentPlaces.filter(p=>p.lat!==applied.lat||p.lng!==applied.lng)].slice(0,20))}setMessage('The iPhone accepted the request. Check its location in Apple Maps.')}await refresh();return{...initialStatus,...result.result,journey:{...initialStatus.journey,...result.result.journey}}}if(['failed','expired','cancelled'].includes(result.state))throw Error(result.error||'Command did not complete. Device outcome is unknown; check the home helper.')}throw Error('The iPhone did not confirm the request. Check the connection before trying again.')}catch(e){if(alive.current&&current===operation.current){setMessage('');setError((e as Error).message)}throw e}finally{if(current===operation.current){working.current=false;if(alive.current)setBusy(false)}}
 }
 // Status polling supersedes a one-off command response as soon as fresh telemetry arrives.
 useEffect(()=>{setAccepted(null)},[computer?.last_seen]);
 const remoteDevice:DeviceSession={status,online:!!computer?.online,busy,error,setError,canAlwaysStop:true,authorize:async()=>{await refresh()},act};
 
 return <WorkspaceShell title={studio?'Location studio':'Home iPhone controls'} subtitle={studio?'Choose a place. Make it your own.':'Use this dashboard to control the iPhone plugged in at home.'}>
  <main className="portal-main remote-main simple-remote">
   <section className="simple-connection-strip" aria-label="iPhone connection">
    <span className="simple-phone-symbol"><MonitorSmartphone size={24}/></span>
    <div className="simple-connection-name"><strong>Home iPhone</strong><span>{computer?.name||'No computer linked'}{computer&&(computer.online?' · Computer online':' · Computer offline')}</span></div>
    <span className={'simple-connection-state '+(computer?.online&&status.connection==='connected'?'ready':'')}>{computer?.online&&status.connection==='connected'?'Ready':'Not connected'}</span>
    {computer&&status.connection!=='connected'&&<button className="button secondary" disabled={!computer.online||busy} onClick={()=>void act('connect').catch(()=>{})}>{busy?'Connecting…':'Reconnect iPhone'}</button>}
   </section>
   {!studio&&localComputer&&computer&&!computer.revoked&&<PhoneAccess/>}
   {computers.filter(c=>!c.revoked).length>1&&<label className="simple-computer-choice">Computer<select id="remote-computer" value={computer?.id||''} disabled={busy} onChange={e=>setSelected(e.target.value)}>{computers.filter(c=>!c.revoked).map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>}
   {loading?<p className="simple-control-note" role="status">Checking your connection…</p>:!computer||computer.revoked?<section className="portal-card simple-empty"><Cable size={30}/><h2>Connect the home iPhone first.</h2><p>Open TQIG on your Windows computer. Plug in the iPhone you plan to leave at home, unlock it and follow the connection steps.</p>{localComputer?<button className="button primary" onClick={()=>setShowLocal(!showLocal)}>{showLocal?'Close setup':'Connect an iPhone'}</button>:<p>On the computer, open <strong>Start-TQIG</strong> and sign in with this same account.</p>}{showLocal&&<LocalLink onLinked={()=>{setShowLocal(false);void refresh()}}/>}<Link to="/dashboard" className="simple-back">Back to workspace</Link></section>:<>
    <nav className="remote-tabs" aria-label="Location options">{[{key:'location',label:'Place',icon:MapPin},{key:'walking',label:'Walk',icon:Footprints},{key:'driving',label:'Drive',icon:Car}].map(t=><button key={t.key} aria-pressed={tab===t.key} className={tab===t.key?'active':''} disabled={busy} onClick={()=>studio?navigate(t.key==='walking'?'/app/walk':t.key==='driving'?'/app/drive':'/app'):setTab(t.key as typeof tab)}><t.icon size={16}/>{t.label}</button>)}</nav>
    {tab==='location'?<div className="remote-location-grid">
     <div className="remote-location-map"><Suspense fallback={<div className="map-loading">Opening map…</div>}><WorldMap selected={place} onSelect={setPlace} savedPlaces={savedPlaces} showSelectionCard={false}/></Suspense></div>
     <section className="portal-card remote-location-controls"><span className="selection-panel-kicker"><MapPin size={14}/> YOUR SELECTED PLACE</span><div className="simple-place-title"><h2>{place.name}</h2><button className="icon-button" title={placeSaved?'Remove saved place':'Save place'} aria-label={placeSaved?'Remove saved place':'Save place'} onClick={()=>setSavedPlaces(placeSaved?savedPlaces.filter(p=>p.lat!==place.lat||p.lng!==place.lng):[place,...savedPlaces].slice(0,50))}><Bookmark size={19} fill={placeSaved?'currentColor':'none'}/></button></div><p className="selected-place-region">{place.region}<code>{place.lat.toFixed(5)}, {place.lng.toFixed(5)}</code></p><PlaceQuickActions place={place} onUndo={undo} canUndo={canUndo}/>{savedPlaces.length>0&&<div className="saved-place-shortcuts"><span>SAVED PLACES</span><div>{savedPlaces.slice(0,4).map(p=><button key={`${p.lat},${p.lng}`} aria-label={`Choose saved place ${p.name}`} onClick={()=>setPlace(p)}>{p.name}</button>)}</div></div>}<p className="selection-tip"><MousePointer2 size={16}/><span>Search the map, tap a place, or drag the pin to fine-tune your choice.</span></p>
      <div className="simple-active-location"><small>IPHONE STATUS</small><span>{simulationLabel}</span>{status.lastAcceptedCoordinates&&status.simulation==='command_accepted'&&<code>{status.lastAcceptedCoordinates.lat.toFixed(4)}, {status.lastAcceptedCoordinates.lng.toFixed(4)}</code>}</div>
      <button className="button primary full" disabled={!computer.online||busy||status.connection!=='connected'||journeyActive} onClick={()=>void act('location',{lat:place.lat,lng:place.lng}).catch(()=>{})}><MapPin size={16}/>{busy?'Applying location…':journeyActive?'Trip in progress':'Set Location'}</button>
      <button className="button secondary full" disabled={!computer.online} onClick={()=>void act('stop').catch(()=>{})}><Square size={15}/>Stop & Restore</button>
      <p className="simple-control-note">{journeyActive?'A trip is running. Stop & Restore ends it before you choose a new place.':'Check the result in Apple Maps. Keep your iPhone connected while using computer mode.'}</p>
     </section>
    </div>:<div className="map-workspace is-drive remote-trip-workspace"><Suspense fallback={<div className="map-loading">Opening map…</div>}><WorldMap selected={place} route={route} vehicle={vehicle}/></Suspense><JourneySimulator key={tab} defaultMode="device" travelMode={tab} device={remoteDevice} onRoute={setRoute} onVehicle={setVehicle} onConnect={()=>void act('connect').catch(()=>{})} onSave={r=>{setSavedRoutes([r,...savedRoutes.filter(x=>x.id!==r.id||x.name!==r.name)].slice(0,20));setMessage('Trip saved.')}} units={units} loadedRoute={loadedTrip}/></div>}
   </>}
   {message&&<div className="remote-message" role="status">{message}</div>}{error&&<div className="error-box" role="alert">{error}</div>}
   <details className="simple-details computer-options"><summary>Connection options</summary>
    <p>TQIG applies your changes to the home iPhone. Maps and other apps running on your main phone use that phone’s own GPS.</p>
    <p>For Find My People sharing, you can choose the home iPhone as the source in <strong>Find My → Me → Use This iPhone as My Location</strong>. Each iPhone still has a separate entry under Devices. <a href="https://support.apple.com/guide/iphone/iph01954dc44/ios" target="_blank" rel="noreferrer">Apple’s instructions</a></p>
    {localComputer&&computer&&<><button className="button secondary" onClick={()=>setShowLocal(!showLocal)}>{showLocal?'Close setup':'Set up this computer'}</button>{showLocal&&<LocalLink onLinked={()=>{setShowLocal(false);void refresh()}}/>}{studio&&<Link className="button secondary" to="/remote">Open controls on your main phone</Link>}</>}
    {computer&&!computer.revoked&&<button className="text-button" disabled={busy} onClick={()=>void accountApi('computers/'+computer.id+'/revoke',{}).then(refresh).catch(e=>setError(e.message))}>Remove this computer from my account</button>}
   </details>
  </main>
 </WorkspaceShell>;
}
