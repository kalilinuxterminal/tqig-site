import {Link} from 'react-router-dom';
import {Cable,ShieldCheck,SlidersHorizontal,Smartphone,LockKeyhole,ArrowUpRight,Info,TrendingUp} from 'lucide-react';
import {WorkspaceShell} from './Workspace';
import {useAuth} from '../hooks/useAuth';

export default function SettingsHub(){
 const {session}=useAuth();
 const items=[{to:'/snapscore',icon:TrendingUp,title:'Snapscore tracker',text:'Log your score manually and follow your progress.'},{to:'/app/devices',icon:Cable,title:'Computer connection',text:'Set up or reconnect the iPhone attached to your computer.'},{to:'/account',icon:ShieldCheck,title:'Account & security',text:'Change your password and review browser access.'},{to:'/app/settings',icon:SlidersHorizontal,title:'Preferences',text:'Map units and workspace preferences.'},{to:'/phone',icon:Smartphone,title:'On this iPhone',text:'Phone-only mode is not ready yet. See its availability.'},{to:'/overview',icon:Info,title:'Getting started',text:'Choose which iPhone you want to change.'}];
 if(session.user?.role==='owner')items.push({to:'/admin',icon:LockKeyhole,title:'Owner console',text:'Manage invitations and registered accounts.'});
 return <WorkspaceShell title="Settings" subtitle="Everything else, in one place."><main className="portal-main"><div className="settings-hub-grid">{items.map(item=><Link className="portal-card settings-hub-card" to={item.to} key={item.to}><item.icon/><div><h2>{item.title}</h2><p>{item.text}</p></div><ArrowUpRight size={17}/></Link>)}</div></main></WorkspaceShell>;
}
