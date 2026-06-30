import { Activity, BarChart3, ExternalLink, Filter, GitFork, Radar, RefreshCw, Search, ShieldCheck, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { fetchDashboard, fetchRepo, fetchSectors, fetchTopics, syncNow } from "./api";
import type { DashboardPayload, Repo, RepoDetail, Sector, TopicPayload } from "./types";

const emptyDashboard: DashboardPayload = {
  snapshot_at: null,
  repos: [],
  sectors: [],
  totals: { repositories: 0, stars_delta: 0, forks_delta: 0 }
};

function App() {
  const [dashboard, setDashboard] = useState<DashboardPayload>(emptyDashboard);
  const [topics, setTopics] = useState<TopicPayload>({ snapshot_at: null, topics: [], sectors: [] });
  const [sectorConfig, setSectorConfig] = useState<Sector[]>([]);
  const [selectedSector, setSelectedSector] = useState<string>("");
  const [selectedRepo, setSelectedRepo] = useState<RepoDetail | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sectorName = useMemo(() => {
    const map = new Map(sectorConfig.map((sector) => [sector.id, sector.name ?? sector.id]));
    map.set("unclassified", "Unclassified");
    return map;
  }, [sectorConfig]);

  const filteredRepos = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return dashboard.repos;
    return dashboard.repos.filter((repo) => {
      const haystack = `${repo.owner}/${repo.name} ${repo.description ?? ""} ${repo.language ?? ""} ${repo.topics.join(" ")}`.toLowerCase();
      return haystack.includes(term);
    });
  }, [dashboard.repos, query]);

  async function load(sector = selectedSector) {
    setError(null);
    const [dash, topicPayload, sectorPayload] = await Promise.all([fetchDashboard(sector || undefined), fetchTopics(), fetchSectors()]);
    setDashboard(dash);
    setTopics(topicPayload);
    setSectorConfig(sectorPayload.sectors);
  }

  useEffect(() => {
    load()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function selectSector(sector: string) {
    setSelectedSector(sector);
    setLoading(true);
    try {
      await load(sector);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  async function runSync() {
    setSyncing(true);
    setError(null);
    try {
      await syncNow();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  async function openRepo(repo: Repo) {
    setError(null);
    try {
      setSelectedRepo(await fetchRepo(repo.owner, repo.name));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load repository");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Developer Trend Intelligence</p>
          <h1>GitHub signal board</h1>
        </div>
        <button className="primary-button" onClick={runSync} disabled={syncing}>
          <RefreshCw size={16} className={syncing ? "spin" : ""} />
          {syncing ? "Syncing" : "Sync now"}
        </button>
      </header>

      {error && <div className="alert">{error}</div>}

      <section className="summary-grid">
        <Metric icon={<Activity size={18} />} label="Snapshot" value={dashboard.snapshot_at ? formatDateTime(dashboard.snapshot_at) : "No data"} />
        <Metric icon={<Star size={18} />} label="Stars gained" value={dashboard.totals.stars_delta.toLocaleString()} />
        <Metric icon={<GitFork size={18} />} label="Forks gained" value={dashboard.totals.forks_delta.toLocaleString()} />
        <Metric icon={<ShieldCheck size={18} />} label="Repositories" value={dashboard.totals.repositories.toLocaleString()} />
      </section>

      <section className="control-strip">
        <div className="searchbox">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search repos, topics, languages" />
        </div>
        <div className="sector-filter" aria-label="Sector filters">
          <button className={!selectedSector ? "active" : ""} onClick={() => selectSector("")}>
            <Filter size={14} />
            All sectors
          </button>
          {sectorConfig.map((sector) => (
            <button key={sector.id} className={selectedSector === sector.id ? "active" : ""} onClick={() => selectSector(sector.id)}>
              {sector.name}
            </button>
          ))}
        </div>
      </section>

      <div className="content-grid">
        <section className="report-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Today vs previous snapshot</p>
              <h2>Rising repositories</h2>
            </div>
            <span>{loading ? "Loading" : `${filteredRepos.length} visible`}</span>
          </div>
          <RepoTable repos={filteredRepos} sectorName={sectorName} onOpen={openRepo} />
        </section>

        <aside className="side-rail">
          <section className="report-panel compact">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Sector movement</p>
                <h2>Momentum</h2>
              </div>
              <BarChart3 size={18} />
            </div>
            <div className="momentum-list">
              {(dashboard.sectors.length ? dashboard.sectors : topics.sectors).slice(0, 8).map((sector) => (
                <div className="momentum-row" key={sector.id}>
                  <span>{sectorName.get(sector.id) ?? sector.id}</span>
                  <strong>+{sector.stars_delta ?? 0}</strong>
                </div>
              ))}
              {!dashboard.sectors.length && <p className="empty-copy">Run a sync to build sector movement.</p>}
            </div>
          </section>

          <section className="report-panel compact">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Topic radar</p>
                <h2>Frequent tags</h2>
              </div>
            </div>
            <div className="topic-cloud">
              {topics.topics.slice(0, 20).map((topic) => (
                <span key={topic.name}>
                  {topic.name} <b>{topic.count}</b>
                </span>
              ))}
              {!topics.topics.length && <p className="empty-copy">Topics will appear after the first sync.</p>}
            </div>
          </section>
        </aside>
      </div>

      {selectedRepo && <RepoDrawer repo={selectedRepo} sectorName={sectorName} onClose={() => setSelectedRepo(null)} />}
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="metric">
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RepoTable({ repos, sectorName, onOpen }: { repos: Repo[]; sectorName: Map<string, string>; onOpen: (repo: Repo) => void }) {
  if (!repos.length) {
    return (
      <div className="empty-state">
        <Radar size={38} />
        <h3>No trend snapshot yet</h3>
        <p>Start the backend, add an optional GitHub token, then run Sync now to collect your first local snapshot.</p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Repository</th>
            <th>Sector</th>
            <th>Language</th>
            <th>Stars</th>
            <th>Forks</th>
            <th>Source</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {repos.map((repo, index) => (
            <tr key={`${repo.owner}/${repo.name}`} onClick={() => onOpen(repo)}>
              <td className="rank">#{index + 1}</td>
              <td>
                <strong>{repo.owner}/{repo.name}</strong>
                <span>{repo.description || "No description"}</span>
              </td>
              <td>
                <div className="chips">
                  {repo.sectors.slice(0, 2).map((sector) => (
                    <span key={sector}>{sectorName.get(sector) ?? sector}</span>
                  ))}
                </div>
              </td>
              <td>{repo.language ?? "Unknown"}</td>
              <td>
                {repo.stars.toLocaleString()} <b>+{repo.stars_delta ?? 0}</b>
              </td>
              <td>
                {repo.forks.toLocaleString()} <b>+{repo.forks_delta ?? 0}</b>
              </td>
              <td><span className="source-badge">{repo.source}</span></td>
              <td>{repo.trend_score?.toFixed(1) ?? "0.0"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RepoDrawer({ repo, sectorName, onClose }: { repo: RepoDetail; sectorName: Map<string, string>; onClose: () => void }) {
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(event) => event.stopPropagation()}>
        <button className="close-button" onClick={onClose}>Close</button>
        <p className="eyebrow">Repository detail</p>
        <h2>{repo.owner}/{repo.name}</h2>
        <p className="drawer-description">{repo.description || repo.readme_excerpt || "No description available."}</p>
        <a className="github-link" href={repo.url} target="_blank" rel="noreferrer">
          Open GitHub <ExternalLink size={15} />
        </a>

        <div className="detail-grid">
          <Metric icon={<Star size={16} />} label="Stars" value={repo.stars.toLocaleString()} />
          <Metric icon={<GitFork size={16} />} label="Forks" value={repo.forks.toLocaleString()} />
        </div>

        <h3>Sectors</h3>
        <div className="chips large">
          {repo.sectors.map((sector) => (
            <span key={sector}>{sectorName.get(sector) ?? sector}</span>
          ))}
        </div>

        <h3>Snapshot history</h3>
        <div className="history-list">
          {repo.history.map((item) => (
            <div key={`${item.snapshot_at}-${item.source}`} className="history-row">
              <span>{formatDateTime(item.snapshot_at)}</span>
              <strong>+{item.stars_delta} stars</strong>
              <small>{item.source}</small>
            </div>
          ))}
        </div>

        {repo.readme_excerpt && (
          <>
            <h3>README excerpt</h3>
            <p className="readme">{repo.readme_excerpt}</p>
          </>
        )}
      </aside>
    </div>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export default App;
