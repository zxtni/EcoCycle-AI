"use client";

import { useEffect, useRef, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { api, message, post, type Person } from "@/lib/api";
import { Button } from "./ui/button";
import { GuideMotion } from "./guide-motion";

type Identity = {accounts: {id: {
  initialize: (options: {client_id: string; callback: (result: {credential: string}) => void}) => void;
  renderButton: (element: HTMLElement, options: object) => void;
}}};
declare global { interface Window { google?: Identity } }

export function Auth({onSuccess}: {onSuccess: (person: Person) => void}) {
  const [signup, setSignup] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
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
    <div className="auth-visual"><div>
      <GuideMotion scene={signup ? "account" : "welcome"} className="auth-motion" onDark/>
      <h2>{signup ? "Start with one scan" : "Pick up where you left off"}</h2>
      <p>{signup ? "Photograph an item, review its material and record what you recycle." : "Find your previous scans and see your recycling impact."}</p>
    </div></div>
    <div className="auth-body">
      <h1 id="auth-title">{signup ? "Create account" : "Welcome back"}</h1>
      <p>{signup ? "Start tracking the materials you recycle." : "Sign in to access your recycling history."}</p>
      <form className="auth-form" onSubmit={submit}>
        {signup && <label>Name<input required name="name" maxLength={80} autoComplete="name"/></label>}
        <label>Email<input required name="email" type="email" autoComplete="email"/></label>
        <div className="password-field">
          <label htmlFor="auth-password">Password</label>
          <div className="password-control">
            <input required id="auth-password" name="password" type={showPassword ? "text" : "password"}
              minLength={10} maxLength={128} autoComplete={signup ? "new-password" : "current-password"}
              aria-describedby={signup ? "password-hint" : undefined}/>
            <button type="button" className="iconbtn password-toggle" onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}>
              {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
            </button>
          </div>
          {signup && <small id="password-hint">Use at least 10 characters.</small>}
        </div>
        {error && <p role="alert" className="error">{error}</p>}
        <Button disabled={busy}>{busy ? "Please wait…" : signup ? "Create account" : "Sign in"}</Button>
      </form>
      <Button className="auth-switch" variant="ghost" disabled={busy} onClick={() => { setSignup(!signup); setShowPassword(false); setError(""); }}>
        {signup ? "Already registered? Sign in" : "Create an account"}
      </Button>
      <div className="auth-provider" ref={google}/>
    </div>
  </section>;
}
