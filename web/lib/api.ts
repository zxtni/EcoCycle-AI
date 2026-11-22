export type Person={id:number;name:string;email:string;role:"citizen"|"admin";synthetic:boolean};
export async function api<T>(path:string, options:RequestInit={}):Promise<T>{
 const res=await fetch('/api'+path,{...options,cache:'no-store',headers:{...(options.body && !(options.body instanceof FormData)?{'Content-Type':'application/json'}:{}),...options.headers}});
 if(!res.ok){let detail;try{detail=(await res.json()).detail;}catch{}throw new Error(typeof detail==='string'?detail:res.status===422?'Check the fields and try again.':'The service could not complete this request.');}
 return res.json();
}
export const post=(body:unknown)=>({method:'POST',body:JSON.stringify(body)});
export const message=(e:unknown)=>e instanceof Error?e.message:'Please try again.';
