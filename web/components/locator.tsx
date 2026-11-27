"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { LocateFixed, MapPin, Navigation } from "lucide-react";
import { Button } from "./ui/button";
import { GuideMotion } from "./guide-motion";
import { api, message } from "@/lib/api";

export type Point = {
  id: string; name: string; lat: number; lon: number; materials: string[];
  source: string; distance: number; url: string | null;
};
export type Coordinate = [number, number];

const Map = dynamic(() => import("./recycling-map"), {
  ssr: false,
  loading: () => <div className="skeleton map" aria-label="Loading map"/>,
});
const materialChoices = [
  ["plastic", "Plastic"], ["glass", "Glass"], ["metal", "Metal"], ["e-waste", "E-waste"],
];
const BENGALURU: Coordinate = [12.9716, 77.5946];

export function Locator() {
  const [position, setPosition] = useState<Coordinate>();
  const [filter, setFilter] = useState("");
  const [selected, select] = useState("");
  const [data, setData] = useState<{centers: Point[]; live_available: boolean}>();
  const [error, setError] = useState("");
  const [geo, setGeo] = useState("");
  const [busy, setBusy] = useState(true);
  const [locationRequest, requestLocation] = useState(0);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (!position) return;
    const controller = new AbortController();
    const params = new URLSearchParams({lat: String(position[0]), lon: String(position[1])});
    if (filter) params.set("material", filter);
    const deadline = AbortSignal.timeout(15000);
    const signal = AbortSignal.any([controller.signal, deadline]);
    api<typeof data>("/centers?" + params, {signal}).then(results => {
      if (!controller.signal.aborted) setData(results);
    }).catch(error => {
      if (!controller.signal.aborted) {
        setError(deadline.aborted ? "The recycling directory is taking too long. Try Google Maps or retry here." : message(error));
      }
    });
    return () => controller.abort();
  }, [position, filter, retry]);

  function resetResults() {
    setData(undefined);
    setError("");
    select("");
  }

  useEffect(() => {
    let active = true;
    const unavailable = () => {
      if (!active) return;
      setGeo("Location unavailable. Allow location access and retry, or search Bengaluru.");
      setBusy(false);
    };
    if (!navigator.geolocation) {
      const frame = requestAnimationFrame(unavailable);
      return () => cancelAnimationFrame(frame);
    }
    navigator.geolocation.getCurrentPosition(({coords}) => {
      if (!active) return;
      setPosition([coords.latitude, coords.longitude]);
      resetResults();
      setGeo("Searching near your location.");
      setBusy(false);
    }, unavailable, {timeout: 8000, maximumAge: 300000});
    return () => { active = false; };
  }, [locationRequest]);

  function locate() {
    setBusy(true);
    setGeo("");
    requestLocation(count => count + 1);
  }

  const mapsQuery = filter === "e-waste" ? "e-waste collection" : filter ? filter + " recycling center" : "recycling drop-off";
  const mapsLink = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(mapsQuery + (position ? " near " + position.join(",") : " near me"));

  return <>
    <div className="heading"><div><h1>Center locator</h1><p>Find recycling drop-off points within 1,000 km.</p></div></div>
    <section className="card locator-controls">
      <div className="row between">
        <label>Accepted material
          <select value={filter} onChange={event => { setFilter(event.target.value); resetResults(); }}>
            <option value="">All materials</option>
            {materialChoices.map(([value, label]) => <option value={value} key={value}>{label}</option>)}
          </select>
        </label>
        <Button onClick={locate} variant="secondary" disabled={busy}>
          <LocateFixed size={18} aria-hidden="true"/>{busy ? "Finding location…" : "Use my location"}
        </Button>
      </div>
      {geo && <p role="status">{geo}</p>}
      {!busy && <div className="row">
        {!position && <Button variant="secondary" onClick={() => { setPosition(BENGALURU); setGeo("Searching near Bengaluru."); }}>Search Bengaluru</Button>}
        <Button variant="secondary" asChild><a href={mapsLink} target="_blank" rel="noreferrer">Search in Google Maps</a></Button>
      </div>}
    </section>
    {busy || !position ? null : error ? <section className="card scan-result">
      <p role="alert">{error}</p><Button onClick={() => { setError(""); setRetry(retry + 1); }}>Retry</Button>
    </section> : !data ? <section className="card scan-result guide-panel" role="status">
      <GuideMotion scene="nearby"/><h2>Finding centers</h2><p>Checking recycling listings for your map area.</p>
    </section> : <>
      <div className="map-layout locator-map">
        <Map points={data.centers} origin={position} selected={selected} onSelect={select}/>
        <section className="card results">
          <h2>{data.centers.length} nearby {data.centers.length === 1 ? "result" : "results"}</h2>
          <p className="listing-source" role="status">
            {data.live_available ? "OpenStreetMap and local listings." : "Showing local listings while live results are unavailable."}
          </p>
          {data.centers.length === 0 && <div className="stack">
            <p>{data.live_available
              ? "No listed centers matched. Some facilities may be missing from the map or their accepted materials may be unlisted."
              : "The live directory did not respond and there are no matching saved listings in this area."}</p>
            <a href="https://apps.bbmpgov.in/SWM/Home/Forms/Home.aspx" target="_blank" rel="noreferrer">Bengaluru municipal waste directory</a>
          </div>}
          {data.centers.map(center => <article className="activity place-card" key={center.id}>
            <button className="button ghost place-title" aria-pressed={selected === center.id} onClick={() => select(center.id)}>
              <span className="place-icon"><MapPin size={18} aria-hidden="true"/></span>
              <span>{center.name}<small>{center.distance} km · {center.source}</small></span>
            </button>
            <p>{center.materials.join(", ") || "Materials unlisted"}</p>
            <div className="row">
              {center.source !== "Synthetic demo" && <Button variant="secondary" asChild>
                <a href={"https://www.google.com/maps/dir/?api=1&destination=" + center.lat + "," + center.lon} target="_blank" rel="noreferrer">
                  <Navigation size={15} aria-hidden="true"/> Directions
                </a>
              </Button>}
              {center.url && <a className="button ghost" href={center.url}>OSM listing</a>}
            </div>
          </article>)}
          {data.centers.length > 0 && <small>Confirm materials with the center before visiting.</small>}
        </section>
      </div>
    </>}
  </>;
}
