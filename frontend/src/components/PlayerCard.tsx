"use client";

import type { TodayPlayer } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { Swords, Target, Activity } from "lucide-react";

interface PlayerCardProps {
  player: TodayPlayer;
  rank?: number;
}

export default function PlayerCard({ player, rank }: PlayerCardProps) {
  const p = player.player;
  const form = p.form;

  return (
    <div className="card hover:border-primary-500/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {rank && (
            <span className="text-2xl font-bold text-primary-400">
              #{rank}
            </span>
          )}
          <div>
            <h3 className="font-semibold text-white">{p.name}</h3>
            <p className="text-sm text-gray-400">
              {p.team_name} • {player.league}
            </p>
          </div>
        </div>
        <span className="badge-blue">{p.position || "N/A"}</span>
      </div>

      {form && (
        <div className="grid grid-cols-3 gap-3 mt-3">
          <div className="bg-surface-700/50 rounded-lg p-2.5 text-center">
            <Target className="w-4 h-4 text-accent-400 mx-auto mb-1" />
            <div className="stat-value text-sm">{form.avg_shots_on_target.toFixed(1)}</div>
            <div className="stat-label text-xs">Chutes no Gol (média)</div>
          </div>
          <div className="bg-surface-700/50 rounded-lg p-2.5 text-center">
            <Swords className="w-4 h-4 text-primary-400 mx-auto mb-1" />
            <div className="stat-value text-sm">{form.avg_total_shots.toFixed(1)}</div>
            <div className="stat-label text-xs">Total Chutes (média)</div>
          </div>
          <div className="bg-surface-700/50 rounded-lg p-2.5 text-center">
            <Activity className="w-4 h-4 text-yellow-400 mx-auto mb-1" />
            <div className="stat-value text-sm">
              {(form.consistency_score * 100).toFixed(0)}%
            </div>
            <div className="stat-label text-xs">Consistência</div>
          </div>
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-surface-700">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">1+ chute no gol:</span>
          <span className="font-medium text-accent-400">
            {formatPercent(player.prob_1_shot_ot)}
          </span>
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="text-gray-400">2+ chutes no gol:</span>
          <span className="font-medium text-primary-300">
            {formatPercent(player.prob_2_plus_shot_ot)}
          </span>
        </div>
      </div>
    </div>
  );
}
