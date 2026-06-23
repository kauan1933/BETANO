export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatEV(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${(value * 100).toFixed(1)}%`;
}

export function formatOdds(value: number): string {
  return value.toFixed(2);
}

export function confidenceColor(level: string): string {
  switch (level) {
    case "high":
      return "text-accent-400";
    case "medium":
      return "text-yellow-400";
    default:
      return "text-gray-400";
  }
}

export function confidenceBadge(level: string): string {
  switch (level) {
    case "high":
      return "badge-green";
    case "medium":
      return "badge badge-yellow";
    default:
      return "badge bg-gray-500/20 text-gray-400";
  }
}

export function positionLabel(pos: string | null): string {
  if (!pos) return "N/A";
  const map: Record<string, string> = {
    "Goalkeeper": "GOL",
    "Defender": "DEF",
    "Midfielder": "MEI",
    "Attacker": "ATA",
    "Forward": "ATA",
  };
  return map[pos] || pos;
}
