"use client";
import {useEffect,useRef} from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
type Ward={ward:string;lat:number;lon:number;kg:number};
export default function HotspotMap({wards}:{wards:Ward[]}){
 const element=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  if(!element.current || !wards.length)return;
  const map=L.map(element.current,{scrollWheelZoom:false});
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
  const max=Math.max(1,...wards.map(ward=>ward.kg));
  const layer=L.featureGroup(wards.map(ward=>{
   const weight=ward.kg/max;
   const label=document.createElement("span");label.textContent=ward.ward+" · "+ward.kg+" kg";
   return L.circleMarker([ward.lat,ward.lon],{radius:8+weight*27,color:"#962e1a",fillColor:weight>.7?"#e0542d":"#f4a541",fillOpacity:.67}).bindTooltip(label);
  })).addTo(map);
  map.fitBounds(layer.getBounds(),{padding:[36,36]});
  return ()=>{map.remove();};
 },[wards]);
 return <div className="map" aria-label="Hotspot map showing estimated volumes by ward"/>;
}
