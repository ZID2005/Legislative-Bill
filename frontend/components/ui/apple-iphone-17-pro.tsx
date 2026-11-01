/**
 * components/ui/apple-iphone-17-pro.tsx
 * =====================================
 * Institutional Hardware Mockup: Apple iPhone 17 Pro Max
 *
 * Implements a high-precision, CSS/SVG-composed smartphone device frame:
 * - Precision rounded chassis with titanium/graphite brushed outer bezel
 * - Interactive Dynamic Island with animated expansion states (default, compact, expanded, minimal)
 * - Calibrated iOS status bar (cellular signal, Wi-Fi, battery pill with live percentage)
 * - Integrated physical buttons (Action button, Volume up/down, Side power key)
 * - Bottom home indicator bar
 * - Scalable responsive layout designed for showcase viewports without overflow
 */

"use client";

import React from "react";
import { cn } from "@/lib/utils";

export type DynamicIslandSize = "default" | "compact" | "expanded" | "minimal";
export type FrameColor = "graphite" | "silver" | "gold" | "deep-blue" | "black";

export interface IPhone17ProMaxProps {
  children?: React.ReactNode;
  batteryLevel?: number;
  dynamicIslandSize?: DynamicIslandSize;
  frameColor?: FrameColor;
  signalStrength?: number; // 1 to 4
  time?: string;
  onDynamicIslandTap?: () => void;
  className?: string;
}

export function IPhone17ProMax({
  children,
  batteryLevel = 94,
  dynamicIslandSize = "default",
  frameColor = "graphite",
  signalStrength = 3,
  time = "9:41",
  onDynamicIslandTap,
  className,
}: IPhone17ProMaxProps) {
  // Frame bezel gradient configurations
  const frameBorderStyles: Record<FrameColor, string> = {
    graphite: "bg-gradient-to-b from-[#3a3a3c] via-[#242426] to-[#1c1c1e] ring-1 ring-white/15 shadow-2xl shadow-black/90",
    silver: "bg-gradient-to-b from-[#e2e2e6] via-[#b0b0b5] to-[#7a7a80] ring-1 ring-white/30 shadow-2xl shadow-black/80",
    gold: "bg-gradient-to-b from-[#e3c79a] via-[#ba9b6d] to-[#6e593c] ring-1 ring-amber-300/20 shadow-2xl shadow-black/90",
    "deep-blue": "bg-gradient-to-b from-[#2b3a4a] via-[#1b2531] to-[#0e161f] ring-1 ring-blue-400/20 shadow-2xl shadow-black/90",
    black: "bg-gradient-to-b from-[#282828] via-[#161616] to-[#0c0c0c] ring-1 ring-white/10 shadow-2xl shadow-black/95",
  };

  // Dynamic Island sizing profiles
  const dynamicIslandConfig: Record<DynamicIslandSize, { width: string; height: string; rounded: string }> = {
    minimal: { width: "w-14", height: "h-4", rounded: "rounded-full" },
    compact: { width: "w-20", height: "h-5.5", rounded: "rounded-full" },
    default: { width: "w-28", height: "h-6.5", rounded: "rounded-full" },
    expanded: { width: "w-56", height: "h-11", rounded: "rounded-2xl" },
  };

  const island = dynamicIslandConfig[dynamicIslandSize] || dynamicIslandConfig.default;

  return (
    <div
      className={cn(
        "relative mx-auto flex items-center justify-center select-none",
        "w-[260px] sm:w-[290px] md:w-[310px]",
        className
      )}
      style={{
        maxHeight: "100%",
      }}
      role="region"
      aria-label="Apple iPhone 17 Pro Max Device Frame"
    >
      {/* Outer Titanium Chassis Outer Bezel */}
      <div
        className={cn(
          "relative w-full rounded-[44px] p-[3px] transition-all duration-300",
          frameBorderStyles[frameColor]
        )}
      >
        {/* Physical Side Buttons: Action Button & Volume on Left */}
        <div
          aria-hidden="true"
          className="absolute -left-[5px] top-[90px] w-[3px] h-[22px] bg-[#3f3f42] rounded-l-sm"
          title="Action Button"
        />
        <div
          aria-hidden="true"
          className="absolute -left-[5px] top-[124px] w-[3px] h-[38px] bg-[#3f3f42] rounded-l-sm"
          title="Volume Up"
        />
        <div
          aria-hidden="true"
          className="absolute -left-[5px] top-[170px] w-[3px] h-[38px] bg-[#3f3f42] rounded-l-sm"
          title="Volume Down"
        />

        {/* Physical Side Power / Lock Button on Right */}
        <div
          aria-hidden="true"
          className="absolute -right-[5px] top-[130px] w-[3px] h-[52px] bg-[#3f3f42] rounded-r-sm"
          title="Side Button"
        />

        {/* Inner Ultra-thin Black Screen Bezel */}
        <div className="relative w-full h-[480px] sm:h-[500px] rounded-[41px] bg-[#000000] p-[7px] flex flex-col overflow-hidden shadow-inner">
          {/* Active Screen Display Surface */}
          <div className="relative w-full h-full rounded-[35px] bg-[#09090b] text-[#f4f4f4] overflow-hidden flex flex-col border border-white/[0.04]">
            {/* Top Status Bar Container */}
            <div className="relative z-30 w-full px-5 pt-2 pb-1 flex items-center justify-between text-[11px] font-semibold text-white/90">
              {/* Clock */}
              <span className="font-mono tracking-tight text-[11px] pl-1">{time}</span>

              {/* Dynamic Island Capsule */}
              <div
                onClick={onDynamicIslandTap}
                className={cn(
                  "absolute left-1/2 -translate-x-1/2 top-1.5 bg-black border border-white/10 flex items-center justify-between px-2 cursor-pointer transition-all duration-300 ease-out z-40 hover:border-white/25",
                  island.width,
                  island.height,
                  island.rounded
                )}
                role="button"
                tabIndex={0}
                aria-label="Dynamic Island"
                title="Tap Dynamic Island to expand/collapse"
              >
                {dynamicIslandSize === "expanded" ? (
                  <div className="w-full flex items-center justify-between text-[9px] font-mono px-1">
                    <span className="flex items-center gap-1 text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      SEANCE INTELLIGENCE
                    </span>
                    <span className="text-white/60">LIVE</span>
                  </div>
                ) : (
                  <>
                    <div className="w-2.5 h-2.5 rounded-full bg-[#151515] border border-white/10 flex items-center justify-center">
                      <div className="w-1 h-1 rounded-full bg-blue-900/60" />
                    </div>
                    <div className="w-1.5 h-1.5 rounded-full bg-[#0d0d0d]" />
                  </>
                )}
              </div>

              {/* Status Icons: Cellular, Wi-Fi, Battery */}
              <div className="flex items-center gap-1.5 pr-1 text-white/80">
                {/* Cellular Signal Bars (SVG) */}
                <svg
                  className="w-3.5 h-3"
                  viewBox="0 0 16 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-hidden="true"
                >
                  <rect x="0" y="10" width="2.5" height="4" rx="0.5" fill="currentColor" fillOpacity={signalStrength >= 1 ? 1 : 0.25} />
                  <rect x="4.5" y="7" width="2.5" height="7" rx="0.5" fill="currentColor" fillOpacity={signalStrength >= 2 ? 1 : 0.25} />
                  <rect x="9" y="4" width="2.5" height="10" rx="0.5" fill="currentColor" fillOpacity={signalStrength >= 3 ? 1 : 0.25} />
                  <rect x="13.5" y="1" width="2.5" height="13" rx="0.5" fill="currentColor" fillOpacity={signalStrength >= 4 ? 1 : 0.25} />
                </svg>

                {/* Wi-Fi Icon (SVG) */}
                <svg
                  className="w-3.5 h-3"
                  viewBox="0 0 16 14"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-hidden="true"
                >
                  <path d="M1 4.5C5 1.5 11 1.5 15 4.5" />
                  <path d="M3.5 7.5C6.5 5 9.5 5 12.5 7.5" />
                  <circle cx="8" cy="11.5" r="1" fill="currentColor" />
                </svg>

                {/* Battery Pill with Live Level */}
                <div className="flex items-center gap-0.5" title={`Battery ${batteryLevel}%`}>
                  <div className="w-5 h-2.5 rounded-[3px] border border-white/70 p-[1px] flex items-center">
                    <div
                      className="h-full bg-white rounded-[1.5px] transition-all"
                      style={{ width: `${Math.min(100, Math.max(0, batteryLevel))}%` }}
                    />
                  </div>
                  <div className="w-[1.5px] h-1 bg-white/70 rounded-r-sm" />
                </div>
              </div>
            </div>

            {/* Screen Content Slot */}
            <div className="relative flex-1 w-full overflow-hidden flex flex-col pt-1">
              {children}
            </div>

            {/* Bottom Home Indicator Bar */}
            <div className="w-full pb-1 pt-0.5 flex justify-center z-30">
              <div
                aria-hidden="true"
                className="w-24 h-1 bg-white/40 rounded-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default IPhone17ProMax;

