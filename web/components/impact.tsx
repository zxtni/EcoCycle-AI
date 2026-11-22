"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Leaf, Zap, Scale, Wallet, Flame, Award } from "lucide-react";
import { api, message, post } from "@/lib/api";
import { Button } from "./ui/button";

type Factor = {label:string; inr_per_kg:number; carbon_kg_per_kg:number; energy_kwh_per_kg:number; recyclability_score:number; proxy:string; score_source:string};
type Totals = {value_inr:number; carbon_kg:number; energy_kwh:number; landfill_kg:number};
type Breakdown = Totals & {material:string; weight:number; factor:Factor; version:string};
type Report = {totals:Totals; streak:number; badges:string[]; history:(Breakdown & {id:number; created:string; ward:string})[]};
const format = (n:number) => new Intl.NumberFormat("en-IN",{maximumFractionDigits:2}).format(n);
const stats = [
  {key:"landfill_kg", label:"Landfill diverted", unit:"kg", icon:Scale},
  {key:"carbon_kg", label:"Carbon saved", unit:"kg CO₂e", icon:Leaf},
  {key:"energy_kwh", label:"Energy saved", unit:"kWh", icon:Zap},
  {key:"value_inr", label:"Material value", unit:"INR", icon:Wallet},
] as const;

function Counter({value}:{value:number}) {
  const reduced = useReducedMotion();
  const [current, setCurrent] = useState(0);
  useEffect(() => {
    if (reduced) return;
    const start = performance.now();
    let frame:number;
    function tick(time:number) {
      const progress = Math.min((time-start)/500,1);
      setCurrent(value * (1-Math.pow(1-progress,3)));
      if (progress < 1) frame=requestAnimationFrame(tick);
    }
    frame=requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  },[value,reduced]);
  return <><span aria-hidden="true">{format(reduced ? value : current)}</span><span className="sr-only">{format(value)}</span></>;
}

export function Impact({overview=false, signedIn=true}:{overview?:boolean; signedIn?:boolean}) {
  const [data,setData]=useState<Report>();
  const [error,setError]=useState("");
  const [attempt,retry]=useState(0);
  const reducedMotion = useReducedMotion();
  useEffect(() => {
    if (!signedIn) return;
    const controller=new AbortController();
    api<Report>("/impact",{signal:controller.signal}).then(setData).catch(error => {
      if (!controller.signal.aborted) setError(message(error));
    });
    return () => controller.abort();
  },[signedIn,attempt]);
  return <>
    {overview ? <div className="sectionhead"><h2>My impact</h2><Link href="/impact" className="button ghost">View history</Link></div> : <div className="heading"><div><h1>My impact</h1><p>Estimated benefits from recycling you recorded.</p></div></div>}
    {!signedIn ? <section className="card"><p>Sign in to see your recycling history and lifetime totals.</p><Button asChild><Link href="/account">Sign in</Link></Button></section> : error ? <section className="card"><p role="alert">{error}</p><Button onClick={()=>{setError("");retry(attempt+1);}}>Retry</Button></section> : !data ? <div className="skeleton" aria-label="Loading impact"/> : <>
      <div className="stat-grid">{stats.map(({key,label,unit,icon:Icon}) => <motion.div key={key} className={`card stat-card stat-${key}`} initial={false} whileHover={reducedMotion ? undefined : {y:-3}} transition={{type:"spring",stiffness:320,damping:27}}><span className="stat-icon"><Icon size={21}/></span><p>{label}</p><strong><Counter value={data.totals[key]}/></strong> <small>{unit}</small></motion.div>)}</div>
      <div className="sectionhead"><h2>{overview ? "Recent activity" : "Recycling history"}</h2><span className="row"><Flame size={18}/>{data.streak} day streak</span></div>
      {!data.history.length ? <section className="card"><h3>No recycling records yet</h3><p>Scan an item and confirm its weight to start.</p><Button asChild><Link href="/scan">Scan waste</Link></Button></section> : <section className="card activity-card">{data.history.slice(0,overview?5:undefined).map(entry => <div className="activity row between" key={entry.id}><div className="row activity-title"><span className="activity-icon"><Leaf size={19} aria-hidden="true"/></span><div><h3>{entry.factor.label}</h3><small>{new Date(entry.created).toLocaleDateString("en-IN")} · {entry.ward}</small></div></div><div className="activity-weight"><strong>{format(entry.weight)} kg</strong><small>₹{format(entry.value_inr)} est.</small></div></div>)}</section>}
      {!overview && <><div className="sectionhead"><h2>Badges</h2></div><section className="card row">{data.badges.length ? data.badges.map(badge=><span key={badge} className="pill"><Award size={18}/>{badge}</span>) : <p>Record your first item to earn a badge.</p>}</section></>}
    </>}
  </>;
}

export function ValueForm({id, suggested}:{id:number; suggested?:string}) {
  const [material,setMaterial]=useState(suggested||""),[weight,setWeight]=useState(""),[ward,setWard]=useState("Central");
  const [discarded,setDiscarded]=useState(false);
  const [table,setTable]=useState<{materials:Record<string,Factor>;wards:string[];version:string;price_source:string;impact_source:string}>();
  const [result,setResult]=useState<Breakdown>(),[error,setError]=useState(""),[busy,setBusy]=useState(false),[saved,setSaved]=useState(false),[estimated,setEstimated]=useState(false);
  useEffect(()=>{api<typeof table>("/materials").then(setTable).catch(error=>setError(message(error)));},[]);
  async function submit(confirm:boolean) {
    setBusy(true);setError("");
    try {
      const path=confirm ? "/scans/"+id+"/confirm" : "/materials/estimate";
      setResult(await api<Breakdown>(path,post({material,weight:Number(weight),ward,weight_source:estimated?"estimated":"user",discarded_electronics:discarded})));
      setSaved(confirm);
    } catch (error) {
      setError(message(error));
    } finally { setBusy(false); }
  }
  function invalidate() {setResult(undefined);setError("");}
  return <section className="card scan-result"><h2>Recycling estimate</h2><p>Enter your item’s weight. Save the record after you commit to recycling it.</p>
  {table && <form onSubmit={event=>{event.preventDefault();void submit(false);}}>
    <label>Material<select required disabled={busy||saved} value={material} onChange={event=>{
      setMaterial(event.target.value);
      setDiscarded(false);
      if(estimated){setWeight("");setEstimated(false);}
      invalidate();
    }}><option value="">Choose a material</option>{Object.entries(table.materials).map(([key,factor])=><option key={key} value={key}>{key==="e-waste"?"Electronics for recycling":factor.label}</option>)}</select></label>
    <label>Weight (kg)<input required disabled={saved} type="number" min="0.001" max="10000" step="0.001" value={weight} onChange={event=>{setWeight(event.target.value);setEstimated(false);invalidate();}}/></label>
    <Button type="button" variant="secondary" disabled={!material||busy||saved} onClick={()=>{setWeight(({plastic:"0.025",glass:"0.250",metal:"0.050","e-waste":"0.150"} as Record<string,string>)[material]);setEstimated(true);invalidate();}}>Use a typical item weight</Button>
    {estimated && <p>Typical item assumption. Weigh the item for a more accurate result.</p>}
    <label>Ward<select disabled={saved} value={ward} onChange={event=>setWard(event.target.value)}><option>Central</option>{table.wards.map(item=><option key={item}>{item}</option>)}</select></label>
    {material==="e-waste" && <label className="checkbox"><input type="checkbox" checked={discarded} disabled={busy||saved} onChange={event=>setDiscarded(event.target.checked)}/>I am discarding this device for recycling.</label>}
    {!saved && <div><Button disabled={busy||!material}>Calculate estimate</Button></div>}
  </form>}
  {error && <p role="alert" className="error">{error}</p>}
  {result && table && <div className="estimate stack"><h3>₹{format(result.value_inr)} estimated value</h3><p>{format(result.weight)} kg × ₹{format(result.factor.inr_per_kg)}/kg. The buyer’s actual rate can vary.</p><p>{result.factor.recyclability_score}/100 recovery benchmark for {result.factor.proxy}.</p><div className="row">{stats.slice(0,3).map(({key,label,unit})=><span className="pill" key={key}>{format(result[key])} {unit} · {label}</span>)}</div><small>Factor version {result.version} · <a href={table.price_source}>Rate card</a> · <a href={table.impact_source}>EPA WARM</a> · <a href={result.factor.score_source}>Recovery data</a></small>{saved ? <p role="status">Saved to <Link href="/impact">your impact history</Link>.</p> : <div><Button disabled={busy||(material==="e-waste"&&!discarded)} onClick={()=>void submit(true)}>Save to my impact</Button></div>}</div>}
  </section>;
}

