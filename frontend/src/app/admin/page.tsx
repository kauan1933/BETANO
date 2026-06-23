"use client";

import { useEffect, useState } from "react";
import { api, type AdminDashboard } from "@/lib/api";
import Navbar from "@/components/Navbar";
import {
  Shield,
  RefreshCw,
  Calendar,
  Users,
  TrendingUp,
  Target,
  Activity,
  Database,
} from "lucide-react";

export default function AdminPage() {
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    api.getAdminDashboard().then(setDashboard).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/admin/refresh`,
        { method: "POST" }
      );
      const updated = await api.getAdminDashboard();
      setDashboard(updated);
    } catch (e) {
      console.error(e);
    }
    setRefreshing(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-primary-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary-400" />
            Painel Administrativo
          </h1>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Atualizar Dados
          </button>
        </div>

        {dashboard && (
          <>
            {/* Platform Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="card">
                <Calendar className="w-5 h-5 text-primary-400 mb-2" />
                <div className="stat-value">{dashboard.today_matches}</div>
                <div className="stat-label">Jogos Hoje</div>
                {dashboard.live_matches > 0 && (
                  <span className="badge-green mt-1 inline-block">
                    {dashboard.live_matches} ao vivo
                  </span>
                )}
              </div>
              <div className="card">
                <Users className="w-5 h-5 text-accent-400 mb-2" />
                <div className="stat-value">{dashboard.players_with_form}</div>
                <div className="stat-label">Jogadores com Form</div>
              </div>
              <div className="card">
                <TrendingUp className="w-5 h-5 text-yellow-400 mb-2" />
                <div className="stat-value">{dashboard.active_value_bets}</div>
                <div className="stat-label">Value Bets Ativas</div>
              </div>
              <div className="card">
                <Target className="w-5 h-5 text-red-400 mb-2" />
                <div className="stat-value">
                  {(dashboard.average_ev * 100).toFixed(1)}%
                </div>
                <div className="stat-label">EV Médio</div>
              </div>
            </div>

            {/* Leagues */}
            <div className="card mb-8">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary-400" />
                  Ligas Monitoradas
                </h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {dashboard.tracked_leagues.map((league) => (
                  <span
                    key={league}
                    className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-1.5 text-sm text-gray-300"
                  >
                    {league}
                  </span>
                ))}
              </div>
            </div>

            {/* Last Refresh */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-primary-400" />
                  Última Atualização
                </h2>
              </div>
              <div className="space-y-2">
                {Object.entries(dashboard.last_refresh).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-gray-400 capitalize">{key}</span>
                    <span className="text-sm text-gray-300">
                      {new Date(val).toLocaleTimeString("pt-BR")}
                    </span>
                  </div>
                ))}
                {Object.keys(dashboard.last_refresh).length === 0 && (
                  <p className="text-gray-500 text-sm">
                    Nenhuma atualização registrada ainda.
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
