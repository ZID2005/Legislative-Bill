/**
 * components/ui/feature-carousel.tsx
 * ===================================
 * TASK 1.15C — SEANCE NATIVE ANIMATED INTELLIGENCE SHOWCASE.
 *
 * Upgraded from static screenshot presentation to native, animated React compositions:
 * - Stage 01: LegislativeJourneyVisual (Procedural passage & assent journey)
 * - Stage 02: WorkspaceCommandCenterVisual (Multi-source operational telemetry)
 * - Stage 03: CorporateExposureNetworkVisual (Dynamic SVG corporate beta graph)
 * - Stage 04: StateIntelligenceMapVisual (India statutory map & 0.00% prediction firewall)
 * - Stage 05: WatchlistIntelligenceVisual (Compact surveillance & listed securities)
 * - Stage 06: AlertIntelligenceVisual (Radial threshold dial & multi-channel routing)
 * - Stage 07: SeanceMobileShowcase (Apple iPhone 17 Pro Max hardware mockup & mobile intelligence)
 * - Stage 08: WorkspaceLaunchVisual (Unified subsystem deployment matrix)
 *
 * Retains authentic Cult UI / 21st.dev FeatureCarousel motion behavior:
 * - Direction-aware spring-physics entrance (cubic-bezier(0.16, 1, 0.3, 1))
 * - Interactive hover depth elevation
 * - Strict prefers-reduced-motion compliance
 * - Preserves 4-stage and 8-stage configurations, backward-compatible fallback, and all exported types
 */

"use client";

import React, { useState, useEffect, useCallback, useId, useRef } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import {
  LegislativeJourneyVisual,
  WorkspaceCommandCenterVisual,
  CorporateExposureNetworkVisual,
  StateIntelligenceMapVisual,
  WatchlistIntelligenceVisual,
  AlertIntelligenceVisual,
  SeanceMobileShowcase,
  WorkspaceLaunchVisual,
} from "@/components/onboarding/showcase";

// ---------------------------------------------------------------------------
// Type Definitions
// ---------------------------------------------------------------------------

export interface FeatureImage {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
}

export interface FeatureStage {
  step: number;
  title: string;
  subtitle?: string;
  description: string;
  tag?: string;
  badge?: string;
  images?: FeatureImage[];
  metrics?: { label: string; value: string }[];
  visual?: React.ReactNode;
}

// ---------------------------------------------------------------------------
// Canonical 4-Stage Showcase (Backward-Compatible Standard Export)
// ---------------------------------------------------------------------------

export const DEFAULT_FOUR_STAGES: FeatureStage[] = [
  {
    step: 1,
    tag: "STATUTORY INTELLIGENCE",
    title: "Legislative Bill Dossier & Mechanics",
    subtitle: "20 Central Parliament Acts (22 Scanned Records)",
    description:
      "Deep statutory provisions, historical amendments, and procedural journey timelines with rigorous verification.",
    images: [],
    visual: <LegislativeJourneyVisual />,
    metrics: [
      { label: "Parliamentary Acts", value: "20 Central" },
      { label: "Scanned Records", value: "22 Dossiers" },
    ],
  },
  {
    step: 2,
    tag: "WORKSPACE ARCHITECTURE",
    title: "Command Center & Custom Watchlists",
    subtitle: "Multi-Tenant Institutional Telemetry",
    description:
      "Real-time regulatory intake feeds, customizable priority watchlists, and unified telemetry streams.",
    images: [],
    visual: <WorkspaceCommandCenterVisual />,
    metrics: [
      { label: "Telemetry Feeds", value: "12/12 Live" },
      { label: "Active Watchlists", value: "Enterprise" },
    ],
  },
  {
    step: 3,
    tag: "QUANTITATIVE EXPOSURE",
    title: "Corporate Exposure Matrix & Beta Mapping",
    subtitle: "47 Liquid Securities across 13 Macro Sectors",
    description:
      "Direct statutory clause mapping to corporate balance sheets, legal entity IDs, and historical stock return models.",
    images: [],
    visual: <CorporateExposureNetworkVisual />,
    metrics: [
      { label: "Listed Securities", value: "47 Quant" },
      { label: "Corporate Universe", value: "70 Entities" },
    ],
  },
  {
    step: 4,
    tag: "SUB-NATIONAL JURISDICTION",
    title: "State Assemblies & Statutory Firewall",
    subtitle: "AP, KA, KL, and TS Enacted Acts",
    description:
      "Unpolluted sub-national gazette coverage governed by a strict zero-stock-prediction architectural firewall.",
    images: [],
    visual: <StateIntelligenceMapVisual />,
    metrics: [
      { label: "Enacted State Acts", value: "44 Acts" },
      { label: "Stock Prediction Leakage", value: "0.00% (Firewall)" },
    ],
  },
];

// ---------------------------------------------------------------------------
// Canonical 8-Stage Showcase for Full Seance Onboarding Flow
// ---------------------------------------------------------------------------

export const SEANCE_EIGHT_STAGES: FeatureStage[] = [
  {
    step: 1,
    tag: "STAGE 01 · FOUNDATION",
    title: "Legislative Bill Dossier & Mechanics",
    subtitle: "20 Central Parliament Acts (22 Records)",
    description:
      "Deep parliamentary provisions, section-by-section diffs, and procedural legislative timelines with verified provenance.",
    images: [],
    visual: <LegislativeJourneyVisual />,
    metrics: [
      { label: "Central Acts", value: "20 Central" },
      { label: "Scanned Records", value: "22 Dossiers" },
    ],
  },
  {
    step: 2,
    tag: "STAGE 02 · WORKSPACE",
    title: "Command Center & Organization Profile",
    subtitle: "Enterprise Governance & Sector Templates",
    description:
      "Configurable workspace profiles tailored to Institutional Equity Research, Macro Funds, and Regulatory Affairs.",
    images: [],
    visual: <WorkspaceCommandCenterVisual />,
    metrics: [
      { label: "Reporting Presets", value: "5 Domains" },
      { label: "Telemetry Streams", value: "Real-time" },
    ],
  },
  {
    step: 3,
    tag: "STAGE 03 · CORPORATE UNIVERSE",
    title: "Corporate Exposure Matrix & Entity Mapping",
    subtitle: "70 Corporations & Listed Securities",
    description:
      "Direct mapping between statutory provisions, corporate revenue streams, and liquid NSE/BSE securities.",
    images: [],
    visual: <CorporateExposureNetworkVisual />,
    metrics: [
      { label: "Quant Securities", value: "47 Liquid" },
      { label: "Macro Sectors", value: "13 Granular" },
    ],
  },
  {
    step: 4,
    tag: "STAGE 04 · SUB-NATIONAL JURISDICTION",
    title: "State Assemblies & Statutory Firewall",
    subtitle: "Andhra Pradesh, Karnataka, Kerala & Telangana",
    description:
      "Comprehensive state gazettes under strict zero-stock-prediction architectural firewall guarantees.",
    images: [],
    visual: <StateIntelligenceMapVisual />,
    metrics: [
      { label: "Enacted State Acts", value: "44 Total" },
      { label: "Prediction Firewall", value: "Zero Leakage" },
    ],
  },
  {
    step: 5,
    tag: "STAGE 05 · SURVEILLANCE",
    title: "Priority Regulatory Watchlists",
    subtitle: "Real-time Tracking of Landmark Legislation",
    description:
      "Instant portfolio tracking across telecom, digital personal data, energy transitions, and labor codes.",
    images: [],
    visual: <WatchlistIntelligenceVisual />,
    metrics: [
      { label: "Watchlist Feeds", value: "Curated" },
      { label: "Multi-State Scope", value: "Central + 4 States" },
    ],
  },
  {
    step: 6,
    tag: "STAGE 06 · INTELLIGENCE RULES",
    title: "Notification Center & Digest Frequency",
    subtitle: "Real-time Alerts & Scheduled Briefs",
    description:
      "Fine-grained delivery controls for regulatory intake triggers, committee hearings, and state gazette releases.",
    images: [],
    visual: <AlertIntelligenceVisual />,
    metrics: [
      { label: "Alert Latency", value: "< 2 Minutes" },
      { label: "Delivery Channels", value: "In-App + Digest" },
    ],
  },
  {
    step: 7,
    tag: "STAGE 07 · REASONING ENGINE",
    title: "AI Analyst & Mobile Intelligence",
    subtitle: "Hardware Mockup & Statutory Text RAG",
    description:
      "Natural language inquiries grounded in parliamentary bills, delivered across desktop terminal and mobile interface.",
    images: [],
    visual: <SeanceMobileShowcase />,
    metrics: [
      { label: "Citation Strictness", value: "100% Grounded" },
      { label: "Mobile Device", value: "iPhone 17 Pro" },
    ],
  },
  {
    step: 8,
    tag: "STAGE 08 · COMMAND CENTER",
    title: "Quantitative Terminal & Workspace Entry",
    subtitle: "4,700 Econometric Event-Study Predictions",
    description:
      "Your institutional environment is configured. Enter the command center to explore live legislative intelligence.",
    images: [],
    visual: <WorkspaceLaunchVisual />,
    metrics: [
      { label: "Event Predictions", value: "4,700 Records" },
      { label: "Status", value: "Production Ready" },
    ],
  },
];

// ---------------------------------------------------------------------------
// Props Interface
// ---------------------------------------------------------------------------

export interface FeatureCarouselProps {
  stages?: FeatureStage[];
  activeStep?: number; // 1-indexed (e.g. 1..8)
  onStepChange?: (step: number) => void;
  className?: string;
  autoPlay?: boolean;
  autoPlayInterval?: number;
  interactive?: boolean;
  compact?: boolean;
}

// ---------------------------------------------------------------------------
// FeatureCarousel Component
// ---------------------------------------------------------------------------

export function FeatureCarousel({
  stages = DEFAULT_FOUR_STAGES,
  activeStep,
  onStepChange,
  className,
  autoPlay = false,
  autoPlayInterval = 6000,
  interactive = true,
  compact = false,
}: FeatureCarouselProps) {
  const carouselId = useId();
  const [internalStep, setInternalStep] = useState<number>(1);
  const [direction, setDirection] = useState<"forward" | "backward">("forward");
  const [isHovered, setIsHovered] = useState<boolean>(false);

  // Controlled vs Uncontrolled step resolution
  const isControlled = typeof activeStep === "number";
  const currentStep = isControlled ? activeStep : internalStep;

  // Track previous step to derive natural direction
  const prevStepRef = useRef<number>(currentStep);

  useEffect(() => {
    if (currentStep !== prevStepRef.current) {
      setDirection(currentStep > prevStepRef.current ? "forward" : "backward");
      prevStepRef.current = currentStep;
    }
  }, [currentStep]);

  // Safe clamping to available stages
  const stageIndex = Math.max(0, Math.min(currentStep - 1, stages.length - 1));
  const activeStage = stages[stageIndex] || stages[0];

  const handleStepSelect = useCallback(
    (step: number) => {
      if (!isControlled) {
        setInternalStep(step);
      }
      onStepChange?.(step);
    },
    [isControlled, onStepChange]
  );

  // AutoPlay support for uncontrolled presentations
  useEffect(() => {
    if (!autoPlay || isControlled) return;
    const interval = setInterval(() => {
      setInternalStep((prev) => (prev % stages.length) + 1);
    }, autoPlayInterval);
    return () => clearInterval(interval);
  }, [autoPlay, autoPlayInterval, isControlled, stages.length]);

  const hasNativeVisual = Boolean(activeStage.visual);
  const hasImages = Array.isArray(activeStage.images) && activeStage.images.length > 0;
  const hasMultipleImages = (activeStage.images?.length || 0) > 1;

  return (
    <div
      id={carouselId}
      className={cn(
        "relative flex flex-col justify-between h-full w-full select-none overflow-hidden rounded-[20px]",
        "text-[#F4F4F4]",
        className
      )}
      role="region"
      aria-label="Product Showcase Carousel"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Inline styles for spring physics and direction-aware keyframe animations */}
      <style dangerouslySetInnerHTML={{ __html: `
        .fc-anim-single, .fc-anim-primary, .fc-anim-secondary {
          will-change: transform, opacity;
        }
        @keyframes fcPrimaryInForward {
          0% {
            transform: translate3d(12px, 0, 0) scale(0.99);
            opacity: 0;
          }
          100% {
            transform: translate3d(0, 0, 0) scale(1);
            opacity: 1;
          }
        }
        @keyframes fcPrimaryInBackward {
          0% {
            transform: translate3d(-12px, 0, 0) scale(0.99);
            opacity: 0;
          }
          100% {
            transform: translate3d(0, 0, 0) scale(1);
            opacity: 1;
          }
        }
        @keyframes fcSecondaryInForward {
          0% {
            transform: translate3d(18px, 0, 0) scale(0.97);
            opacity: 0;
          }
          100% {
            transform: translate3d(0, 0, 0) scale(1);
            opacity: 1;
          }
        }
        @keyframes fcSecondaryInBackward {
          0% {
            transform: translate3d(-18px, 0, 0) scale(0.97);
            opacity: 0;
          }
          100% {
            transform: translate3d(0, 0, 0) scale(1);
            opacity: 1;
          }
        }
        @media (prefers-reduced-motion: reduce) {
          .fc-anim-primary, .fc-anim-secondary, .fc-anim-single {
            animation: none !important;
            opacity: 1 !important;
            transform: none !important;
            transition: opacity 150ms ease !important;
          }
        }
      `}} />

      {/* Top Showcase Header: Tag & Stage Counter */}
      <div className="flex items-center justify-between px-5 py-2.5 sm:py-3 border-b border-white/[0.08] bg-white/[0.02] z-20 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
          <span className="text-[11px] font-mono tracking-widest uppercase font-semibold text-[#A3A3A3]">
            {activeStage.tag || `STAGE ${String(activeStage.step).padStart(2, "0")}`}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-mono text-[#A3A3A3]">
          <span className="text-[#F4F4F4] font-medium">
            {String(activeStage.step).padStart(2, "0")}
          </span>
          <span className="text-[#666666]">/</span>
          <span>{String(stages.length).padStart(2, "0")}</span>
        </div>
      </div>

      {/* Main Showcase Stage */}
      <div className="relative flex-1 min-h-0 flex items-center justify-center p-2.5 sm:p-4 overflow-hidden">
        {/* Subtle radial ambient dark charcoal glow */}
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-radial from-white/[0.03] via-transparent to-transparent pointer-events-none"
        />

        {/* Dynamic Presentation Frame */}
        <div className="relative w-full max-w-[580px] h-full flex items-center justify-center min-h-0">
          {hasNativeVisual ? (
            /* Native Animated Intelligence Composition */
            <div
              key={`native-${activeStage.step}-${direction}`}
              className={cn(
                "relative w-full h-full flex items-center justify-center fc-anim-single min-h-0",
                "motion-reduce:transform-none motion-reduce:transition-none"
              )}
              style={{
                animation: `${
                  direction === "forward" ? "fcPrimaryInForward" : "fcPrimaryInBackward"
                } 360ms cubic-bezier(0.16, 1, 0.3, 1) both`,
                zIndex: 10,
              }}
            >
              <div
                className={cn(
                  "relative w-full flex items-center justify-center",
                  activeStage.step === 7
                    ? "max-h-[460px] h-full"
                    : "aspect-[16/10] sm:aspect-[16/9.5] max-h-[440px] rounded-[18px] overflow-hidden border border-white/[0.10] bg-[#131318]/65 shadow-2xl shadow-black/80 backdrop-blur-xl",
                  "motion-reduce:transform-none motion-reduce:transition-none"
                )}
                style={{
                  transform: isHovered
                    ? "translate3d(0, -2px, 0) scale(1.008)"
                    : "translate3d(0, 0, 0)",
                  borderColor: isHovered ? "rgba(139, 92, 246, 0.45)" : "rgba(255,255,255,0.10)",
                  transition: "transform 360ms cubic-bezier(0.16, 1, 0.3, 1), border-color 250ms ease",
                }}
              >
                {activeStage.visual}
              </div>
            </div>
          ) : hasImages ? (
            /* Fallback: Multi/Single Image Support for Backward Compatibility */
            hasMultipleImages && activeStage.images ? (
              <div
                key={`multi-${activeStage.step}-${direction}`}
                className="relative w-full h-full aspect-[16/10]"
              >
                {/* Secondary Image */}
                <div
                  className="absolute right-0 bottom-0 w-[82%] h-[82%] fc-anim-secondary"
                  style={{
                    animation: `${
                      direction === "forward" ? "fcSecondaryInForward" : "fcSecondaryInBackward"
                    } 480ms cubic-bezier(0.16, 1, 0.3, 1) both`,
                    zIndex: 5,
                  }}
                >
                  <div
                    className="relative w-full h-full rounded-xl overflow-hidden border border-white/[0.08] bg-[#191919] shadow-2xl shadow-black/95"
                    style={{
                      transform: isHovered
                        ? "translate3d(5px, 6px, 0) scale(1.02) rotate(2deg)"
                        : "translate3d(0, 0, 0) rotate(1.5deg)",
                      opacity: isHovered ? 0.9 : 0.75,
                      transition: "transform 400ms cubic-bezier(0.16, 1, 0.3, 1), opacity 300ms ease-out",
                    }}
                  >
                    <Image
                      src={activeStage.images[1].src}
                      alt={activeStage.images[1].alt}
                      fill
                      sizes="(max-width: 768px) 100vw, 520px"
                      className="object-cover object-top"
                    />
                  </div>
                </div>

                {/* Primary Image */}
                <div
                  className="absolute left-0 top-0 w-[88%] h-[88%] fc-anim-primary"
                  style={{
                    animation: `${
                      direction === "forward" ? "fcPrimaryInForward" : "fcPrimaryInBackward"
                    } 400ms cubic-bezier(0.16, 1, 0.3, 1) both`,
                    zIndex: 10,
                  }}
                >
                  <div
                    className="relative w-full h-full rounded-xl overflow-hidden border border-white/[0.14] bg-[#161616] shadow-2xl shadow-black/90"
                    style={{
                      transform: isHovered ? "translate3d(-2px, -3px, 0) scale(1.01)" : "translate3d(0, 0, 0)",
                      borderColor: isHovered ? "rgba(255,255,255,0.24)" : "rgba(255,255,255,0.14)",
                      transition: "transform 400ms cubic-bezier(0.16, 1, 0.3, 1), border-color 300ms ease",
                    }}
                  >
                    <Image
                      src={activeStage.images[0].src}
                      alt={activeStage.images[0].alt}
                      fill
                      sizes="(max-width: 768px) 100vw, 560px"
                      className="object-cover object-top"
                    />
                  </div>
                </div>
              </div>
            ) : activeStage.images ? (
              <div
                key={`single-${activeStage.step}-${direction}`}
                className="relative w-full h-full aspect-[16/10] fc-anim-single"
                style={{
                  animation: `${
                    direction === "forward" ? "fcPrimaryInForward" : "fcPrimaryInBackward"
                  } 400ms cubic-bezier(0.16, 1, 0.3, 1) both`,
                  zIndex: 10,
                }}
              >
                <div className="relative w-full h-full rounded-xl overflow-hidden border border-white/[0.14] bg-[#161616] shadow-2xl shadow-black/95">
                  <Image
                    src={activeStage.images[0].src}
                    alt={activeStage.images[0].alt}
                    fill
                    sizes="(max-width: 768px) 100vw, 560px"
                    className="object-cover object-top"
                  />
                </div>
              </div>
            ) : null
          ) : null}
        </div>
      </div>

      {/* Stage Explanatory Metadata & Metrics Footer */}
      <div className="px-5 py-2.5 sm:py-3 border-t border-white/[0.08] bg-white/[0.02] z-20 flex-shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
          <div className="space-y-0.5">
            <h4 className="text-xs sm:text-sm font-semibold text-[#F4F4F4] tracking-tight">
              {activeStage.title}
            </h4>
            <p className="text-[11px] sm:text-xs text-[#A3A3A3] line-clamp-1 sm:line-clamp-2 max-w-md leading-relaxed">
              {activeStage.description}
            </p>
          </div>

          {/* Active metrics pill indicators */}
          {activeStage.metrics && activeStage.metrics.length > 0 && (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              {activeStage.metrics.map((metric, idx) => (
                <div
                  key={idx}
                  className="px-2 py-0.5 rounded-md border border-white/[0.08] bg-white/[0.03] text-[10px] font-mono text-[#A3A3A3]"
                >
                  <span className="text-[#888888]">{metric.label}: </span>
                  <span className="text-[#F4F4F4] font-semibold">{metric.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Interactive Step Dots */}
        {interactive && (
          <div
            className="flex items-center justify-center gap-1.5 pt-2 mt-2 border-t border-white/[0.06]"
            role="tablist"
            aria-label="Showcase stage selector"
          >
            {stages.map((st) => {
              const isCurrent = st.step === currentStep;
              return (
                <button
                  key={st.step}
                  type="button"
                  role="tab"
                  aria-selected={isCurrent}
                  aria-label={`Go to stage ${st.step}: ${st.title}`}
                  onClick={() => handleStepSelect(st.step)}
                  className={cn(
                    "h-1.5 rounded-full transition-all duration-300 focus:outline-none focus:ring-1 focus:ring-white/40",
                    isCurrent
                      ? "w-7 bg-white"
                      : "w-2 bg-white/20 hover:bg-white/40"
                  )}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default FeatureCarousel;
