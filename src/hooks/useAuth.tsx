import {createContext,useCallback,useContext,useEffect,useState,type ReactNode} from 'react';
import {Navigate,useLocation} from 'react-router-dom';
import {accountApi,rememberSession,type Session} from '../services/account';
type Auth={session:Session;loading:boolean;error:string;refresh:()=>Promise<void>;accept:(s:Session)=>void;signOut:()=>Promise<void>};
const Context=createContext<Auth|null>(null);
export function AuthProvider({children}:{children:ReactNode}){
 const [session,setSession]=useState<Session>({user:null}),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const accept=useCallback((next:Session)=>{rememberSession(next);setSession(next);setError('')},[]);
 const refresh=useCallback(async()=>{try{accept(await accountApi<Session>('auth/session'))}catch{accept({user:null});setError('The account service is offline. Start TQIG or check the server connection.')}finally{setLoading(false)}},[accept]);
 useEffect(()=>{void refresh();const timer=setInterval(()=>void refresh(),60000);return()=>clearInterval(timer)},[refresh]);
 async function signOut(){try{await accountApi('auth/signout',{});accept({user:null})}catch(e){setError('Sign-out could not reach the account service. Your session is still active; reconnect and retry.');throw e}}
 return <Context.Provider value={{session,loading,error,accept,refresh,signOut}}>{children}</Context.Provider>;
}
export function useAuth(){const value=useContext(Context);if(!value)throw Error('Account provider missing.');return value}
export function Protected({children,owner=false}:{children:ReactNode;owner?:boolean}){const {session,loading,error}=useAuth(),path=useLocation();if(loading)return <div className="account-loading">Opening your workspace…</div>;if(!session.user)return <Navigate to={'/signin?next='+encodeURIComponent(path.pathname)} replace/>;if(owner&&session.user.role!=='owner')return <Navigate to="/dashboard" replace/>;return <>{error&&<div className="account-offline" role="alert">{error}</div>}{children}</>}
