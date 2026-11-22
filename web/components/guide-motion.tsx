"use client";

import { useEffect, useRef } from "react";
import { ChartNoAxesCombined, CircleCheck, CircleUserRound, ClipboardList, MapPin, ScanLine, UserRoundPlus } from "lucide-react";
import type { GuideScene } from "./guide-lottie-data";

const icons = {
  welcome: CircleUserRound,
  account: UserRoundPlus,
  scan: ScanLine,
  loading: ScanLine,
  review: ClipboardList,
  saved: CircleCheck,
  nearby: MapPin,
  impact: ChartNoAxesCombined,
};

export function GuideMotion({scene, onDark = false, className = ""}: {
  scene: GuideScene;
  onDark?: boolean;
  className?: string;
}) {
  const host = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const node = host.current;
    if (!node) return;
    const preference = matchMedia("(prefers-reduced-motion: reduce)");
    let active = true;
    let visible = false;
    let starting = false;
    let animation: import("lottie-web").AnimationItem | undefined;

    function reconcile() {
      if (preference.matches) {
        animation?.destroy();
        animation = undefined;
        return;
      }
      if (animation) {
        if (scene === "loading") {
          if (visible) animation.play();
          else animation.pause();
        }
        return;
      }
      if (!visible || starting) return;
      starting = true;
      Promise.all([import("lottie-web/build/player/lottie_light"), import("./guide-lottie-data")])
        .then(([{default: lottie}, {guideAnimation}]) => {
          if (!active || !visible || preference.matches) return;
          animation = lottie.loadAnimation({
            container: node!, renderer: "svg", autoplay: true,
            loop: scene === "loading", animationData: guideAnimation(scene, onDark),
          });
        })
        .catch(() => { /* The static icon remains visible if the player cannot load. */ })
        .finally(() => { starting = false; });
    }

    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      reconcile();
    });
    observer.observe(node);
    preference.addEventListener("change", reconcile);
    return () => {
      active = false;
      observer.disconnect();
      preference.removeEventListener("change", reconcile);
      animation?.destroy();
    };
  }, [scene, onDark]);

  const Fallback = icons[scene];
  return <span className={`guide-animation ${onDark ? "guide-on-dark" : ""} ${className}`} aria-hidden="true">
    <Fallback className="guide-fallback" strokeWidth={1.6}/>
    <span className="guide-player" ref={host}/>
  </span>;
}
