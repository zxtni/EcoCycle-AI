"use client";
import {useEffect,useRef} from "react";
import L from "leaflet";
import "leaflet.markercluster";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import type {Coordinate,Point} from "./locator";
export default function RecyclingMap({points,origin,selected,onSelect}:{points:Point[];origin:Coordinate;selected:string;onSelect:(id:string)=>void}){
 const node=useRef<HTMLDivElement>(null);
 const map=useRef<L.Map|null>(null);
 const pins=useRef(new Map<string,L.Marker>());
 const group=useRef<L.MarkerClusterGroup|null>(null);
 useEffect(()=>{
  if(!node.current)return;
  const view=L.map(node.current,{scrollWheelZoom:false}).setView(origin,12);
  map.current=view;
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(view);
  L.circleMarker(origin,{radius:6,color:"#145e44",fillOpacity:1}).bindTooltip("Search origin").addTo(view);
  const layer=L.markerClusterGroup({showCoverageOnHover:false});
  const current=pins.current;
  group.current=layer;
  for(const point of points){
   const popup=document.createElement("div");
   popup.textContent=point.name+" · "+point.distance+" km";
   const icon=L.divIcon({className:"recycling-pin",iconSize:[20,20],iconAnchor:[10,10]});
   const marker=L.marker([point.lat,point.lon],{icon,title:point.name}).bindPopup(popup);
   marker.on("click",()=>onSelect(point.id));
   current.set(point.id,marker);layer.addLayer(marker);
  }
  view.addLayer(layer);
  if(points.length)view.fitBounds(L.latLngBounds([origin,...points.map(point=>[point.lat,point.lon] as Coordinate)]),{padding:[30,30],maxZoom:14});
  return ()=>{current.clear();view.remove();map.current=null;group.current=null;};
 },[points,origin,onSelect]);
 useEffect(()=>{
  const marker=pins.current.get(selected);
  if(marker)group.current?.zoomToShowLayer(marker,()=>marker.openPopup());
 },[selected]);
 return <div ref={node} className="map" aria-label="Interactive map of nearby recycling centers"/>;
}
