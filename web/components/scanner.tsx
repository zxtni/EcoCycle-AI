"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, Upload, ScanLine } from "lucide-react";
import { api, message } from "@/lib/api";
import { Button } from "./ui/button";

type Result = {id: number; status: "detected" | "blurry" | "no_detection"; model: string; detections: {material: string; confidence: number; box: [number, number, number, number]}[]};

export function Scanner() {
  const [image, setImage] = useState<File>();
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState<Result>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [camera, setCamera] = useState<MediaStream>();
  const video = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    if (!camera) return;
    if (video.current) video.current.srcObject = camera;
    return () => camera.getTracks().forEach(track => track.stop());
  }, [camera]);
  async function startCamera() {
    setError("");
    try {
      setCamera(await navigator.mediaDevices.getUserMedia({video: {facingMode: {ideal: "environment"}}}));
    } catch {
      setError("Camera unavailable. Check your browser permissions or upload a photo.");
    }
  }
  function capture() {
    const source = video.current;
    if (!source?.videoWidth) return;
    const canvas = document.createElement("canvas");
    const scale = Math.min(1, 1280 / Math.max(source.videoWidth, source.videoHeight));
    canvas.width = Math.round(source.videoWidth * scale);
    canvas.height = Math.round(source.videoHeight * scale);
    canvas.getContext("2d")?.drawImage(source, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
      if (blob) choose(new File([blob], "capture.jpg", {type: "image/jpeg"}));
      setCamera(undefined);
    }, "image/jpeg", 0.9);
  }
  useEffect(() => {
    if (!image) return;
    const url = URL.createObjectURL(image);
    queueMicrotask(() => setPreview(url));
    return () => URL.revokeObjectURL(url);
  }, [image]);
  function choose(file?: File) {
    setImage(file);
    setResult(undefined);
    setFeedback("");
    setError("");
  }
  async function scan() {
    if (!image) return;
    setBusy(true);
    setError("");
    const data = new FormData();
    data.set("image", image);
    try {
      setResult(await api<Result>("/scans", {method: "POST", body: data}));
    } catch (error) {
      setError(message(error));
    } finally {
      setBusy(false);
    }
  }
  return <><div className="heading"><div><h1>Scan waste</h1><p>Photograph plastic, glass, metal or electronics in good light.</p></div></div>
    <section className="card stack">
      <div className="row">
        <label className="button secondary"><Upload size={18}/>Upload photo<input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={event => choose(event.target.files?.[0])}/></label>
        <Button variant="secondary" disabled={busy || !!camera} onClick={startCamera}><Camera size={18}/>Open camera</Button>
      </div>
      {camera && <div className="stack"><video className="scan-video" ref={video} autoPlay playsInline muted aria-label="Camera preview"/><div className="row"><Button onClick={capture}>Take photo</Button><Button variant="secondary" onClick={() => setCamera(undefined)}>Close camera</Button></div></div>}
      {image && preview && <div className="scan-preview">
        {/* The source is a transient local upload rather than a remote image. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={preview} alt="Your uploaded waste photo"/>
        {result?.detections.map(({material, confidence, box: [left, top, right, bottom]}, index) =>
          <span className="scan-box" key={index} style={{left: left*100+"%", top: top*100+"%", width: (right-left)*100+"%", height: (bottom-top)*100+"%"}} aria-hidden="true"><span>{material} {Math.round(confidence*100)}%</span></span>)}
      </div>}
      <div><Button disabled={!image || busy} onClick={scan}><ScanLine size={18}/>{busy ? "Analyzing photo…" : "Analyze photo"}</Button></div>
      {error && <p role="alert" className="error">{error}</p>}
    </section>
    {result && <section className="card scan-result" aria-live="polite">
      <h2>{result.status === "detected" ? "Detected materials" : result.status === "blurry" ? "Try a clearer photo" : "No material detected"}</h2>
      {result.detections.length ? <ul>{result.detections.map((item, index) => <li key={index}>{item.material} · {Math.round(item.confidence*100)}% confidence</li>)}</ul> : <p>Use good light, get closer and keep the object in frame.</p>}
      <details><summary>Wrong result?</summary>
        <form onSubmit={async event => {
          event.preventDefault();
          setFeedback("");
          const fields = new FormData(event.currentTarget);
          try {
            await api("/scans/" + result.id + "/correction", {method: "PUT", body: JSON.stringify(Object.fromEntries(fields))});
            setFeedback("Correction saved for review.");
          } catch (error) {
            setFeedback(message(error));
          }
        }}>
          <label>Correct material<select name="material">{["plastic","glass","metal","e-waste"].map(value => <option key={value}>{value}</option>)}</select></label>
          <label>Note (optional)<textarea name="note" maxLength={400}/></label>
          <Button>Save correction</Button>
        </form>
        <p role="status">{feedback}</p>
      </details>
    </section>}
  </>;
}

