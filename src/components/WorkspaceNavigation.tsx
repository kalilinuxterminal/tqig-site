import {Link,useLocation} from 'react-router-dom';
import {LayoutDashboard,MapPin,Bookmark,Settings,Car,Footprints} from 'lucide-react';

export function WorkspaceLinks({mobile=false}:{mobile?:boolean}){
 const {pathname}=useLocation();
 const group=['/dashboard','/overview','/phone','/snapscore'].includes(pathname)?'dashboard':pathname==='/app/locations'?'saved':['/app','/app/drive','/app/walk','/remote'].includes(pathname)?'studio':'settings';
 const links=[{key:'dashboard',to:'/dashboard',label:'Home',icon:LayoutDashboard},{key:'studio',to:'/app',label:'Location',icon:MapPin},{key:'saved',to:'/app/locations',label:mobile?'Saved':'Saved Places',icon:Bookmark},{key:'settings',to:'/settings',label:'Settings',icon:Settings}];
 return <>{links.map(item=><Link key={item.key} to={item.to} aria-current={group===item.key?'page':undefined} className={(mobile?'mobile-workspace-link':'app-nav')+(group===item.key?' active':'')}><item.icon size={mobile?17:18}/><span>{item.label}</span></Link>)}</>;
}
export function MobileWorkspaceNav(){return <nav className="workspace-mobile-nav" aria-label="Workspace"><WorkspaceLinks mobile/></nav>}
export function StudioTabs(){
 const {pathname}=useLocation();
 return <nav className="studio-tabs" aria-label="Location tools">{[{to:'/app',name:'Map',icon:MapPin},{to:'/app/walk',name:'Walking',icon:Footprints},{to:'/app/drive',name:'Driving',icon:Car}].map(item=><Link to={item.to} key={item.to} className={pathname===item.to?'active':''} aria-current={pathname===item.to?'page':undefined}><item.icon size={15}/>{item.name}</Link>)}</nav>;
}
