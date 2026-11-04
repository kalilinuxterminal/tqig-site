export type User={id:string;email:string;name:string;role:'owner'|'member';disabled:boolean;created:number;last_login:number|null};
export type Session={user:User|null;csrf?:string;expires?:number;remember?:boolean};
export const portalUrl=(import.meta.env.VITE_PORTAL_URL||(location.hostname==='localhost'||location.hostname==='127.0.0.1'?`${location.protocol}//${location.hostname}:8770`:location.origin)).replace(/\/$/,'');
let csrf='';
export function rememberSession(session:Session){csrf=session.csrf||''}
export async function accountApi<T=any>(path:string,body?:unknown):Promise<T>{
 const response=await fetch(`${portalUrl}/api/${path}`,{method:body===undefined?'GET':'POST',credentials:'include',headers:{...(body===undefined?{}:{'Content-Type':'application/json','X-TQIG-CSRF':csrf})},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(15000)});
 const data=await response.json().catch(()=>({detail:'The account service is unavailable. Start TQIG or check the server connection.'}));
 if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Check the form fields and try again.');
 return data;
}
