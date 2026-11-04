import {BrowserRouter,Routes,Route,useLocation,Link} from 'react-router-dom';
import {MotionConfig} from 'motion/react';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Policy from './pages/Policy';
import {AuthProvider,Protected} from './hooks/useAuth';
import Account from './pages/Account';
import Workspace,{WorkspaceShell} from './pages/Workspace';
import {localHelperPage} from './services/environment';
import Admin from './pages/Admin';
import Remote from './pages/Remote';
import Phone from './pages/Phone';
import Preview from './pages/Preview';
import Security from './pages/Security';
import SettingsHub from './pages/SettingsHub';
import Snapscore from './pages/Snapscore';
function StudioEntry(){const {pathname}=useLocation();if(pathname.endsWith('/locations')||pathname.endsWith('/settings')||localHelperPage&&pathname.endsWith('/devices'))return <Dashboard/>;if(pathname.endsWith('/devices'))return <WorkspaceShell title="Home connection" subtitle="Connections are managed on the home computer."><main className="portal-main"><section className="portal-card"><h3>Connect the target iPhone at home.</h3><p>Open the local TQIG dashboard on that PC, verify its iPhone connection and link the computer to your account. This phone browser controls the linked device through your dashboard.</p><Link className="button primary" style={{marginTop:20}} to="/dashboard">Open home dashboard</Link></section></main></WorkspaceShell>;return <Remote studio/>}
export default function App(){return <MotionConfig reducedMotion="user"><BrowserRouter><AuthProvider><Routes><Route path="/" element={<Landing/>}/><Route path="/preview" element={<Preview/>}/>{['/signin','/signup','/owner/setup'].map(path=><Route key={path} path={path} element={<Account key={path}/>}/>)}<Route path="/dashboard" element={<Protected><Workspace/></Protected>}/><Route path="/overview" element={<Protected><Workspace/></Protected>}/><Route path="/settings" element={<Protected><SettingsHub/></Protected>}/><Route path="/snapscore" element={<Protected><Snapscore/></Protected>}/><Route path="/remote" element={<Protected><Remote/></Protected>}/><Route path="/phone" element={<Protected><Phone/></Protected>}/><Route path="/account" element={<Protected><Security/></Protected>}/><Route path="/admin" element={<Protected owner><Admin/></Protected>}/><Route path="/app/*" element={<Protected><StudioEntry/></Protected>}/><Route path="/privacy" element={<Policy/>}/><Route path="/terms" element={<Policy/>}/><Route path="/support" element={<Policy/>}/><Route path="*" element={<Policy/>}/></Routes></AuthProvider></BrowserRouter></MotionConfig>}
