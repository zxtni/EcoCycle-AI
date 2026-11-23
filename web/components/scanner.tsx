"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, Check, ImagePlus, Lightbulb, ScanLine, Tag } from "lucide-react";
import { api, message } from "@/lib/api";
import { Button } from "./ui/button";
import { ValueForm } from "./impact";
import { GuideMotion } from "./guide-motion";

type Box = [number, number, number, number];

type Result = {
  id: number;
  status: "detected" | "blurry" | "no_detection";
  model: string;
  detections: {material: string; confidence: number; box: Box}[];
  identified_objects?: {name: string; confidence: number; box: Box}[];
};

function materialLabel(material: string) {
  return material === "e-waste" ? "Electronics" : material;
}

function confidenceLabel(score: number) {
  return score > 0.99 ? "99%+" : `${Math.round(score * 100)}%`;
}

export function Scanner() {
  const [image, setImage] = useState<File>();
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState<Result>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [saved, setSaved] = useState(false);
  const [showObjects, setShowObjects] = useState(false);
  const [camera, setCamera] = useState<MediaStream>();
  const [openingCamera, setOpeningCamera] = useState(false);
  const cameraRequest = useRef(0);
  const video = useRef<HTMLVideoElement>(null);
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const step = saved ? 3 : result ? 2 : 1;
  const objects = result?.identified_objects ?? [];
  const materials = result?.detections ?? [];
  const objectOverlay = objects.length > 0 && (showObjects || materials.length === 0);
  const boxes = objectOverlay
    ? objects.map(item => ({...item, label: item.name}))
    : materials.map(item => ({...item, label: materialLabel(item.material)}));

  useEffect(() => () => { cameraRequest.current++; }, []);
  useEffect(() => {
    if (!camera) return;
    if (video.current) video.current.srcObject = camera;
    return () => camera.getTracks().forEach(track => track.stop());
  }, [camera]);

  useEffect(() => {
    if (!image) return;
    const url = URL.createObjectURL(image);
    const frame = requestAnimationFrame(() => setPreview(url));
    return () => { cancelAnimationFrame(frame); URL.revokeObjectURL(url); };
  }, [image]);

  useEffect(() => {
    if (result) resultHeading.current?.focus();
  }, [result]);

  async function startCamera() {
    setError("");
    setOpeningCamera(true);
    const request = ++cameraRequest.current;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: {ideal: "environment"}}});
      if (request === cameraRequest.current) setCamera(stream);
      else stream.getTracks().forEach(track => track.stop());
    } catch {
      if (request === cameraRequest.current) setError("Camera unavailable. Check your browser permissions or upload a photo.");
    } finally {
      if (request === cameraRequest.current) setOpeningCamera(false);
    }
  }

  function choose(file: File) {
    setPreview("");
    setImage(file);
    setCamera(undefined);
    setResult(undefined);
    setShowObjects(false);
    setSaved(false);
    setFeedback("");
    setError("");
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
    }, "image/jpeg", 0.9);
  }

  async function scan(detail = false) {
    if (!image || busy || saved || camera || openingCamera) return;
    setBusy(true);
    setFeedback("");
    setError("");
    const data = new FormData();
    data.set("image", image);
    if (detail) data.set("detail", "true");
    try {
      setResult(await api<Result>("/scans", {method: "POST", body: data}));
      setShowObjects(false);
    } catch (error) {
      setError(message(error));
    } finally {
      setBusy(false);
    }
  }

  return <>
    <div className="heading"><div><h1>Scan waste</h1><p>Identify plastic, glass, metal and electronics from a photo.</p></div></div>
    <ol className="scan-steps" role="list" aria-label="Scan progress">
      {["Photo", "Review", "Save"].map((label, index) => <li key={label} aria-current={step === index + 1 ? "step" : undefined}>
        <span className="scan-step-index" aria-hidden="true">{step > index + 1 || saved ? <Check size={15}/> : index + 1}</span>
        <span>{label}</span>
      </li>)}
    </ol>
    <div className="scan-layout">
      <section className="card scan-card" aria-label="Material scanner">
        <div className="scan-stage" aria-busy={busy}>
          {busy && <div className="scan-busy"><GuideMotion scene="loading" onDark/><span>Checking materials…</span></div>}
          {camera ? <video className="scan-video" ref={video} autoPlay playsInline muted aria-label="Camera preview"/>
            : image && preview ? <div className="scan-preview">
              {/* The image source is a transient local upload. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={preview} alt="Your uploaded waste photo"/>
              {boxes.map(({label, confidence, box: [left, top, right, bottom]}, index) =>
                <span className={objectOverlay ? "scan-box scan-object-box" : "scan-box"} key={index} style={{left: left * 100 + "%", top: top * 100 + "%", width: (right - left) * 100 + "%", height: (bottom - top) * 100 + "%"}} aria-hidden="true">
                  <span>{label} {confidenceLabel(confidence)}</span>
                </span>)}
            </div> : <div className="viewfinder">
              <GuideMotion scene="scan" onDark/>
              <h2>Frame the item</h2>
              <p>Use your camera or select a photo from this device.</p>
            </div>}
        </div>
        {objects.length > 0 && materials.length > 0 && !busy && !camera && <div className="row scan-overlay-controls" role="group" aria-label="Photo overlay">
          <Button variant={showObjects ? "secondary" : "default"} aria-pressed={!showObjects} onClick={() => setShowObjects(false)}>Material boxes</Button>
          <Button variant={showObjects ? "default" : "secondary"} aria-pressed={showObjects} onClick={() => setShowObjects(true)}>Object boxes</Button>
        </div>}
        <div className="scan-actions">
          {camera ? <>
            <Button variant="secondary" onClick={() => setCamera(undefined)}>Close camera</Button>
            <Button className="scan-submit" onClick={capture}><Camera size={17} aria-hidden="true"/> Take photo</Button>
          </> : <>
            <label className="button secondary"><ImagePlus size={17} aria-hidden="true"/>Upload photo
              <input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" disabled={busy || openingCamera}
                onChange={event => {
                  const file = event.target.files?.[0];
                  if (file) choose(file);
                  event.target.value = "";
                }}/>
            </label>
            <Button variant="secondary" disabled={busy || openingCamera} onClick={startCamera}>
              <Camera size={17} aria-hidden="true"/>{openingCamera ? "Opening…" : "Open camera"}
            </Button>
            <Button className="scan-submit" disabled={!image || busy || openingCamera || saved} onClick={() => void scan()}>
              <ScanLine size={17} aria-hidden="true"/>{busy ? "Analyzing photo…" : "Analyze photo"}
            </Button>
          </>}
        </div>
        {error && <p role="alert" className="error">{error}</p>}
        {saved && <p role="status">Upload or take a new photo to record another item.</p>}
      </section>
      <aside className="card scan-hints">
        <span className="stat-icon"><Lightbulb size={21} aria-hidden="true"/></span>
        <h2>For a clearer scan</h2>
        <ul><li>Photograph one item in good light.</li><li>Show its full shape against a plain background.</li><li>Upload JPEG, PNG or WebP up to 8 MB.</li></ul>
      </aside>
    </div>
    {result && !busy && <section className="card scan-result" aria-live="polite">
      <div className="guide-state"><GuideMotion scene="review"/><h2 tabIndex={-1} ref={resultHeading}>
        {result.status === "detected" ? "Detected materials" : result.status === "blurry" ? "Try a clearer photo" : objects.length ? "Objects recognized" : "No material detected"}
      </h2></div>
      {result.detections.length
        ? <ul className="detection-list">{result.detections.map((item, index) => <li className="pill" key={index}><Tag size={15} aria-hidden="true"/>{materialLabel(item.material)} · {confidenceLabel(item.confidence)} model confidence</li>)}</ul>
        : <p>{objects.length ? "Choose a material below if you know what the item is made of." : "Move closer and photograph one item against a plain background. You can also select a material below if you know it."}</p>}
      {objects.length > 0 && <div className="scan-object-results">
        {result.status === "detected" && <h3>Recognized objects</h3>}
        <ul className="detection-list">{objects.map((item, index) => <li className="pill" key={index}>{item.name} · {confidenceLabel(item.confidence)} object confidence</li>)}</ul>
        <p>Object names help identify the item. Check its material before recording it.</p>
      </div>}
      {result.detections.some(item => item.material === "e-waste") &&
        <p>The photo shows electronics. Record the device as e-waste only if you are discarding it for recycling.</p>}
      {!saved && result.status !== "blurry" &&
        <Button variant="secondary" disabled={!!camera || openingCamera} onClick={() => void scan(true)}>Search for small items</Button>}
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
          <label>Correct material<select name="material">{["plastic", "glass", "metal", "e-waste"].map(value => <option key={value}>{value}</option>)}</select></label>
          <label>Note (optional)<textarea name="note" maxLength={400}/></label>
          <div><Button>Save correction</Button></div>
        </form>
        {feedback && <p role="status">{feedback}</p>}
      </details>
    </section>}
    {result && !busy && <ValueForm key={result.id} id={result.id} onSaved={() => setSaved(true)}
      suggested={result.detections.length === 1 && result.detections[0].material !== "e-waste" ? result.detections[0].material : undefined}/>}
  </>;
}
