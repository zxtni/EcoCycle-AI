"use client";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { LocateFixed, MapPin } from "lucide-react";
import { Button } from "./ui/button";
import { api, message } from "@/lib/api";

export type Point={id:string;name:string;lat:number;lon:number;materials:string[];source:string;distance:number;url:string|null};
export type Coordinate=[number,number];
const Map=dynamic(()=>import("./recycling-map"),{ssr:false,loading:()=> <div className="skeleton" aria-label="Loading map"/>});
export function Locator(){
 const [position,setPosition]=useState<Coordinate>([12.9716,77.5946]),[filter,setFilter]=useState(""),[selected,select]=useState("");
 const [data,setData]=useState<{centers:Point[];live_available:boolean}>(),[error,setError]=useState(""),[geo,setGeo]=useState(""),[busy,setBusy]=useState(false),[retry,setRetry]=useState(0);
 useEffect(()=>{
  const controller=new AbortController();
  const params=new URLSearchParams({lat:String(position[0]),lon:String(position[1])});
  if(filter)params.set("material",filter);
  api<typeof data>("/centers?"+params,{signal:controller.signal}).then(setData).catch(error=>{if(!controller.signal.aborted)setError(message(error));});
  return ()=>controller.abort();
 },[position,filter,retry]);
 function locate(){
  if(!navigator.geolocation){setGeo("Location is unavailable on this browser.");return;}
  setBusy(true);setGeo("");
  navigator.geolocation.getCurrentPosition(({coords})=>{setPosition([coords.latitude,coords.longitude]);setData(undefined);setError("");select("");setBusy(false);},()=>{setGeo("We could not get your location. Bengaluru remains selected.");setBusy(false);},{timeout:8000,maximumAge:300000});
 }
 return <><div className="heading"><div><h1>Center locator</h1><p>Find recycling drop-off points within 20 km of your location.</p></div></div>
 <section className="card"><div className="row between"><label>Accepted material<select value={filter} onChange={event=>{setFilter(event.target.value);setData(undefined);setError("");select("");}}><option value="">All materials</option>{["plastic","glass","metal","e-waste"].map(item=><option key={item}>{item}</option>)}</select></label><Button onClick={locate} variant="secondary" disabled={busy}><LocateFixed size={18}/>{busy?"Finding location…":"Use my location"}</Button></div>{geo&&<p role="status">{geo}</p>}</section>
 {error?<section className="card scan-result"><p role="alert">{error}</p><Button onClick={()=>{setError("");setRetry(retry+1);}}>Retry</Button></section>:!data?<div className="skeleton scan-result" aria-label="Finding centers"/>:<><p role="status">{data.live_available?"OpenStreetMap and local listings.":"Live listings are unavailable. Showing local listings."} Confirm acceptance before visiting.</p>
 <div className="map-layout"><Map points={data.centers} origin={position} selected={selected} onSelect={select}/><section className="card results"><h2>{data.centers.length} nearby {data.centers.length===1?"result":"results"}</h2>{data.centers.length===0&&<p>No centers matched. Try a different filter or location.</p>}
 {data.centers.map(center=><article className="activity" key={center.id}><button className="button ghost place-title" aria-pressed={selected===center.id} onClick={()=>select(center.id)}><MapPin size={17}/>{center.name}</button><small>{center.distance} km · {center.source}</small><p>{center.materials.join(", ")||"Materials unlisted"}</p><div className="row">{center.source!=="Synthetic demo"&&<Button variant="secondary" asChild><a href={"https://www.google.com/maps/dir/?api=1&destination="+center.lat+","+center.lon} target="_blank" rel="noreferrer">Directions</a></Button>}{center.url&&<a className="button ghost" href={center.url}>OSM listing</a>}</div></article>)}</section></div></>}</>;
}
