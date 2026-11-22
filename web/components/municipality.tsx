"use client";
import {useEffect,useState} from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {api,message} from "@/lib/api";
import {Button} from "./ui/button";
type Ward={ward:string;lat:number;lon:number;kg:number};
type Forecast={method:string;source:string;source_through:string;metrics:{mae_kg:number;rmse_kg:number;test_rows:number;training_mean_mae_kg:number};weeks:{week_start:string;wards:Ward[]}[];route:Ward[]};
type Summary={totals:Record<string,number>;mix:Record<string,number>;trend:Record<string,number>;wards:Record<string,number>};
const Heatmap=dynamic(()=>import("./hotspot-map"),{ssr:false,loading:()=> <div className="skeleton"/>});
const format=(value:number)=>value.toLocaleString("en-IN",{maximumFractionDigits:2});

function Bars({title,values}:{title:string;values:Record<string,number>}){
 const rows=Object.entries(values);
 const max=Math.max(1,...rows.map(([,value])=>value));
 return <section className="card stack"><h2>{title}</h2>{rows.length?rows.map(([name,value])=><div key={name}><div className="row between"><span>{name}</span><strong>{format(value)} kg</strong></div><progress value={value} max={max} aria-label={name}/></div>):<p>No records for this selection.</p>}</section>;
}
export function Municipality({metrics=false}:{metrics?:boolean}){
 const [forecast,setForecast]=useState<Forecast>(),[summary,setSummary]=useState<Summary>();
 const [error,setError]=useState(""),[forecastError,setForecastError]=useState(""),[query,setQuery]=useState(""),[week,setWeek]=useState(0);
 useEffect(()=>{api<Forecast>("/municipality/forecast").then(setForecast).catch(error=>setForecastError(message(error)));},[]);
 useEffect(()=>{if(metrics)return;const controller=new AbortController();api<Summary>("/municipality/summary?"+query,{signal:controller.signal}).then(setSummary).catch(error=>{if(!controller.signal.aborted)setError(message(error));});return()=>controller.abort();},[query,metrics]);
 const current=forecast?.weeks[week];
 return <div className="stack"><div className="heading"><div><h1>{metrics?"Forecast model metrics":"Municipality dashboard"}</h1><p>{metrics?"Evaluation on 312 held-out simulated ward-weeks.":"Track recorded recycling and explore weekly collection scenarios."}</p></div><Button asChild variant="secondary"><Link href={metrics?"/municipality":"/municipality/metrics"}>{metrics?"Dashboard":"Model metrics"}</Link></Button></div>
 {forecastError&&<p role="alert" className="error">{forecastError}</p>}
 {metrics ? forecast?<section className="card stack"><h2>Chronological holdout</h2><div className="row"><span className="pill">MAE {format(forecast.metrics.mae_kg)} kg</span><span className="pill">RMSE {format(forecast.metrics.rmse_kg)} kg</span><span className="pill">Training-mean MAE {format(forecast.metrics.training_mean_mae_kg)} kg</span></div><p>{forecast.method}. The data through {forecast.source_through} are measured in Austin and then allocated to simulated Bengaluru wards. Accuracy for real Bengaluru waste volumes remains unmeasured.</p><a className="button secondary" href={forecast.source}>Open collection dataset</a></section>:!forecastError&&<div className="skeleton" aria-label="Loading model metrics"/>:<>
 <section className="card"><h2>Reporting period</h2><form onSubmit={event=>{event.preventDefault();const fields=new FormData(event.currentTarget);const next=new URLSearchParams();for(const [key,value] of fields)if(value)next.set(key,String(value));if(next.toString()!==query){setError("");setSummary(undefined);setQuery(next.toString());}}}><div className="row"><label>Start date<input name="start" type="date"/></label><label>End date<input name="end" type="date"/></label><label>Dataset<select name="demo"><option value="">Citizen records</option><option value="true">Synthetic demo</option></select></label><Button>Apply filters</Button></div></form><div className="row">{["csv","pdf"].map(kind=><Button key={kind} asChild variant="secondary"><a href={"/api/municipality/report/"+kind+"?"+query} download>Download {kind.toUpperCase()}</a></Button>)}</div></section>
 {error?<p role="alert" className="error">{error}</p>:summary?<><div className="stat-grid">{Object.entries(summary.totals).map(([label,value])=><section className="card stat-card" key={label}><p>{({records:"Records",landfill_kg:"Landfill diverted (kg)",carbon_kg:"Carbon saved (kg CO₂e)",energy_kwh:"Energy saved (kWh)"} as Record<string,string>)[label]}</p><strong>{format(value)}</strong></section>)}</div><div className="map-layout"><Bars title="Material mix" values={summary.mix}/><Bars title="Weekly trend" values={summary.trend}/></div><Bars title="Recorded ward totals" values={summary.wards}/></>:<div className="skeleton" aria-label="Loading municipality data"/>}
 {current&&forecast&&<section className="card stack"><div className="row between"><div><h2>Weekly hotspots</h2><p>Synthetic Bengaluru scenario · estimated kilograms</p></div><label>Week<select value={week} onChange={event=>setWeek(Number(event.target.value))}>{forecast.weeks.map((item,index)=><option key={item.week_start} value={index}>{item.week_start}</option>)}</select></label></div><Heatmap wards={current.wards}/><ul>{current.wards.map(ward=><li key={ward.ward}>{ward.ward} · {format(ward.kg)} kg</li>)}</ul><h3>Suggested collection sequence for {forecast.weeks[0].week_start}</h3><p>Nearest next stop among the four highest-volume simulated wards.</p><ol>{forecast.route.map(ward=><li key={ward.ward}>{ward.ward}</li>)}</ol></section>}
 </>}
 </div>;
}
