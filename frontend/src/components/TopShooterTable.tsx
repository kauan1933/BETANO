"use client";

import type { TopShooter } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function TopShooterTable() {
  const [shooters, setShooters] = useState<TopShooter[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTopShooters(20).then(setShooters).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card p-8 text-center text-gray-400">Carregando...</div>;

  return (
    <div className="card overflow-hidden">
      <div className="card-header">
        <h2 className="text-lg font-semibold text-white">Top Finalizadores</h2>
        <span className="text-sm text-gray-400">{shooters.length} jogadores</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-700 text-gray-400">
              <th className="text-left py-3 px-2">#</th>
              <th className="text-left py-3 px-2">Jogador</th>
              <th className="text-left py-3 px-2">Time</th>
              <th className="text-center py-3 px-2">Chutes/Jogo</th>
              <th className="text-center py-3 px-2">No Gol/Jogo</th>
              <th className="text-center py-3 px-2">Consist.</th>
              <th className="text-center py-3 px-2">1+ Gol</th>
            </tr>
          </thead>
          <tbody>
            {shooters.map((s, i) => (
              <tr
                key={s.player_id}
                className="border-b border-surface-700/50 hover:bg-surface-700/30 transition-colors"
              >
                <td className="py-3 px-2 text-primary-400 font-medium">{i + 1}</td>
                <td className="py-3 px-2 font-medium text-white">{s.player_name}</td>
                <td className="py-3 px-2 text-gray-400">{s.team_name}</td>
                <td className="py-3 px-2 text-center font-medium">{s.avg_total_shots.toFixed(1)}</td>
                <td className="py-3 px-2 text-center font-medium text-accent-400">
                  {s.avg_shots_on_target.toFixed(1)}
                </td>
                <td className="py-3 px-2 text-center">
                  <div className="flex items-center justify-center gap-1">
                    <div
                      className="w-16 h-1.5 bg-surface-700 rounded-full overflow-hidden"
                    >
                      <div
                        className="h-full bg-accent-500 rounded-full"
                        style={{ width: `${s.consistency_score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-400">
                      {(s.consistency_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="py-3 px-2 text-center font-medium text-primary-300">
                  {formatPercent(s.prob_1_shot_ontarget)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
