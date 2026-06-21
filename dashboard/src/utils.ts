// ---------------------------------------------------------------------------
// Shared utilities for the Engram dashboard
// ---------------------------------------------------------------------------

/**
 * Return Tailwind classes for an entity_type badge.
 */
export function entityTypeColor(entityType: string): string {
  const map: Record<string, string> = {
    // Dev artifacts
    commit:          "bg-blue-500/20 text-blue-300",
    branch:          "bg-blue-400/20 text-blue-200",
    pull_request:    "bg-purple-500/20 text-purple-300",
    code_review:     "bg-purple-400/20 text-purple-200",
    issue:           "bg-red-500/20 text-red-300",

    // Knowledge
    decision:        "bg-amber-500/20 text-amber-300",
    design_rationale:"bg-amber-400/20 text-amber-200",
    bug_report:      "bg-red-400/20 text-red-200",
    failed_attempt:  "bg-orange-500/20 text-orange-300",

    // Communication
    conversation:    "bg-teal-500/20 text-teal-300",
    message:         "bg-teal-400/20 text-teal-200",
    meeting_note:    "bg-cyan-500/20 text-cyan-300",
    slack_thread:    "bg-cyan-400/20 text-cyan-200",

    // Content
    document:        "bg-emerald-500/20 text-emerald-300",
    snippet:         "bg-emerald-400/20 text-emerald-200",

    // Measurement
    benchmark:       "bg-pink-500/20 text-pink-300",
    experiment:      "bg-pink-400/20 text-pink-200",

    // Graph entities
    person:          "bg-sky-500/20 text-sky-300",
    project:         "bg-indigo-500/20 text-indigo-300",
    component:       "bg-violet-500/20 text-violet-300",
    concept:         "bg-fuchsia-500/20 text-fuchsia-300",
  };
  return map[entityType] ?? "bg-gray-600/20 text-gray-300";
}

/**
 * Return an SVG fill color hex for a given entity_type (used in the graph).
 */
export function entityTypeNodeColor(entityType: string): string {
  const map: Record<string, string> = {
    commit:          "#3b82f6",
    branch:          "#60a5fa",
    pull_request:    "#a855f7",
    code_review:     "#c084fc",
    issue:           "#ef4444",
    decision:        "#f59e0b",
    design_rationale:"#fbbf24",
    bug_report:      "#f87171",
    failed_attempt:  "#f97316",
    conversation:    "#14b8a6",
    message:         "#2dd4bf",
    meeting_note:    "#06b6d4",
    slack_thread:    "#22d3ee",
    document:        "#10b981",
    snippet:         "#34d399",
    benchmark:       "#ec4899",
    experiment:      "#f472b6",
    person:          "#0ea5e9",
    project:         "#6366f1",
    component:       "#8b5cf6",
    concept:         "#d946ef",
  };
  return map[entityType] ?? "#6b7280";
}

/**
 * Format an ISO date string into a human-readable relative or absolute form.
 */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  const seconds = diff / 1000;
  if (seconds < 60) return "just now";
  const minutes = seconds / 60;
  if (minutes < 60) return `${Math.floor(minutes)}m ago`;
  const hours = minutes / 60;
  if (hours < 24) return `${Math.floor(hours)}h ago`;
  const days = hours / 24;
  if (days < 7) return `${Math.floor(days)}d ago`;
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: d.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
  });
}

/**
 * Truncate text to a maximum length with ellipsis.
 */
export function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max).trimEnd() + "...";
}
