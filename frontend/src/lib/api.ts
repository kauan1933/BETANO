const API_BASE = "https://betano-7.onrender.com";

async function fetchJSON<T>(endpoint: string): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      signal: controller.signal,
      cache: "no-cache",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export interface PlayerFormData {
  avg_total_shots: number;
  avg_shots_on_target: number;
  consistency_score: number;
  games_analyzed: number;
}

export interface TodayPlayer {
  match_id: number;
  match: string;
  league: string;
  match_date: string;
  player: {
    id: number;
    name: string;
    team_name: string;
    position: string | null;
    photo_url: string | null;
    form: PlayerFormData | null;
  };
  prob_1_shot_ot: number;
  prob_2_plus_shot_ot: number;
  prob_x_total_shots: Record<string, number>;
}

export interface TopShooter {
  player_id: number;
  player_name: string;
  team_name: string;
  league_name: string;
  position: string | null;
  avg_total_shots: number;
  avg_shots_on_target: number;
  consistency_score: number;
  prob_1_shot_ontarget: number;
  prob_2_plus_shots_ontarget: number;
}

export interface ValueBet {
  id: number;
  match: string;
  player_name: string;
  team_name: string;
  league_name: string;
  market: string;
  calc_probability: number;
  market_odds: number;
  implied_probability: number;
  expected_value: number;
  confidence: string;
  created_at: string;
}

export interface MatchData {
  id: number;
  league_name: string;
  home_team: string;
  away_team: string;
  match_date: string;
  status: string;
  home_score: number | null;
  away_score: number | null;
}

export interface AdminDashboard {
  today_matches: number;
  live_matches: number;
  total_players: number;
  players_with_form: number;
  active_value_bets: number;
  average_ev: number;
  last_refresh: Record<string, string>;
  tracked_leagues: string[];
}

export const api = {
  getTodayPlayers: () => fetchJSON<TodayPlayer[]>("/api/v1/players/today"),
  getTopShooters: (limit = 20) =>
    fetchJSON<TopShooter[]>(`/api/v1/players/top-shooters?limit=${limit}`),
  getPlayerDetail: (id: number) => fetchJSON<any>(`/api/v1/players/${id}`),
  getTodayMatches: () => fetchJSON<MatchData[]>("/api/v1/matches/today"),
  getMatchDetail: (id: number) => fetchJSON<any>(`/api/v1/matches/${id}`),
  getValueBets: (minEv = 0.05, limit = 50) =>
    fetchJSON<ValueBet[]>(
      `/api/v1/value-bets/shots?min_ev=${minEv}&limit=${limit}`
    ),
  getValueBetStats: () => fetchJSON<any>("/api/v1/value-bets/stats"),
  getAdminDashboard: () => fetchJSON<AdminDashboard>("/api/v1/admin/dashboard"),
};
