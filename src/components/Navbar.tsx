import {ArrowUpRight,Menu,X} from 'lucide-react';
import {Link,useLocation} from 'react-router-dom';
import {useEffect,useId,useRef,useState} from 'react';
import {Logo} from './Logo';
import {useAuth} from '../hooks/useAuth';
export function Navbar(){
 const {session}=useAuth(),{pathname}=useLocation(),[open,setOpen]=useState(false),id=useId();
 const header=useRef<HTMLElement>(null),toggle=useRef<HTMLButtonElement>(null);
 useEffect(()=>setOpen(false),[pathname]);
 useEffect(()=>{if(!open)return;const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'){setOpen(false);toggle.current?.focus();}};const outside=(event:PointerEvent)=>{if(!header.current?.contains(event.target as Node))setOpen(false);};document.addEventListener('keydown',escape);document.addEventListener('pointerdown',outside);return()=>{document.removeEventListener('keydown',escape);document.removeEventListener('pointerdown',outside);};},[open]);
 return <>{pathname==='/'&&<a className="skip-link" href="#main-content">Skip to content</a>}<header ref={header} className="site-nav" onClick={e=>{if((e.target as HTMLElement).closest('a'))setOpen(false);}}><div className="nav-inner"><Logo/>
  <nav id={id} aria-label="Main navigation" className={open?'site-links open':'site-links'}><a href="/#features">Explore</a><a href="/#how-it-works">How it works</a><a href="/#compatibility">Compatibility</a><Link to="/preview">Preview</Link><Link to="/support">Support</Link></nav>
  <Link className="button nav-cta" to={session.user?'/dashboard':'/signin'}>{session.user?'Workspace':'Sign in'} <ArrowUpRight size={15}/></Link>
  <button ref={toggle} type="button" className="icon-button mobile-menu" aria-label={open?'Close menu':'Open menu'} aria-expanded={open} aria-controls={id} onClick={()=>setOpen(!open)}>{open?<X size={21}/>:<Menu size={21}/>}</button>
 </div></header></>;
}
