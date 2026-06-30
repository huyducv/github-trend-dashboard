export type Repo = {
  owner: string;
  name: string;
  url: string;
  description: string | null;
  language: string | null;
  topics: string[];
  stars: number;
  forks: number;
  created_at: string | null;
  pushed_at: string | null;
  license: string | null;
  readme_excerpt: string | null;
  first_seen_at: string;
  last_seen_at: string;
  snapshot_at?: string;
  stars_delta?: number;
  forks_delta?: number;
  sectors: string[];
  source?: string;
  trend_score?: number;
};

export type Sector = {
  id: string;
  name?: string;
  count?: number;
  stars_delta?: number;
  forks_delta?: number;
  keywords?: string[];
  topics?: string[];
  languages?: string[];
};

export type DashboardPayload = {
  snapshot_at: string | null;
  repos: Repo[];
  sectors: Sector[];
  totals: {
    repositories: number;
    stars_delta: number;
    forks_delta: number;
  };
};

export type TopicPayload = {
  snapshot_at: string | null;
  topics: { name: string; count: number }[];
  sectors: Sector[];
};

export type RepoDetail = Repo & {
  history: {
    snapshot_at: string;
    stars: number;
    forks: number;
    stars_delta: number;
    forks_delta: number;
    sectors: string[];
    source: string;
    trend_score: number;
  }[];
};
