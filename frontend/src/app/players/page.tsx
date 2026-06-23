"use client";

import { useEffect, useState } from "react";
import { api, type TodayPlayer } from "@/lib/api";
import Navbar from "@/components/Navbar";
import PlayerCard from "@/components/PlayerCard";
import TopShooterTable from "@/components/TopShooterTable";
import { RefreshCw } from "lucide-react";

export default function PlayersPage() {
  const [players, setPlayers] = useState<TodayPlayer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTodayPlayers().then(setPlayers).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-white mb-6">Jogadores do Dia</h1>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-white mb-4">Top Finalizadores</h2>
          <TopShooterTable />
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-4">
            Jogadores em Campo Hoje ({players.length})
          </h2>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-6 h-6 text-accent-400 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {players.map((p) => (
                <PlayerCard key={`${p.match_id}-${p.player.id}`} player={p} />
              ))}
              {players.length === 0 && (
                <div className="col-span-full text-center py-12 text-gray-400">
                  Nenhum jogador encontrado para hoje.
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
