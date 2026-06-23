"use client";

import { useEffect, useState } from "react";
import { api, type ValueBet } from "@/lib/api";
import Navbar from "@/components/Navbar";
import ValueBetCard from "@/components/ValueBetCard";
import { formatEV, formatPercent } from "@/lib/utils";
import { TrendingUp, RefreshCw, Filter } from "lucide-react";

export default function ValueBetsPage() {
  const [bets, setBets] = useState<ValueBet[]>([]);
  const [loading, setLoading] = useState(true);
  const [minEv, setMinEv] = useState(0.05);
  const [filterConfidence, setFilterConfidence] = useState<string>("all");

  useEffect(() => {
    api.getValueBets(minEv, 100).then(setBets).catch(console.error).finally(() => setLoading(false));
  }, [minEv]);

  const filtered = filterConfidence === "all"
    ? bets
    : bets.filter((b) => b.confidence === filterConfidence);

  const highCount = bets.filter((b) => b.confidence === "high").length;
  const avgEv = bets.length > 0
    ? bets.reduce((a, b) => a + b.expected_value, 0) / bets.length
    : 0;

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-accent-400" />
            Value Bets
          </h1>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="card text-center">
            <div className="stat-value text-accent-400">{bets.length}</div>
            <div className="stat-label">Total de Oportunidades</div>
          </div>
          <div className="card text-center">
            <div className="stat-value text-yellow-400">{formatEV(avgEv)}</div>
            <div className="stat-label">EV Médio</div>
          </div>
          <div className="card text-center">
            <div className="stat-value text-primary-400">{highCount}</div>
            <div className="stat-label">Alta Confiança</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-1.5 text-sm text-gray-200"
              value={filterConfidence}
              onChange={(e) => setFilterConfidence(e.target.value)}
            >
              <option value="all">Todas</option>
              <option value="high">Alta Confiança</option>
              <option value="medium">Média Confiança</option>
              <option value="low">Baixa Confiança</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">EV mínimo:</span>
            <select
              className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-1.5 text-sm text-gray-200"
              value={minEv}
              onChange={(e) => setMinEv(Number(e.target.value))}
            >
              <option value="0.05">5%</option>
              <option value="0.10">10%</option>
              <option value="0.15">15%</option>
              <option value="0.20">20%</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 text-accent-400 animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            Nenhuma value bet encontrada com os filtros atuais.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((bet, i) => (
              <ValueBetCard key={bet.id} bet={bet} rank={i + 1} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
