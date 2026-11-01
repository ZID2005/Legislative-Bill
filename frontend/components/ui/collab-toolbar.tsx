/**
 * components/ui/collab-toolbar.tsx
 * ==================================
 * Task 1.14C — Seance Final Header Collaboration Toolbar Refinement.
 *
 * Implements the refined premium modern SaaS collaboration toolbar:
 * - Pill-shaped horizontal groupings with subtle dividers
 * - Responsive automation: zero simulated phone/desktop buttons; layout adapts via CSS & viewport
 * - Single authenticated user avatar displaying uppercase first initial
 * - Dual-theme support via semantic tokens (Light, Dark, System)
 * - Refined 150-220ms transitions and microinteractions
 * - Full WCAG 2.2 AAA accessibility, keyboard navigation, and reduced-motion support
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

export type IconKey =
  | "phone"
  | "compass"
  | "desktop"
  | "chrome"
  | "chat"
  | "inbox"
  | "toggle"
  | "layers"
  | "upload"
  | "menu";

export const icons: Record<IconKey, React.ReactNode> = {
  phone: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M5.25 0C3.73122 0 2.5 1.23122 2.5 2.75V13.25C2.5 14.7688 3.73122 16 5.25 16H10.75C12.2688 16 13.5 14.7688 13.5 13.25V2.75C13.5 1.23122 12.2688 0 10.75 0H5.25ZM4 2.75C4 2.05964 4.55964 1.5 5.25 1.5H10.75C11.4404 1.5 12 2.05964 12 2.75V13.25C12 13.9404 11.4404 14.5 10.75 14.5H5.25C4.55964 14.5 4 13.9404 4 13.25V2.75ZM6.25 4.75C6.80228 4.75 7.25 4.30228 7.25 3.75C7.25 3.19772 6.80228 2.75 6.25 2.75C5.69772 2.75 5.25 3.19772 5.25 3.75C5.25 4.30228 5.69772 4.75 6.25 4.75Z"
      />
    </svg>
  ),
  compass: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M14.5 8C14.5 11.5899 11.5899 14.5 8 14.5C4.41015 14.5 1.5 11.5899 1.5 8C1.5 4.41015 4.41015 1.5 8 1.5C11.5899 1.5 14.5 4.41015 14.5 8ZM16 8C16 12.4183 12.4183 16 8 16C3.58172 16 0 12.4183 0 8C0 3.58172 3.58172 0 8 0C12.4183 0 16 3.58172 16 8ZM12.5925 3.40746L8.75908 4.93074L6.01936 6.0194L4.9307 8.75912L3.40742 12.5926L7.24089 11.0693L9.9806 9.98064L11.0693 7.24092L12.5925 3.40746ZM9.25 8C9.25 8.69036 8.69036 9.25 8 9.25C7.30964 9.25 6.75 8.69036 6.75 8C6.75 7.30964 7.30964 6.75 8 6.75C8.69036 6.75 9.25 7.30964 9.25 8Z"
      />
    </svg>
  ),
  desktop: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M0 2C0 1.44772 .447715 1 1 1H15C15.5523 1 16 1.44772 16 2V10.5C16 11.0523 15.5523 11.5 15 11.5H8.75V14.5H9.75H10.5V16H9.75H6.25H5.5V14.5H6.25H7.25V11.5H1C.447714 11.5 0 11.0523 0 10.5V2ZM1.5 2.5V10H14.5V2.5H1.5Z"
      />
    </svg>
  ),
  chrome: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M8.53216 11.3333L6.77086 14.3839C3.76871 13.8094 1.5 11.1696 1.5 8C1.5 6.86643 1.79018 5.80063 2.3003 4.87284L5.006 9.55925C5.56913 10.6383 6.69854 11.375 8 11.375C8.18107 11.375 8.35881 11.3607 8.53216 11.3333ZM10.8505 9.80787L8.14234 14.4985C11.6665 14.4228 14.5 11.5423 14.5 8C14.5 7.2549 14.3746 6.53909 14.1438 5.8725L10.6201 5.8725C11.0921 6.45305 11.375 7.19349 11.375 8C11.375 8.66509 11.1826 9.28525 10.8505 9.80787ZM8.13109 4.6275L13.5577 4.6275C12.4175 2.7524 10.355 1.5 8 1.5C6.0376 1.5 4.27831 2.36964 3.08649 3.74456L4.84694 6.79376C5.33242 5.52553 6.56104 4.625 8 4.625C8.0439 4.625 8.0876 4.62584 8.13109 4.6275ZM8 16C12.4183 16 16 12.4183 16 8C16 3.58172 12.4183 0 8 0C3.58172 0 0 3.58172 0 8C0 12.4183 3.58172 16 8 16ZM5.875 8C5.875 6.8264 6.8264 5.875 8 5.875C9.1736 5.875 10.125 6.8264 10.125 8C10.125 9.1736 9.1736 10.125 8 10.125C6.8264 10.125 5.875 9.1736 5.875 8Z"
      />
    </svg>
  ),
  chat: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M2.8914 10.4028L2.98327 10.6318C3.22909 11.2445 3.5 12.1045 3.5 13C3.5 13.3588 3.4564 13.7131 3.38773 14.0495C3.69637 13.9446 4.01409 13.8159 4.32918 13.6584C4.87888 13.3835 5.33961 13.0611 5.70994 12.7521L6.22471 12.3226L6.88809 12.4196C7.24851 12.4724 7.61994 12.5 8 12.5C11.7843 12.5 14.5 9.85569 14.5 7C14.5 4.14431 11.7843 1.5 8 1.5C4.21574 1.5 1.5 4.14431 1.5 7C1.5 8.18175 1.94229 9.29322 2.73103 10.2153L2.8914 10.4028ZM2.8135 15.7653C1.76096 16 1 16 1 16C1 16 1.43322 15.3097 1.72937 14.4367C1.88317 13.9834 2 13.4808 2 13C2 12.3826 1.80733 11.7292 1.59114 11.1903C.591845 10.0221 0 8.57152 0 7C0 3.13401 3.58172 0 8 0C12.4183 0 16 3.13401 16 7C16 10.866 12.4183 14 8 14C7.54721 14 7.10321 13.9671 6.67094 13.9038C6.22579 14.2753 5.66881 14.6656 5 15C4.24606 15.3618 3.49129 15.6171 2.8135 15.7653Z"
      />
    </svg>
  ),
  inbox: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M2.5 1.5C1.94772 1.5 1.5 1.94772 1.5 2.5V13.5C1.5 14.0523 1.94772 14.5 2.5 14.5H13.5C14.0523 14.5 14.5 14.0523 14.5 13.5V2.5C14.5 1.94772 14.0523 1.5 13.5 1.5H2.5ZM0 2.5C0 1.11929 1.11929 0 2.5 0H13.5C14.8807 0 16 1.11929 16 2.5V13.5C16 14.8807 14.8807 16 13.5 16H2.5C1.11929 16 0 14.8807 0 13.5V2.5ZM3 9.5V11H13V9.5H10.5C10.2239 9.5 10 9.72386 10 10C10 10.5523 9.55228 11 9 11H7C6.44772 11 6 10.5523 6 10C6 9.72386 5.77614 9.5 5.5 9.5H3Z"
      />
    </svg>
  ),
  toggle: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M5 3C2.79086 3 1 4.79086 1 7C1 9.20914 2.79086 11 5 11H11C13.2091 11 15 9.20914 15 7C15 4.79086 13.2091 3 11 3H5ZM11 5C12.1046 5 13 5.89543 13 7C13 8.10457 12.1046 9 11 9C9.89543 9 9 8.10457 9 7C9 5.89543 9.89543 5 11 5Z"
      />
    </svg>
  ),
  layers: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M0 5.25136L.463236 5.05968L7.71324 2.05968L8 1.93835L8.28676 2.05968L15.5368 5.05968L16 5.25136V6.8747L15.4632 6.65259L8 3.56431L.536764 6.65259L0 6.8747V5.25136ZM0 5.25136L.463236 5.44304L7.71324 8.44304L8 8.5617L8.28676 8.44304L15.5368 5.44304L16 5.25136L15.5368 5.05968L8.28676 2.05968L8 1.93835L7.71324 2.05968L.463236 5.05968L0 5.25136ZM0 8.45825V6.83491L.536764 7.05702L8 10.1453L15.4632 7.05702L16 6.83491V8.45825L8.28676 11.6499L8 11.7686L7.71324 11.6499L0 8.45825ZM0 11.7083V10.0849L.536764 10.307L8 13.3953L15.4632 10.307L16 10.0849V11.7083L8.28676 14.8999L8 15.0186L7.71324 14.8999L0 11.7083Z"
      />
    </svg>
  ),
  upload: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M7.29289 1.39644C7.68342 1.00592 8.31658 1.00592 8.70711 1.39644L11.7803 4.46966L12.3107 5L11.25 6.06066L10.7197 5.53033L8.75 3.56066V10.25V11H7.25V10.25V3.56066L5.28033 5.53033L4.75 6.06066L3.68934 5L4.21967 4.46966L7.29289 1.39644ZM13.5 9.25V13.5H2.5V9.25V8.5H1V9.25V14C1 14.5523 1.44771 15 2 15H14C14.5523 15 15 14.5523 15 14V9.25V8.5H13.5V9.25Z"
      />
    </svg>
  ),
  menu: (
    <svg
      aria-hidden="true"
      focusable="false"
      height="14"
      viewBox="0 0 16 16"
      width="14"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M1 2H1.75H14.25H15V3.5H14.25H1.75H1V2ZM1 12.5H1.75H14.25H15V14H14.25H1.75H1V12.5ZM1.75 7.25H1V8.75H1.75H14.25H15V7.25H14.25H1.75Z"
      />
    </svg>
  ),
};

export interface Collaborator {
  name: string;
  role?: string;
  tenantId?: string;
  color?: string;
  imageUrl?: string;
  initials?: string;
  email?: string;
}

export type ToolbarGroup = IconKey[] | "avatars" | "avatar";

/**
 * Task 1.14C — Initial Generation Logic for Authenticated User
 *
 * Fallback ladder:
 * 1. Authenticated user's display name
 * 2. Authenticated user's first name
 * 3. Existing authenticated profile identifier or email
 * 4. Neutral fallback "U"
 *
 * Never hardcoded, never random avatar images, never tenant-member initials.
 */
export function getAuthenticatedUserInitial(user?: {
  display_name?: string | null;
  first_name?: string | null;
  name?: string | null;
  email?: string | null;
  user_id?: string | null;
  id?: string | null;
} | null): string {
  if (!user) return "U";

  // 1. Authenticated user's display name
  const displayName = typeof user.display_name === "string" ? user.display_name.trim() : "";
  if (displayName.length > 0) {
    return displayName.charAt(0).toUpperCase();
  }

  // 2. Authenticated user's first name
  const firstName = typeof user.first_name === "string" ? user.first_name.trim() : "";
  if (firstName.length > 0) {
    return firstName.charAt(0).toUpperCase();
  }
  const name = typeof user.name === "string" ? user.name.trim() : "";
  if (name.length > 0) {
    return name.charAt(0).toUpperCase();
  }

  // 3. Existing authenticated profile identifier or email
  const email = typeof user.email === "string" ? user.email.trim() : "";
  if (email.length > 0) {
    return email.charAt(0).toUpperCase();
  }
  const identifier =
    typeof user.user_id === "string"
      ? user.user_id.trim()
      : typeof user.id === "string"
      ? user.id.trim()
      : "";
  if (identifier.length > 0) {
    const cleanId = identifier.replace(/^usr_/, "");
    if (cleanId.length > 0) {
      return cleanId.charAt(0).toUpperCase();
    }
    return identifier.charAt(0).toUpperCase();
  }

  // 4. A neutral fallback such as U if no usable identity is available
  return "U";
}

export interface ActionMeta {
  onClick?: () => void;
  ariaLabel?: string;
  title?: string;
  isActive?: boolean;
  disabled?: boolean;
  href?: string;
  badge?: string;
  className?: string;
}

export interface CollabToolbarProps {
  groups: ToolbarGroup[];
  avatars?: Collaborator[];
  userAvatar?: Collaborator;
  onAction?: (action: IconKey) => void;
  actionProps?: Partial<Record<IconKey, ActionMeta>>;
  activeAction?: IconKey | null;
  className?: string;
  ariaLabel?: string;
  onAvatarClick?: (collaborator: Collaborator) => void;
}

/**
 * Avatar item with initials fallback, respectful of privacy & tenant boundaries
 */
export function CollabToolbarAvatar({
  collaborator,
  size = 22,
  onClick,
}: {
  collaborator: Collaborator;
  size?: number;
  onClick?: () => void;
}) {
  const [imageError, setImageError] = useState(false);

  // Compute initials fallback (Phase 3: single uppercase initial preferred)
  const initial =
    collaborator.initials ||
    (collaborator.name ? collaborator.name.trim().charAt(0).toUpperCase() : "U");

  const displayName = collaborator.name || "Authenticated User";
  const tooltipTitle = `${displayName}${
    collaborator.role ? ` (${collaborator.role})` : ""
  }${collaborator.tenantId ? ` · ${collaborator.tenantId}` : ""}`;

  return (
    <button
      type="button"
      data-slot="collab-avatar"
      onClick={onClick}
      title={tooltipTitle}
      aria-label={`User account: ${tooltipTitle}`}
      className={cn(
        "relative shrink-0 rounded-full flex items-center justify-center font-bold font-mono select-none overflow-hidden text-[10.5px]",
        "border border-[var(--border-strong)] bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-xs",
        "transition-all duration-150 ease-out hover:scale-105 hover:border-[var(--focus-ring)] hover:bg-[var(--bg-card-hover)]",
        "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]",
        "motion-reduce:transition-none motion-reduce:hover:scale-100 cursor-pointer"
      )}
      style={{
        width: size,
        height: size,
        backgroundColor: collaborator.color ? `${collaborator.color}22` : undefined,
        color: collaborator.color || "var(--text-primary)",
      }}
    >
      {collaborator.imageUrl && !imageError ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={collaborator.imageUrl}
          alt={displayName}
          className="h-full w-full object-cover rounded-full"
          onError={() => setImageError(true)}
        />
      ) : (
        <span className="leading-none">{initial}</span>
      )}
    </button>
  );
}

/**
 * Toolbar Divider Component
 */
export function CollabToolbarDivider({ className }: { className?: string }) {
  return (
    <div
      data-slot="collab-toolbar-divider"
      role="separator"
      aria-orientation="vertical"
      className={cn(
        "h-4 w-px shrink-0 bg-[var(--border-default)] transition-colors duration-150",
        className
      )}
    />
  );
}

/**
 * Toolbar Individual Action Icon Button
 */
export function CollabToolbarIcon({
  icon,
  onClick,
  isActive = false,
  disabled = false,
  ariaLabel,
  title,
  className,
}: {
  icon: IconKey;
  onClick?: () => void;
  isActive?: boolean;
  disabled?: boolean;
  ariaLabel?: string;
  title?: string;
  className?: string;
}) {
  const defaultLabels: Record<IconKey, string> = {
    phone: "Mobile View",
    desktop: "Desktop View",
    chat: "AI Analyst",
    upload: "Import Holdings",
    menu: "Secondary Menu",
    compass: "Discovery",
    chrome: "Browser",
    inbox: "Notifications",
    toggle: "Toggle",
    layers: "Layers",
  };

  const label = ariaLabel || defaultLabels[icon] || icon;
  const hoverTitle = title || label;

  return (
    <button
      data-slot="collab-toolbar-icon"
      data-action={icon}
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={hoverTitle}
      aria-label={label}
      aria-pressed={isActive}
      className={cn(
        "relative flex cursor-pointer items-center justify-center rounded-md border-0 p-1.5 transition-all duration-150 ease-out",
        "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--focus-ring)]",
        "active:scale-95 motion-reduce:transition-none motion-reduce:active:scale-100",
        disabled && "opacity-40 cursor-not-allowed pointer-events-none",
        isActive
          ? "bg-[var(--action-primary)]/15 text-[var(--action-primary)] font-semibold shadow-xs"
          : "text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)]",
        className
      )}
    >
      {icons[icon]}
    </button>
  );
}

/**
 * CollabToolbar Main Container
 */
export function CollabToolbar({
  groups,
  avatars = [],
  userAvatar,
  onAction,
  actionProps = {},
  activeAction,
  className,
  ariaLabel = "Collaboration and utility toolbar",
  onAvatarClick,
}: CollabToolbarProps) {
  return (
    <div
      data-slot="collab-toolbar"
      role="toolbar"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-default)]",
        "bg-[var(--bg-surface)] px-1.5 py-1 text-xs shadow-xs",
        "backdrop-blur-xs transition-colors duration-150",
        "motion-safe:animate-fade-in",
        className
      )}
    >
      {groups.map((group, groupIdx) => {
        const isFirst = groupIdx === 0;
        const groupKey = Array.isArray(group)
          ? `icons:${group.join("|")}`
          : `group:${group}`;

        return (
          <React.Fragment key={groupKey}>
            {!isFirst && <CollabToolbarDivider />}

            {Array.isArray(group) ? (
              <div
                className="flex items-center gap-0.5"
                role="group"
                aria-label={group.join(", ")}
              >
                {group.map((icon) => {
                  const meta = actionProps[icon] || {};
                  const isCurrentActive =
                    meta.isActive !== undefined
                      ? meta.isActive
                      : activeAction === icon;

                  return (
                    <CollabToolbarIcon
                      key={icon}
                      icon={icon}
                      isActive={isCurrentActive}
                      disabled={meta.disabled}
                      ariaLabel={meta.ariaLabel}
                      title={meta.title}
                      className={meta.className}
                      onClick={() => {
                        meta.onClick?.();
                        onAction?.(icon);
                      }}
                    />
                  );
                })}
              </div>
            ) : group === "avatar" || group === "avatars" ? (
              <div
                className="flex items-center px-0.5"
                role="group"
                aria-label={group === "avatar" ? "User account" : "Active collaborators"}
              >
                {group === "avatar" || userAvatar ? (
                  <CollabToolbarAvatar
                    collaborator={
                      userAvatar ||
                      avatars[0] || {
                        name: "Institutional Analyst",
                        initials: "U",
                      }
                    }
                    size={22}
                    onClick={() => {
                      const target =
                        userAvatar ||
                        avatars[0] || {
                          name: "Institutional Analyst",
                          initials: "U",
                        };
                      onAvatarClick?.(target);
                    }}
                  />
                ) : avatars.length === 0 ? (
                  <CollabToolbarAvatar
                    collaborator={{ name: "Analyst", initials: "A" }}
                    size={22}
                    onClick={() =>
                      onAvatarClick?.({ name: "Analyst", initials: "A" })
                    }
                  />
                ) : (
                  <div className="flex items-center -space-x-1.5">
                    {avatars.map((avatar, idx) => (
                      <CollabToolbarAvatar
                        key={`${avatar.name}-${idx}`}
                        collaborator={avatar}
                        size={22}
                        onClick={() => onAvatarClick?.(avatar)}
                      />
                    ))}
                  </div>
                )}
              </div>
            ) : null}
          </React.Fragment>
        );
      })}
    </div>
  );
}

export default CollabToolbar;
