"use client";

import { useEffect, useState } from "react";
import { api, type TodayPlayer, type MatchData, type ValueBet } from "@/lib/api";
import Navbar from "@/components/Navbar";
import PlayerCard from "@/components/PlayerCard";
import ValueBetCard from "@/components/ValueBetCard";
import TopShooterTable from "@/components/TopShooterTable";
import { Crosshair, Target, TrendingUp, Calendar, RefreshCw } from "lucide-react";

export default function Dashboard() {
  const [players, setPlayers] = useState<TodayPlayer[]>([]);
  const [matches, setMatches] = useState<MatchData[]>([]);
  const [topBets, setTopBets] = useState<ValueBet[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getTodayPlayers(),
      api.getTodayMatches(),
      api.getValueBets(0.05, 10),
    ])
      .then(([p, m, v]) => {
        setPlayers(p);
        setMatches(m);
        setTopBets(v);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-accent-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Carregando dados do dia...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card">
            <div className="flex items-center gap-3">
              <Calendar className="w-8 h-8 text-primary-400" />
              <div>
                <div className="stat-value">{matches.length}</div>
                <div className="stat-label">Jogos Hoje</div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-accent-400" />
              <div>
                <div className="stat-value">{players.length}</div>
                <div className="stat-label">Jogadores Analisados</div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-yellow-400" />
              <div>
                <div className="stat-value">{topBets.length}</div>
                <div className="stat-label">Value Bets Hoje</div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <Crosshair className="w-8 h-8 text-red-400" />
              <div>
                <div className="stat-value">
                  {topBets.length > 0
                    ? `${(topBets.reduce((a, b) => a + b.expected_value, 0) / topBets.length * 100).toFixed(1)}%`
                    : "—"}
                </div>
                <div className="stat-label">EV Médio</div>
              </div>
            </div>
          </div>
        </div>

        {/* Top Value Bets */}
        {topBets.length > 0 && (
          <section className="mb-8">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-accent-400" />
              Melhores Oportunidades do Dia
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topBets.slice(0, 6).map((bet, i) => (
                <ValueBetCard key={bet.id} bet={bet} rank={i + 1} />
              ))}
            </div>
          </section>
        )}

        {/* Top Shooters */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Crosshair className="w-5 h-5 text-primary-400" />
            Ranking de Finalizadores
          </h2>
          <TopShooterTable />
        </section>

        {/* Today's Players */}
        {players.length > 0 && (
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-accent-400" />
              Jogadores em Ação Hoje
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {players.map((p) => (
                <PlayerCard key={`${p.match_id}-${p.player.id}`} player={p} />
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
