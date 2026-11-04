import {Link} from 'react-router-dom';
import {ArrowUpRight,ShieldCheck,LockKeyhole,Settings} from 'lucide-react';
import {Logo} from './Logo';
import {useAuth} from '../hooks/useAuth';
import {WorkspaceLinks} from './WorkspaceNavigation';

export function Sidebar(){
 const {session}=useAuth();
 return <aside className="app-sidebar"><Logo/><div className="sidebar-caption">YOUR WORKSPACE</div>
  <nav><WorkspaceLinks/></nav>
  <div className="sidebar-bottom compact-sidebar-bottom">
   
   <Link to="/account" className="sidebar-profile"><span className="profile-initial">{session.user?.name.slice(0,1).toUpperCase()}</span><span>{session.user?.name}<small>My account</small></span><Settings size={14}/></Link>
   <a href="/support" target="_blank" rel="noreferrer">Help <ArrowUpRight size={14}/></a><span>TQIG PREVIEW <i>0.9</i></span>
  </div>
 </aside>;
}
