import {type ReactNode} from 'react';
import {motion,useReducedMotion} from 'motion/react';
import {Link} from 'react-router-dom';
import {ArrowUpRight,MapPin,Smartphone,ArrowRight,TrendingUp,Footprints,Car,Bookmark,ArrowDownRight} from 'lucide-react';
import {Sidebar} from '../components/Sidebar';
import {MobileWorkspaceNav} from '../components/WorkspaceNavigation';
import {useAuth} from '../hooks/useAuth';
import {useStored} from '../hooks/useStored';
import type {Place} from '../services/types';
import {LogoMark} from '../components/Logo';

export function WorkspaceShell({title,subtitle,children}:{title:string;subtitle:string;children:ReactNode}){
 const {session,signOut}=useAuth();
 return <div className="dashboard-shell"><Sidebar/><div className="app-content">
  <header className="portal-header"><div><span className="eyebrow"><LogoMark size={13}/> TQIG / WORKSPACE</span><h1>{title}</h1><p>{subtitle}</p></div>
   <div className="account-profile"><Link className="workspace-account-avatar" to="/account" aria-label="Open account settings">{session.user?.name.slice(0,1).toUpperCase()}</Link><span>{session.user?.name}<small>{session.user?.role==='owner'?'Owner':'Member'}</small></span><button className="button subtle" onClick={()=>void signOut().catch(()=>{})}>Sign out</button></div>
  </header><MobileWorkspaceNav/><div className="workspace-surface">{children}</div>
 </div></div>;
}

export default function Workspace(){
 const [favorites]=useStored<Place[]>('favorites',[]),reduced=useReducedMotion();
 return <WorkspaceShell title="Your workspace" subtitle="A new point of view starts here.">
  <main className="portal-main refined-home midnight-home">
   <section className="home-welcome"><div><span className="home-kicker"><i/> A WORLD OF YOUR OWN</span><h2>Change your<br/><span>perspective.</span></h2><p>Pick a place. Take the long way.<br/> Create your next move with a connected iPhone.</p><div className="home-welcome-actions"><Link className="button primary" to="/app">Enter the map <ArrowUpRight size={17}/></Link><Link className="home-help-link" to="/remote">Home iPhone controls <ArrowRight size={14}/></Link></div><small>Windows computer required. Keep your iPhone connected.</small></div>
    <div className="midnight-map-art" aria-hidden="true"><div className="midnight-art-grid"/><svg className="midnight-route-art" viewBox="0 0 450 360" fill="none"><path className="midnight-contour" d="M-20 70C90 20 95 160 195 120S350 10 480 100M-20 98C90 48 95 188 195 148S350 38 480 128M-20 126C90 76 95 216 195 176S350 66 480 156M-20 154C90 104 95 244 195 204S350 94 480 184M-20 182C90 132 95 272 195 232S350 122 480 212M-20 210C90 160 95 300 195 260S350 150 480 240" stroke="white" strokeOpacity=".09"/><path d="M68 293V225H160L239 146H365" stroke="white" strokeOpacity=".14" strokeWidth="2"/><path className="midnight-route-flow" d="M68 293V225H160L239 146H365" stroke="#8964af" strokeWidth="3" strokeLinecap="round"/><circle cx="68" cy="293" r="5" fill="#0d0d10" stroke="white" strokeOpacity=".6" strokeWidth="2"/><circle className="midnight-destination-halo" cx="365" cy="146" r="28" fill="#7956a0" fillOpacity=".12"/><circle cx="365" cy="146" r="6" fill="white"/></svg><div className="midnight-art-emblem"><LogoMark size={54}/></div><span className="midnight-art-caption">A DIFFERENT POINT OF VIEW <ArrowDownRight size={14}/></span></div>
   </section>
   <div className="home-section-title"><div><span className="eyebrow">YOUR NEXT MOVE</span><h3>Choose your direction.</h3></div><span>Three ways to make it yours</span></div>
   <div className="home-experience-grid">{[{to:'/app',icon:MapPin,title:'A place.',text:'Anywhere you have in mind.',label:'Explore the map',kind:'place'},{to:'/app/walk',icon:Footprints,title:'A walk.',text:'Your pace. Your time. Your way back.',label:'Plan a walk',kind:'walk'},{to:'/app/drive',icon:Car,title:'A drive.',text:'Real roads. A different perspective.',label:'Plan a drive',kind:'drive'}].map((item,i)=><motion.div className="home-experience-slot" key={item.to} initial={reduced?false:{opacity:0,y:16}} whileInView={{opacity:1,y:0}} viewport={{once:true,amount:.2}} transition={{duration:.5,delay:reduced?0:i*.08}}><Link className={'home-experience '+item.kind} to={item.to}><span className="experience-icon"><item.icon size={23}/></span><span className="experience-number">0{i+1}</span><ArrowUpRight className="experience-arrow" size={18}/><h3>{item.title}</h3><p>{item.text}</p><span className="experience-link">{item.label} <ArrowRight size={14}/></span></Link></motion.div>)}</div>
   <section className="home-saved-row"><div><Bookmark size={21}/><div><h3>Your favorite places</h3><p>{favorites.length?'Pick up where you left off.':'Save a place on the map to find it here.'}</p></div></div><div className="home-place-chips">{favorites.slice(0,3).map(p=><Link key={`${p.lat},${p.lng}`} to={`/app?lat=${p.lat}&lng=${p.lng}&name=${encodeURIComponent(p.name)}`}><MapPin size={13}/>{p.name}</Link>)}</div><Link className="home-help-link" to="/app/locations">View saved <ArrowRight size={14}/></Link></section>
   <div className="home-secondary-grid"><Link to="/snapscore"><TrendingUp size={21}/><div><strong>Snapscore tracker</strong><p>Your manually logged scores, in one place.</p></div><ArrowUpRight size={16}/></Link><Link to="/phone"><Smartphone size={21}/><div><strong>Looking for phone-only?</strong><p>View availability and current limits.</p></div><ArrowUpRight size={16}/></Link></div>
   <p className="home-footnote">New to TQIG? <Link to="/preview">Watch the preview <ArrowUpRight size={12}/></Link></p>
  </main>
 </WorkspaceShell>;
}
