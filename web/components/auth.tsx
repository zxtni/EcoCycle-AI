"use client";

import { useEffect, useRef, useState } from "react";
import { api, message, post, type Person } from "@/lib/api";
import { Button } from "./ui/button";

type Identity = {accounts: {id: {
  initialize: (options: {client_id: string; callback: (result: {credential: string}) => void}) => void;
  renderButton: (element: HTMLElement, options: object) => void;
}}};
declare global { interface Window { google?: Identity } }

export function Auth({onSuccess}: {onSuccess: (person: Person) => void}) {
  const [signup, setSignup] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const google = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    let script: HTMLScriptElement | undefined;
    api<{client_id: string}>("/auth/google/config").then(({client_id}) => {
      if (!client_id || !alive) return;
      const start = () => {
        if (!alive || !google.current || !window.google) return;
        window.google.accounts.id.initialize({
          client_id,
          callback: result => api<Person>("/auth/google", post(result)).then(onSuccess).catch(error => setError(message(error))),
        });
        window.google.accounts.id.renderButton(google.current, {theme: "outline", size: "large"});
      };
      if (window.google) {
        start();
      } else {
        script = document.createElement("script");
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        script.onload = start;
        document.head.append(script);
      }
    }).catch(error => { if (alive) setError(message(error)); });
    return () => { alive = false; script?.remove(); };
  }, [onSuccess]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const fields = Object.fromEntries(new FormData(event.currentTarget));
    try {
      onSuccess(await api<Person>(signup ? "/auth/register" : "/auth/login", post(fields)));
    } catch (error) {
      setError(message(error));
    } finally {
      setBusy(false);
    }
  }

  return <section className="auth-shell" aria-labelledby="auth-title">
    <div className="auth-visual"><div><h2>Your recycling record</h2><p>Keep your photos’ results and impact in one place.</p></div></div>
    <div className="auth-body">
      <h1 id="auth-title">{signup ? "Create account" : "Welcome back"}</h1>
      <p>{signup ? "Start tracking the materials you recycle." : "Sign in to access your recycling history."}</p>
      <form className="auth-form" onSubmit={submit}>
        {signup && <label>Name<input required name="name" maxLength={80} autoComplete="name"/></label>}
        <label>Email<input required name="email" type="email" autoComplete="email"/></label>
        <label>Password<input required name="password" type="password" minLength={10} maxLength={128} autoComplete={signup ? "new-password" : "current-password"}/></label>
        {error && <p role="alert" className="error">{error}</p>}
        <Button disabled={busy}>{busy ? "Please wait…" : signup ? "Create account" : "Sign in"}</Button>
      </form>
      <Button className="auth-switch" variant="ghost" onClick={() => { setSignup(!signup); setError(""); }}>
        {signup ? "Already registered? Sign in" : "Create an account"}
      </Button>
      <div className="auth-provider" ref={google}/>
    </div>
  </section>;
}
