"use client";
import {useEffect,useState} from "react";
import {api,message,post} from "@/lib/api";
import {Button} from "./ui/button";

type Center={key:number;name:string;lat:number;lon:number;materials:string[];source:string};
type Feedback={id:number;scan_id:number;material:string;note:string;status:string;prediction:{status:string;detections:{material:string}[]}};
type Audit={id:number;actor:number;action:string;created:string};
const materials=["plastic","glass","metal","e-waste"];

export function AdminPanel(){
 const [data,setData]=useState<{centers:Center[];feedback:Feedback[];audit:Audit[]}>();
 const [editing,setEditing]=useState<Center>();
 const [error,setError]=useState(""),[status,setStatus]=useState(""),[busy,setBusy]=useState(false),[version,refresh]=useState(0);
 useEffect(()=>{
  const controller=new AbortController();
  const options={signal:controller.signal};
  Promise.all([api<Center[]>("/admin/centers",options),api<Feedback[]>("/admin/feedback",options),api<Audit[]>("/admin/audit",options)])
   .then(([centers,feedback,audit])=>setData({centers,feedback,audit})).catch(error=>{if(!controller.signal.aborted)setError(message(error));});
  return ()=>controller.abort();
 },[version]);
 async function action(path:string,options:RequestInit,success:string){
  setBusy(true);setError("");setStatus("");
  try{await api("/admin"+path,options);setStatus(success);refresh(version+1);return true;}
  catch(error){setError(message(error));return false;}
  finally{setBusy(false);}
 }
 return <div className="stack"><div className="heading"><div><h1>Administration</h1><p>Manage listings, review corrections and retrain the weekly forecast.</p></div></div>
 {error&&<p role="alert" className="error">{error}</p>}{status&&<p role="status">{status}</p>}
 <section className="card"><h2>Recycling centers</h2><form key={editing?.key??"new"} onSubmit={async event=>{
  event.preventDefault();const form=event.currentTarget;const fields=new FormData(form);
  const body={name:fields.get("name"),lat:Number(fields.get("lat")),lon:Number(fields.get("lon")),materials:fields.getAll("materials")};
  if(!body.materials.length){setError("Select at least one accepted material.");return;}
  if(await action(editing?"/centers/"+editing.key:"/centers",{...post(body),method:editing?"PUT":"POST"},editing?"Center updated.":"Center added.")){form.reset();setEditing(undefined);}
 }}>
 <label>Center name<input name="name" defaultValue={editing?.name} required minLength={2} maxLength={120}/></label>
 <div className="row"><label>Latitude<input name="lat" type="number" step="any" min="-90" max="90" defaultValue={editing?.lat} required/></label><label>Longitude<input name="lon" type="number" step="any" min="-180" max="180" defaultValue={editing?.lon} required/></label></div>
 <fieldset><legend>Accepted materials</legend><div className="row">{materials.map(material=><label className="checkbox" key={material}><input name="materials" type="checkbox" value={material} defaultChecked={editing?.materials.includes(material)}/>{material}</label>)}</div></fieldset>
 <div className="row"><Button disabled={busy}>{editing?"Save changes":"Add center"}</Button>{editing&&<Button type="button" variant="ghost" onClick={()=>setEditing(undefined)}>Cancel edit</Button>}</div>
 </form>
 {data?.centers.map(center=><div className="activity row between" key={center.key}><div><h3>{center.name}</h3><small>{center.source} · {center.materials.join(", ")}</small></div><div className="row"><Button variant="secondary" onClick={()=>setEditing(center)}>Edit {center.name}</Button><Button variant="ghost" disabled={busy} onClick={()=>{if(window.confirm("Remove "+center.name+" from the locator?"))void action("/centers/"+center.key,{method:"DELETE"},"Center removed.");}}>Remove</Button></div></div>)}
 </section>
 <section className="card"><h2>Model corrections</h2>{data?.feedback.length===0&&<p>No corrections submitted.</p>}{data?.feedback.map(item=><article key={item.id} className="activity"><h3>Scan #{item.scan_id} · {item.material}</h3><p>{item.note||"No note supplied."}</p><small>Original result {item.prediction.detections.map(value=>value.material).join(", ")||item.prediction.status} · {item.status}</small>{item.status==="pending"&&<div className="row">{(["accepted","dismissed"] as const).map(state=><Button key={state} variant="secondary" disabled={busy} onClick={()=>void action("/feedback/"+item.id,{...post({status:state}),method:"PUT"},"Correction "+state+".")}>{state==="accepted"?"Accept":"Dismiss"}</Button>)}</div>}</article>)}</section>
 <section className="card"><h2>Weekly model</h2><p>Refit using the bundled collection history and simulated ward allocations.</p><Button disabled={busy} onClick={()=>void action("/forecast/refresh",{method:"POST"},"Weekly forecast model refitted.")}>Refresh model</Button></section>
 <section className="card"><h2>Audit log</h2>{!data&&!error&&<p>Loading audit entries…</p>}{data?.audit.length===0&&<p>No administrative changes recorded yet.</p>}{data?.audit.map(item=><p className="activity" key={item.id}>{item.action}<small>{new Date(item.created).toLocaleString("en-IN")} · Account {item.actor}</small></p>)}</section>
 </div>;
}
