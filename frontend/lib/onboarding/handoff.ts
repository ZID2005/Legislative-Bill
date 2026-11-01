/**
 * lib/onboarding/handoff.ts
 * =========================
 * TASK 1.15I — ONBOARDING-TO-PLATFORM HANDOFF & PERSONALIZED FIRST-RUN EXPERIENCE.
 *
 * Canonical data structure, persistence utilities, and persona configuration for
 * seamless handoff from the 8-stage Seance onboarding journey into the authenticated
 * Command Center and workspace.
 *
 * Safeguards & Guarantees:
 * 1. Single canonical source of truth for onboarding metadata.
 * 2. Survives page reloads, browser restarts, and authenticated session switches.
 * 3. Graceful fallbacks for missing, invalid, or outdated metadata.
 * 4. Strictly preserves statutory isolation: 0 State bill stock predictions.
 * 5. Strictly preserves intelligence-only company quarantine and non-advisory boundaries.
 */

export type CanonicalPersona =
  | "INVESTOR"
  | "BUSINESS_OWNER"
  | "ANALYST_RESEARCHER"
  | "GENERAL_PUBLIC";

export interface OnboardingHandoffData {
  completed: boolean;
  completedAt?: string;
  orgName: string;
  industryFocus: string;
  teamSize: string;
  persona: string;
  canonicalPersona: CanonicalPersona;
  selectedJurisdictions: string[];
  selectedBills: string[];
  digestFrequency: string;
  inAppAlerts: boolean;
  emailAlerts: boolean;
}

export const ONBOARDING_COMPLETED_KEY = "seance_onboarding_completed";
export const ONBOARDING_DRAFT_KEY = "seance_onboarding_draft";
export const GUIDANCE_DISMISSED_KEY = "seance_first_run_guidance_dismissed";
export const HERO_COLLAPSED_KEY = "seance_persona_hero_collapsed";

export const DEFAULT_HANDOFF_DATA: OnboardingHandoffData = {
  completed: false,
  completedAt: undefined,
  orgName: "Institutional Research Workspace",
  industryFocus: "Institutional Equity Research",
  teamSize: "5-20",
  persona: "Analyst / Researcher",
  canonicalPersona: "ANALYST_RESEARCHER",
  selectedJurisdictions: ["CENTRAL", "KA", "TS"],
  selectedBills: ["bill_01_telecom_2023", "bill_02_dpdp_2023"],
  digestFrequency: "DAILY",
  inAppAlerts: true,
  emailAlerts: false,
};

/**
 * Normalize any arbitrary persona string or role identifier into one of four
 * canonical analytical archetypes.
 */
export function normalizePersona(persona?: string | null): CanonicalPersona {
  if (!persona) return "ANALYST_RESEARCHER";
  const p = persona.toUpperCase().trim();

  if (p.includes("INVESTOR") || p.includes("PORTFOLIO") || p.includes("FUND") || p.includes("CAPITAL")) {
    return "INVESTOR";
  }
  if (p.includes("BUSINESS") || p.includes("REGULATORY") || p.includes("OWNER") || p.includes("DIRECTOR") || p.includes("EXECUTIVE")) {
    return "BUSINESS_OWNER";
  }
  if (p.includes("PUBLIC") || p.includes("CITIZEN") || p.includes("COUNSEL") || p.includes("CIVIC")) {
    return "GENERAL_PUBLIC";
  }
  if (p.includes("ANALYST") || p.includes("RESEARCH") || p.includes("ECONOM") || p.includes("POLICY")) {
    return "ANALYST_RESEARCHER";
  }

  return "ANALYST_RESEARCHER";
}

export interface PersonaRecommendedAction {
  title: string;
  description: string;
  href: string;
  icon: string;
  badge: string;
  actionText: string;
}

export interface PersonaConfig {
  id: CanonicalPersona;
  displayName: string;
  categoryLabel: string;
  icon: string;
  headline: string;
  subheadline: string;
  description: string;
  statutoryNotice: string;
  recommendedActions: PersonaRecommendedAction[];
  keyFocusAreas: string[];
}

export const PERSONA_CONFIGS: Record<CanonicalPersona, PersonaConfig> = {
  INVESTOR: {
    id: "INVESTOR",
    displayName: "Investor & Portfolio Manager",
    categoryLabel: "Investor",
    icon: "💼",
    headline: "Investor Intelligence & Quantitative Exposure Desk",
    subheadline: "Tailored for Institutional Capital Allocators & Portfolio Managers",
    description:
      "Introducing corporate exposure networks, Central econometric event-study predictions, and pre-event anticipation horizons for listed Indian securities.",
    statutoryNotice:
      "Strictly probabilistic decision support. Non-financial advice only. Zero State bill stock predictions guaranteed by statutory firewall.",
    recommendedActions: [
      {
        title: "Portfolio Exposure Workspace",
        description:
          "Map your equity holdings against active Central acts and State gazettes with quantified sensitivity.",
        href: "/portfolio",
        icon: "💼",
        badge: "Priority Action",
        actionText: "Open Portfolio Exposure →",
      },
      {
        title: "Central Prediction Models",
        description:
          "Inspect cumulative abnormal return (CAR) distributions, estimation windows, and sector beta.",
        href: "/predictions",
        icon: "📈",
        badge: "Quantitative",
        actionText: "Inspect Predictions →",
      },
      {
        title: "Corporate Vulnerability Universe",
        description:
          "Analyze direct and indirect exposure linkages across 70 monitored Indian corporate entities.",
        href: "/companies",
        icon: "🏢",
        badge: "Exposure Matrix",
        actionText: "View Corporate Universe →",
      },
      {
        title: "Pre-Event Anticipation Radar",
        description:
          "Review anticipation velocity signals and pre-event public disclosures before introduction.",
        href: "/anticipation",
        icon: "📡",
        badge: "Early Signals",
        actionText: "Explore Anticipation Hub →",
      },
    ],
    keyFocusAreas: [
      "Securities return sensitivity & event study horizons",
      "Sector beta & industry regulatory exposure",
      "Central Parliament bills econometric predictions",
      "Strict statutory quarantine on unmodeled State bills",
    ],
  },

  BUSINESS_OWNER: {
    id: "BUSINESS_OWNER",
    displayName: "Business Owner & Corporate Executive",
    categoryLabel: "Business Owner",
    icon: "🏛",
    headline: "Corporate Governance & Regulatory Compliance Desk",
    subheadline: "Tailored for Business Owners, Corporate Directors & Compliance Officers",
    description:
      "Essential regulatory governance tracking primary legislation, State gazette enactments, statutory compliance obligations, and operational corporate exposures.",
    statutoryNotice:
      "Statutory tracking across Parliament and State Legislative Assemblies. Independent regulatory intelligence.",
    recommendedActions: [
      {
        title: "Legislative Monitoring Center",
        description:
          "Track bill introductions, committee scrutinies, and official gazette notifications in real-time.",
        href: "/monitoring",
        icon: "🏛",
        badge: "Compliance Radar",
        actionText: "Open Monitoring Center →",
      },
      {
        title: "Corporate Exposure Matrix",
        description:
          "Verify operating obligations, compliance timelines, and direct entity risk dossiers.",
        href: "/companies",
        icon: "🏢",
        badge: "Entity Radar",
        actionText: "Review Exposure Matrix →",
      },
      {
        title: "State Assembly Enactments",
        description:
          "Monitor state-level legislation (AP, Karnataka, Kerala, Telangana) and local statutory orders.",
        href: "/states",
        icon: "🗺",
        badge: "State Coverage",
        actionText: "Explore State Assemblies →",
      },
      {
        title: "Alert Preferences & Rules",
        description:
          "Configure high-priority notification rules and daily executive regulatory digests.",
        href: "/alerts",
        icon: "🔔",
        badge: "Notifications",
        actionText: "Configure Alert Rules →",
      },
    ],
    keyFocusAreas: [
      "Operational compliance and licensing obligations",
      "State gazette notifications & local assembly rules",
      "Supply chain and sector statutory standards",
      "Corporate risk and liability mitigation",
    ],
  },

  ANALYST_RESEARCHER: {
    id: "ANALYST_RESEARCHER",
    displayName: "Analyst & Regulatory Researcher",
    categoryLabel: "Analyst / Researcher",
    icon: "🔬",
    headline: "Legislative Dossiers & Empirical Research Workbench",
    subheadline: "Tailored for Policy Analysts, Legal Researchers & Equity Research Associates",
    description:
      "Comprehensive research environment providing complete bill dossiers, multi-source provenance, econometric prediction evidence, and comparative cross-jurisdiction analysis.",
    statutoryNotice:
      "Auditable empirical methodology with strict [OBSERVED] ⟂ [DERIVED] ⟂ [PREDICTION] epistemic firewall isolation.",
    recommendedActions: [
      {
        title: "Legislative Bill Dossiers",
        description:
          "Examine full bill texts, amendment chains, procedural journeys, and authoritative sources.",
        href: "/bills",
        icon: "📜",
        badge: "Core Research",
        actionText: "Browse Bill Dossiers →",
      },
      {
        title: "Cross-Jurisdiction Comparison",
        description:
          "Compare legislative provisions side-by-side across Central drafts and State assembly enactments.",
        href: "/bills/compare",
        icon: "⚖",
        badge: "Comparative",
        actionText: "Launch Bill Comparison →",
      },
      {
        title: "Econometric Methodology & Evidence",
        description:
          "Verify estimation windows, cumulative abnormal returns, and model calibration datasets.",
        href: "/predictions",
        icon: "📈",
        badge: "Methodology",
        actionText: "Audit Predictions →",
      },
      {
        title: "Grounded AI Research Analyst",
        description:
          "Execute structured queries against grounded legislative texts with verified provenance citations.",
        href: "/ai-analyst",
        icon: "🤖",
        badge: "Grounded AI",
        actionText: "Consult AI Analyst →",
      },
    ],
    keyFocusAreas: [
      "Full legislative text and amendment clause analysis",
      "Multi-source provenance and primary gazette verification",
      "Comparative Central and State statutory structures",
      "Econometric event-study replication and diagnostics",
    ],
  },

  GENERAL_PUBLIC: {
    id: "GENERAL_PUBLIC",
    displayName: "Public Policy & Citizen Impact Observer",
    categoryLabel: "General Public",
    icon: "⚖",
    headline: "Public Policy Observatory & Democratic Impact Desk",
    subheadline: "Tailored for Citizens, Civic Organizations & Public Policy Observers",
    description:
      "Accessible legislative intelligence providing plain-language bill explanations, stakeholder impact breakdowns, and democratic policy developments across India.",
    statutoryNotice:
      "Non-partisan public interest observatory. Objective plain-language explanations without legal jargon.",
    recommendedActions: [
      {
        title: "Plain-Language Bill Explanations",
        description:
          "Read clear, jargon-free explanations detailing how legislative changes affect everyday life.",
        href: "/bills",
        icon: "📖",
        badge: "Plain Language",
        actionText: "Read Bill Explanations →",
      },
      {
        title: "Multi-Stakeholder Impact Views",
        description:
          "Explore balanced perspectives across consumers, workers, farmers, and industry sectors.",
        href: "/overview",
        icon: "👥",
        badge: "Civic Impact",
        actionText: "View Stakeholder Views →",
      },
      {
        title: "State Assembly Legislation",
        description:
          "Browse enactments and gazettes across Karnataka, Telangana, Andhra Pradesh, and Kerala.",
        href: "/states",
        icon: "🗺",
        badge: "Local Assemblies",
        actionText: "Explore Your State →",
      },
      {
        title: "Live Legislative Intake",
        description:
          "Follow new measures in real time as they are introduced in Parliament and state assemblies.",
        href: "/live-discovery",
        icon: "📡",
        badge: "Live Intake",
        actionText: "View Live Intake →",
      },
    ],
    keyFocusAreas: [
      "Plain-language bill summaries and practical implications",
      "Consumer and citizen rights protections",
      "State assembly gazettes and local governance",
      "Open democratic legislative tracking",
    ],
  },
};

/**
 * Retrieve the active onboarding handoff data.
 * Gracefully parses stored metadata from localStorage or returns a clean fallback.
 */
export function getOnboardingHandoff(): OnboardingHandoffData {
  if (typeof window === "undefined") {
    return DEFAULT_HANDOFF_DATA;
  }

  try {
    const raw = localStorage.getItem(ONBOARDING_COMPLETED_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        const persona = parsed.persona || DEFAULT_HANDOFF_DATA.persona;
        return {
          completed: Boolean(parsed.completed ?? true),
          completedAt: parsed.completedAt,
          orgName: parsed.orgName || DEFAULT_HANDOFF_DATA.orgName,
          industryFocus: parsed.industryFocus || DEFAULT_HANDOFF_DATA.industryFocus,
          teamSize: parsed.teamSize || DEFAULT_HANDOFF_DATA.teamSize,
          persona,
          canonicalPersona: normalizePersona(persona),
          selectedJurisdictions: Array.isArray(parsed.selectedJurisdictions) && parsed.selectedJurisdictions.length > 0
            ? parsed.selectedJurisdictions
            : DEFAULT_HANDOFF_DATA.selectedJurisdictions,
          selectedBills: Array.isArray(parsed.selectedBills)
            ? parsed.selectedBills
            : DEFAULT_HANDOFF_DATA.selectedBills,
          digestFrequency: parsed.digestFrequency || DEFAULT_HANDOFF_DATA.digestFrequency,
          inAppAlerts: parsed.inAppAlerts !== undefined ? Boolean(parsed.inAppAlerts) : true,
          emailAlerts: parsed.emailAlerts !== undefined ? Boolean(parsed.emailAlerts) : false,
        };
      }
    }

    // Also inspect draft if completed is missing
    const draftRaw = localStorage.getItem(ONBOARDING_DRAFT_KEY);
    if (draftRaw) {
      const draft = JSON.parse(draftRaw);
      if (draft && typeof draft === "object" && draft.orgName) {
        const persona = draft.persona || DEFAULT_HANDOFF_DATA.persona;
        return {
          completed: false,
          completedAt: undefined,
          orgName: draft.orgName || DEFAULT_HANDOFF_DATA.orgName,
          industryFocus: draft.industryFocus || DEFAULT_HANDOFF_DATA.industryFocus,
          teamSize: draft.teamSize || DEFAULT_HANDOFF_DATA.teamSize,
          persona,
          canonicalPersona: normalizePersona(persona),
          selectedJurisdictions: Array.isArray(draft.selectedJurisdictions) && draft.selectedJurisdictions.length > 0
            ? draft.selectedJurisdictions
            : DEFAULT_HANDOFF_DATA.selectedJurisdictions,
          selectedBills: Array.isArray(draft.selectedBills) ? draft.selectedBills : DEFAULT_HANDOFF_DATA.selectedBills,
          digestFrequency: draft.digestFrequency || DEFAULT_HANDOFF_DATA.digestFrequency,
          inAppAlerts: draft.inAppAlerts !== undefined ? Boolean(draft.inAppAlerts) : true,
          emailAlerts: draft.emailAlerts !== undefined ? Boolean(draft.emailAlerts) : false,
        };
      }
    }
  } catch {
    // Return default on parse failure
  }

  return DEFAULT_HANDOFF_DATA;
}

/**
 * Persist updated handoff data to localStorage.
 */
export function saveOnboardingHandoff(data: Partial<OnboardingHandoffData>): OnboardingHandoffData {
  const current = getOnboardingHandoff();
  const persona = data.persona || current.persona;
  const updated: OnboardingHandoffData = {
    ...current,
    ...data,
    persona,
    canonicalPersona: normalizePersona(persona),
  };

  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(ONBOARDING_COMPLETED_KEY, JSON.stringify(updated));
    } catch {
      // Ignore write errors in restricted sandboxes
    }
  }

  return updated;
}

/**
 * Check if the first-run guidance tour has been dismissed.
 */
export function isGuidanceDismissed(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return localStorage.getItem(GUIDANCE_DISMISSED_KEY) === "true";
  } catch {
    return false;
  }
}

/**
 * Set the first-run guidance dismissal state.
 */
export function setGuidanceDismissed(dismissed: boolean): void {
  if (typeof window === "undefined") return;
  try {
    if (dismissed) {
      localStorage.setItem(GUIDANCE_DISMISSED_KEY, "true");
    } else {
      localStorage.removeItem(GUIDANCE_DISMISSED_KEY);
    }
  } catch {
    // Ignore write errors
  }
}

/**
 * Check if the personalized hero card has been minimized by the user.
 */
export function isHeroCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(HERO_COLLAPSED_KEY) === "true";
  } catch {
    return false;
  }
}

/**
 * Set the personalized hero card collapse state.
 */
export function setHeroCollapsed(collapsed: boolean): void {
  if (typeof window === "undefined") return;
  try {
    if (collapsed) {
      localStorage.setItem(HERO_COLLAPSED_KEY, "true");
    } else {
      localStorage.removeItem(HERO_COLLAPSED_KEY);
    }
  } catch {
    // Ignore write errors
  }
}

/**
 * Reset first-run guidance to visible (for re-opening or testing).
 */
export function resetFirstRunExperience(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(GUIDANCE_DISMISSED_KEY);
    localStorage.removeItem(HERO_COLLAPSED_KEY);
  } catch {
    // Ignore
  }
}

/**
 * Get configuration object for a given persona.
 */
export function getPersonaConfig(persona?: string | null): PersonaConfig {
  const canonical = normalizePersona(persona);
  return PERSONA_CONFIGS[canonical];
}

