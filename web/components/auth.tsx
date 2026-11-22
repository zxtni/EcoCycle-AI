"use client";
import { useEffect,useRef,useState } from "react";
import { api,post,message,type Person } from "@/lib/api";
import { Button } from "./ui/button";
type Identity={accounts:{id:{initialize:(options:{client_id:string;callback:(r:{credential:string})=>void})=>void;renderButton:(el:HTMLElement,options:object)=>void}}};
declare global {interface Window {google?:Identity}}
export function Auth({onSuccess}:{onSuccess:(p:Person)=>void}) {
 const [signup,setSignup]=useState(false),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 const google=useRef<HTMLDivElement>(null);
 useEffect(()=>{let alive=true;api<{client_id:string}>("/auth/google/config").then(c=>{
 if(!c.client_id||!alive)return;
 const start=()=>{if(!alive||!google.current||!window.google)return;window.google.accounts.id.initialize({client_id:c.client_id,callback:r=>api<Person>("/auth/google",post(r)).then(onSuccess).catch(e=>setError(message(e)))});window.google.accounts.id.renderButton(google.current,{theme:"outline",size:"large"});};
 if(window.google){start();return;}const script=document.createElement("script");script.src="https://accounts.google.com/gsi/client";script.async=true;script.onload=start;document.head.append(script);
 }).catch(e=>setError(message(e)));return()=>{alive=false};},[onSuccess]);
 return <section className="card narrow"><span className="eyebrow">YOUR ACCOUNT</span><h2>{signup?"Create an account":"Welcome back"}</h2><p>Save your scans and follow your recycling impact.</p><form onSubmit={async e=>{e.preventDefault();setBusy(true);setError("");const data=Object.fromEntries(new FormData(e.currentTarget));try{onSuccess(await api<Person>("/auth/"+(signup?"register":"login"),post(data)));}catch(e){setError(message(e))}finally{setBusy(false)}}}>
 {signup&&<label>Name<input required name="name" maxLength={80} autoComplete="name"/></label>}<label>Email<input required name="email" type="email" autoComplete="email"/></label><label>Password<input required name="password" type="password" minLength={10} maxLength={128} autoComplete={signup?"new-password":"current-password"}/></label>
 {error&&<p role="alert" className="error">{error}</p>}<Button disabled={busy}>{busy?"Please wait…":signup?"Create account":"Sign in"}</Button></form><Button variant="ghost" onClick={()=>{setSignup(!signup);setError("")}}>{signup?"Already registered? Sign in":"Create an account"}</Button><div ref={google}/></section>;
}
