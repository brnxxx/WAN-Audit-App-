import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiDownload, apiGet, API_BASE, UnauthorizedError } from "../api/client";
import type { GNS3Project, InfrastructureLog } from "../api/types";

export default function InfrastructureLogsPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<GNS3Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [logs, setLogs] = useState<InfrastructureLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);

  const handleError = useCallback((err: unknown) => {
    if (err instanceof UnauthorizedError) {
      navigate("/login");
      return;
    }
    setError(err instanceof Error ? err.message : "Impossible de charger le journal.");
  }, [navigate]);

  const loadLogs = useCallback(async (selectedId: string) => {
    if (!selectedId) {
      setLogs([]);
      return;
    }
    try {
      setError(null);
      setLogs(await apiGet<InfrastructureLog[]>(`/gns3/projects/${selectedId}/logs?limit=500`));
    } catch (err) {
      handleError(err);
    }
  }, [handleError]);

  async function exportLogs(format: "csv" | "pdf") {
    if (!projectId) return;
    try {
      setExporting(format);
      setError(null);
      await apiDownload(
        `/gns3/projects/${encodeURIComponent(projectId)}/logs.${format}`,
        `infrastructure-${projectId}-logs.${format}`,
      );
    } catch (err) {
      handleError(err);
    } finally {
      setExporting(null);
    }
  }

  useEffect(() => {
    void apiGet<GNS3Project[]>("/gns3/projects")
      .then((items) => {
        setProjects(items);
        setProjectId(items[0]?.project_id || "");
      })
      .catch(handleError);
  }, [handleError]);

  useEffect(() => {
    void Promise.resolve().then(() => loadLogs(projectId));
  }, [loadLogs, projectId]);

  async function logout() {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    navigate("/login");
  }

  return (
    <>
      <div className="topbar">
        <div className="brand"><span className="brand-dot" /> WAN Audit</div>
        <nav className="topnav">
          <Link to="/infrastructure" className="topnav-link">Infrastructure</Link>
          <Link to="/equipements" className="topnav-link">Équipements</Link>
          <Link to="/gns3-operations" className="topnav-link">GNS3 Ops</Link>
          <Link to="/infrastructure-logs" className="topnav-link active">Logs</Link>
          <Link to="/sites-backbone" className="topnav-link">Sites & Backbone</Link>
        </nav>
        <button className="logout-btn" onClick={logout}>Se déconnecter</button>
      </div>
      <main className="content">
        <div className="page-heading">
          <div>
            <div className="eyebrow">AUDIT / INFRASTRUCTURE HISTORY</div>
            <h1>Journal d'infrastructure</h1>
            <p className="subtitle">Chaque projet possède son propre historique de connectivité, diagnostics et erreurs.</p>
          </div>
          <div className="live-indicator"><span className="pulse-dot" /> JOURNAL ISOLÉ</div>
        </div>
        <div className="control-bar">
          <label htmlFor="logs-project">Infrastructure</label>
          <select id="logs-project" value={projectId} onChange={(event) => setProjectId(event.target.value)} disabled={!projects.length}>
            {projects.length === 0 && <option value="">Aucune infrastructure disponible</option>}
            {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name} · {project.status}</option>)}
          </select>
          <button className="refresh-btn" disabled={!projectId} onClick={() => loadLogs(projectId)}>Actualiser</button>
          <button className="export-btn" disabled={!projectId || exporting !== null} onClick={() => void exportLogs("csv")}>
            {exporting === "csv" ? "Export CSV..." : "Exporter CSV"}
          </button>
          <button className="export-btn pdf" disabled={!projectId || exporting !== null} onClick={() => void exportLogs("pdf")}>
            {exporting === "pdf" ? "Export PDF..." : "Exporter PDF"}
          </button>
          <Link className="refresh-btn ops-link" to="/gns3-operations">Lancer un diagnostic →</Link>
        </div>
        <section className="monitor-card infrastructure-log-card">
          <div className="card-heading">
            <span className="eyebrow">EVENT STREAM / {projectId || "NO PROJECT"}</span>
            <span className="card-icon">◉</span>
          </div>
          <h2>Historique de l'infrastructure sélectionnée</h2>
          {error && <p className="empty-state">{error}</p>}
          {!error && !logs.length && <p className="empty-state">Aucun événement. Lancez un ping ou un traceroute depuis GNS3 Ops.</p>}
          {!!logs.length && <div className="infrastructure-log-list">
            {logs.map((log) => (
              <article className={`infrastructure-log-row ${log.status}`} key={log.id}>
                <span className="log-status-dot" />
                <div className="log-main">
                  <strong>{log.message}</strong>
                  <small>{log.event_type.toUpperCase()} · cible : {log.target || "—"} · source : {log.source || "—"}</small>
                </div>
                <time dateTime={log.created_at}>{new Date(log.created_at).toLocaleString()}</time>
              </article>
            ))}
          </div>}
        </section>
      </main>
    </>
  );
}
