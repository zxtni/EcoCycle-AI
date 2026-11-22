"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowUpRight, BatteryCharging, BottleWine, ChartNoAxesCombined, CircleUserRound,
  Droplet, LayoutGrid, LogIn, LogOut, MapPin, Moon, PanelLeft, Recycle,
  ScanLine, Settings2, Sun, Wine,
} from "lucide-react";
import { Auth } from "./auth";
import { Scanner } from "./scanner";
import { Impact } from "./impact";
import { Locator } from "./locator";
import { Municipality } from "./municipality";
import { AdminPanel } from "./admin-panel";
import { GuideMotion } from "./guide-motion";
import { Button } from "./ui/button";
import { api, message, type Person } from "@/lib/api";

const citizenLinks = [
  { path: "/", name: "Overview", compact: "Home", icon: LayoutGrid },
  { path: "/scan", name: "Scan waste", compact: "Scan", icon: ScanLine },
  { path: "/impact", name: "My impact", compact: "Impact", icon: ChartNoAxesCombined },
  { path: "/locator", name: "Center locator", compact: "Nearby", icon: MapPin },
];

const adminLinks = [
  { path: "/municipality", name: "Municipality", icon: PanelLeft },
  { path: "/admin", name: "Administration", icon: Settings2 },
];

const materials = [
  { name: "Plastic", example: "Bottles and packaging", icon: BottleWine, color: "mint" },
  { name: "Glass", example: "Bottles and jars", icon: Wine, color: "lilac" },
  { name: "Metal", example: "Cans and light scrap", icon: Droplet, color: "sand" },
  { name: "E-waste", example: "Small electronics", icon: BatteryCharging, color: "sky" },
];

function Brand() {
  return <Link href="/" className="brand" aria-label="EcoCycle AI home">
    <span className="brandmark"><Recycle size={22} strokeWidth={2.2} aria-hidden="true"/></span>
    <span>EcoCycle<span className="brand-ai"> AI</span></span>
  </Link>;
}

function Sidebar({path, user, onSignOut}: {
  path: string;
  user: Person | null;
  onSignOut: () => void;
}) {
  return <aside className="sidebar">
    <Brand/>
    <nav className="rail-nav" aria-label="Workspace">
      {citizenLinks.map(({path: href, name, icon: Icon}) => <Link key={href} href={href} aria-current={path === href ? "page" : undefined}>
        <Icon size={19} aria-hidden="true"/><span>{name}</span>
      </Link>)}
    </nav>
    {user?.role === "admin" && <nav className="rail-nav rail-admin" aria-label="Municipal tools">
      {adminLinks.map(({path: href, name, icon: Icon}) => <Link key={href} href={href} aria-current={path.startsWith(href) ? "page" : undefined}>
        <Icon size={19} aria-hidden="true"/><span>{name}</span>
      </Link>)}
    </nav>}
    <div className="sidebarfoot">
      {user ? <button className="rail-account" onClick={onSignOut}><LogOut size={19} aria-hidden="true"/>Sign out</button>
        : <Link className="rail-account" href="/account"><LogIn size={19} aria-hidden="true"/>Sign in</Link>}
    </div>
  </aside>;
}

function Dock({path}: {path: string}) {
  return <nav className="bottomnav" aria-label="Mobile tabs">
    {citizenLinks.map(({path: href, name, compact, icon: Icon}) => <Link
      key={href} href={href} aria-label={name} aria-current={path === href ? "page" : undefined}
      className={href === "/scan" ? "dock-scan" : undefined}
    >
      <span className="dock-icon"><Icon size={21} strokeWidth={2} aria-hidden="true"/></span>
      <span>{compact}</span>
    </Link>)}
  </nav>;
}

function Overview({user, ready}: {user: Person | null; ready: boolean}) {
  return <>
    <div className="heading overview-heading">
      <div>
        <h1>Overview<span className="title-dot">.</span></h1>
        <p>{user ? `Welcome back, ${user.name.trim().split(/\s+/)[0]}.` : "Scan materials, track impact and find where to recycle."}</p>
      </div>
      <span className="overview-location"><MapPin size={16} aria-hidden="true"/> Bengaluru</span>
    </div>
    <div className="feature-grid">
      <section className="hero" aria-labelledby="scanner-feature">
        <div className="hero-art" aria-hidden="true"/>
        <div className="hero-copy">
          <span className="hero-label"><ScanLine size={15} aria-hidden="true"/> Material scanner</span>
          <h2 id="scanner-feature">What can<br/>you recycle?</h2>
          <p>Take a photo to identify the material and estimate its recycling value.</p>
          <Button asChild><Link href="/scan"><ScanLine size={18} aria-hidden="true"/> Scan waste</Link></Button>
        </div>
      </section>
      <div className="shortcut-grid">
        <Link href="/locator" className="shortcut shortcut-nearby">
          <div className="shortcut-top"><GuideMotion scene="nearby" className="shortcut-icon"/><ArrowUpRight size={19} aria-hidden="true"/></div>
          <div><h2>Find a drop-off</h2><p>Search nearby recycling centers.</p></div>
        </Link>
        <Link href="/impact" className="shortcut shortcut-impact">
          <div className="shortcut-top"><GuideMotion scene="impact" className="shortcut-icon"/><ArrowUpRight size={19} aria-hidden="true"/></div>
          <div><h2>Track your impact</h2><p>See what you’ve saved.</p></div>
        </Link>
      </div>
    </div>
    {user && <Impact overview/>}
    {!ready && <div className="skeleton overview-skeleton" aria-label="Loading your dashboard"/>}
    {ready && !user && <section aria-labelledby="materials-title" className="materials">
      <div className="sectionhead"><h2 id="materials-title">Supported materials</h2></div>
      <ul className="material-grid">
        {materials.map(({name, example, icon: Icon, color}) => <li className="material-card" key={name}>
          <span className={`material-icon ${color}`}><Icon size={22} aria-hidden="true"/></span>
          <strong>{name}</strong>
          <small>{example}</small>
        </li>)}
      </ul>
    </section>}
  </>;
}

export function Workspace({page}: {page: string}) {
  const [user, setUser] = useState<Person | null>(null);
  const [ready, setReady] = useState(false);
  const [dark, setDark] = useState(false);
  const [sessionError, setSessionError] = useState("");
  const router = useRouter();
  const path = page === "overview" ? "/" : "/" + page;

  useEffect(() => {
    if (process.env.NODE_ENV === "production" && "serviceWorker" in navigator) {
      void navigator.serviceWorker.register("/sw.js").catch(console.error);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    api<Person>("/auth/me", {signal: controller.signal})
      .then(setUser)
      .catch(() => {})
      .finally(() => { if (!controller.signal.aborted) setReady(true); });
    const savedTheme = localStorage.getItem("theme");
    const isDark = savedTheme === "dark" || (!savedTheme && matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.dataset.theme = isDark ? "dark" : "light";
    const frame = requestAnimationFrame(() => setDark(isDark));
    return () => { controller.abort(); cancelAnimationFrame(frame); };
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  const signIn = useCallback((person: Person) => {
    setUser(person);
    if (page === "account") router.push("/");
  }, [page, router]);

  async function signOut() {
    setSessionError("");
    try {
      await api("/auth/logout", {method: "POST"});
      setUser(null);
      router.push("/account");
    } catch (error) {
      setSessionError(message(error));
    }
  }

  function currentView() {
    if (page === "overview") return <Overview user={user} ready={ready}/>;
    if (!ready) return <div className="skeleton" aria-label="Loading account"/>;
    if (!user) return <Auth onSuccess={signIn}/>;
    if (page === "scan") return <Scanner/>;
    if (page === "impact") return <Impact/>;
    if (page === "locator") return <Locator/>;
    if (page === "municipality" || page === "municipality/metrics" || page === "admin") {
      if (user.role !== "admin") return <section className="card"><h1>Administrator access required</h1></section>;
      return page === "admin" ? <AdminPanel/> : <Municipality metrics={page.endsWith("/metrics")}/>;
    }
    if (page === "account") return <section className="card narrow account-card stack">
      <span className="avatar account-avatar" aria-hidden="true">{user.name.charAt(0).toUpperCase()}</span>
      <div><h1>{user.name}</h1><p>{user.email}</p></div>
      {user.role === "admin" && <div className="row">{adminLinks.map(({path, name, icon: Icon}) =>
        <Button asChild variant="secondary" key={path}><Link href={path}><Icon size={17} aria-hidden="true"/>{name}</Link></Button>
      )}</div>}
      <div><Button variant="secondary" onClick={signOut}><LogOut size={18} aria-hidden="true"/>Sign out</Button></div>
    </section>;
    return <section className="card stack"><h1>Page unavailable</h1><div><Button asChild><Link href="/">Return to overview</Link></Button></div></section>;
  }

  return <div className="frame">
    <a href="#content" className="skip">Skip to content</a>
    <Sidebar path={path} user={user} onSignOut={signOut}/>
    <div className="main">
      <header className="topbar">
        <div className="mobile-brand"><Brand/></div>
        <div className="desktop-location"><MapPin size={17} aria-hidden="true"/><span>Bengaluru, India</span></div>
        <div className="actions">
          <button className="iconbtn" aria-label="Toggle color theme" aria-pressed={dark} onClick={toggleTheme}>
            {dark ? <Sun size={19} aria-hidden="true"/> : <Moon size={19} aria-hidden="true"/>}
          </button>
          <Link className="avatar" aria-label="Your account" href="/account">
            {user ? user.name.charAt(0).toUpperCase() : <CircleUserRound size={21} aria-hidden="true"/>}
          </Link>
        </div>
      </header>
      <main id="content">
        {sessionError && <p role="alert" className="error">{sessionError}</p>}
        {currentView()}
      </main>
    </div>
    <Dock path={path}/>
  </div>;
}
