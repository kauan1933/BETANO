"use client";

import type { ValueBet } from "@/lib/api";
import { formatPercent, formatEV, formatOdds, confidenceBadge } from "@/lib/utils";
import { TrendingUp, Target } from "lucide-react";

interface ValueBetCardProps {
  bet: ValueBet;
  rank?: number;
}

export default function ValueBetCard({ bet, rank }: ValueBetCardProps) {
  return (
    <div className="card hover:border-accent-500/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {rank && (
            <span className="text-lg font-bold text-accent-400">#{rank}</span>
          )}
          <div>
            <h3 className="font-semibold text-white">{bet.player_name}</h3>
            <p className="text-sm text-gray-400">
              {bet.team_name} • {bet.league_name}
            </p>
          </div>
        </div>
        <span className={confidenceBadge(bet.confidence)}>
          {bet.confidence}
        </span>
      </div>

      <div className="flex items-center gap-2 text-sm text-gray-400 mb-3">
        <Target className="w-4 h-4" />
        <span>{bet.market}</span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-surface-700/50 rounded-lg p-2.5 text-center">
          <div className="stat-value text-lg text-accent-400">
            {formatPercent(bet.calc_probability)}
          </div>
          <div className="stat-label text-xs">Prob. Calculada</div>
        </div>
        <div className="bg-surface-700/50 rounded-lg p-2.5 text-center">
          <div className="stat-value text-lg text-yellow-400">
            {formatOdds(bet.market_odds)}
          </div>
          <div className="stat-label text-xs">Odd</div>
        </div>
        <div className="bg-surface-700/50 rounded-lg p-2.5 text-center">
          <div className="stat-value text-lg text-accent-400">
            {formatEV(bet.expected_value)}
          </div>
          <div className="stat-label text-xs">EV</div>
        </div>
      </div>
    </div>
  );
}
