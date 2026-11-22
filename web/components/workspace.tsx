"use client";
import Link from "next/link";
import { useEffect,useState } from "react";
import { useRouter } from "next/navigation";
import { Recycle,LayoutDashboard,ScanLine,MapPin,ChartNoAxesCombined,Settings2,Menu,X,Sun,Moon,LogIn,LogOut,Leaf,ChevronRight,PanelLeft } from "lucide-react";
import { Auth } from './auth';
import { Scanner } from './scanner';
import { Button } from "./ui/button";
import { api,type Person } from "@/lib/api";
const nav=[{page:"overview",name:"Overview",icon:LayoutDashboard},{page:"scan",name:"Scan waste",icon:ScanLine},{page:"impact",name:"My impact",icon:ChartNoAxesCombined},{page:"locator",name:"Center locator",icon:MapPin}];
const admin=[{page:"municipality",name:"Municipality",icon:PanelLeft},{page:"admin",name:"Administration",icon:Settings2}];
export function Workspace({page}:{page:string}){
 const [user,setUser]=useState<Person|null>(null),[ready,setReady]=useState(false),[open,setOpen]=useState(false),[dark,setDark]=useState(false);
 const router=useRouter();
 useEffect(()=>{api<Person>("/auth/me").then(setUser).catch(()=>{}).finally(()=>setReady(true));const saved=localStorage.getItem("theme");const d=saved==="dark"||(!saved&&matchMedia("(prefers-color-scheme:dark)").matches);requestAnimationFrame(()=>setDark(d));document.documentElement.dataset.theme=d?"dark":"light";},[]);
 function toggle(){setDark(!dark);document.documentElement.dataset.theme=dark?"light":"dark";localStorage.setItem("theme",dark?"light":"dark");}
 const title=[...nav,...admin].find(n=>n.page===page)?.name||"Account";
 const links=(items:typeof nav)=>items.map(n=><Link key={n.page} href={n.page==="overview"?"/":"/"+n.page} onClick={()=>setOpen(false)} aria-current={page===n.page?"page":undefined}><n.icon size={19}/>{n.name}</Link>);
 return <div className="frame"><a href="#content" className="skip">Skip to content</a>{open&&<button aria-label="Close navigation" className="scrim" onClick={()=>setOpen(false)}/>}<aside className={open?"sidebar open":"sidebar"}><Link className="brand" href="/"><span className="brandmark"><Recycle size={25} strokeWidth={2.4}/></span>EcoCycle<span className="ai">AI</span></Link><div className="sidelabel">WORKSPACE</div><nav>{links(nav)}</nav>{user?.role==="admin"&&<><div className="sidelabel">MUNICIPAL TOOLS</div><nav>{links(admin)}</nav></>}<div className="sidebarfoot"><div className="city"><span className="cityicon"><MapPin size={18}/></span><div><strong>Bengaluru</strong><small>Karnataka, India</small></div></div><button className="account" onClick={async()=>{if(user){await api("/auth/logout",{method:"POST"});setUser(null);}router.push("/account");setOpen(false)}}>{user?<LogOut size={17}/>:<LogIn size={17}/>} {user?"Sign out":"Sign in"}</button></div></aside>
 <div className="main"><header><button className="mobilemenu iconbtn" aria-label={open?"Close menu":"Open menu"} onClick={()=>setOpen(!open)}>{open?<X/>:<Menu/>}</button><span className="crumb">Workspace <ChevronRight size={14}/> <strong>{title}</strong></span><div className="actions"><button className="iconbtn" aria-label="Toggle color theme" onClick={toggle}>{dark?<Sun size={18}/>:<Moon size={18}/>}</button><Link className="avatar" aria-label="Your account" href="/account">{user?user.name.charAt(0).toUpperCase():<Leaf size={19}/>}</Link></div></header>
 <main id="content">{page==="overview"?<><div className="heading"><div><div className="eyebrow"><span className="dot"/> CITIZEN WORKSPACE</div><h1>Recycling overview</h1><p>Your materials, activity and environmental impact at a glance.</p></div></div><Hero/></>:!ready?<div className="skeleton" aria-label="Loading account"/>:!user||page==="account"&&!user?<Auth onSuccess={p=>{setUser(p);if(page==="account")router.push("/")}}/>:page==="scan"?<Scanner/>:page==="account"?<section className="card"><h1>{user.name}</h1><p>{user.email} · {user.role}</p></section>:<section className="card"><h1>{title}</h1><Link href="/">Return to overview</Link></section>}</main></div><nav className="bottomnav">{links(nav)}</nav></div>
}
export function Hero(){return <section className="hero"><div className="hero-copy"><span className="hero-label"><ScanLine size={15}/> AI MATERIAL SCANNER</span><h2>Give waste a<br/>second life.</h2><p>Identify a material and discover its recycling value with a single photo.</p><Button asChild><Link href="/scan"><ScanLine size={18}/>Scan waste</Link></Button></div></section>}

