import { useEffect, useState, useCallback, useMemo, type CSSProperties } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiPost, API_BASE, UnauthorizedError } from "../api/client";
import type { DeviceOut, GNS3Project, ImportResult, InfrastructureLog } from "../api/types";

const STATUS_LABELS: Record<string, string> = {
  online: "En ligne",
  offline: "Hors ligne",
  warning: "Avertissement",
  unknown: "Inconnu",
};

export default function InfrastructurePage() {
  const navigate = useNavigate();

  const [projects, setProjects] = useState<GNS3Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [projectsError, setProjectsError] = useState<string | null>(null);

  const [devices, setDevices] = useState<DeviceOut[] | null>(null);
  const [devicesError, setDevicesError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [logs, setLogs] = useState<InfrastructureLog[]>([]);
  const [logsError, setLogsError] = useState<string | null>(null);

  const [importing, setImporting] = useState(false);
  const [importSummary, setImportSummary] = useState<{ text: string; error: boolean } | null>(null);

  const handleUnauthorized = useCallback(() => {
    navigate("/login");
  }, [navigate]);

  const loadProjects = useCallback(async () => {
    try {
      const data = await apiGet<GNS3Project[]>("/gns3/projects");
      setProjects(data);
      setProjectsError(null);
      if (data.length > 0) setSelectedProject(data[0].project_id);
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      setProjectsError("Impossible de charger les projets GNS3.");
    }
  }, [handleUnauthorized]);

  const summary = useMemo(() => {
    const rows = devices || [];
    return {
      total: rows.length,
      online: rows.filter((device) => device.status === "online").length,
      offline: rows.filter((device) => device.status === "offline").length,
      unassigned: rows.filter((device) => !device.site_id && !device.backbone_id).length,
    };
  }, [devices]);

  const topology = useMemo(() => {
    const rows = devices || [];
    const groups = new Map<string, number>();
    rows.forEach((device) => {
      const key = device.site_name || device.backbone_name || "Non assigné";
      groups.set(key, (groups.get(key) || 0) + 1);
    });
    return Array.from(groups.entries()).sort((a, b) => b[1] - a[1]).slice(0, 6);
  }, [devices]);

  const visibleDevices = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!devices || !query) return devices || [];
    return devices.filter((device) =>
      [device.name, device.device_type, device.ip_address, device.site_name, device.backbone_name]
        .some((value) => value?.toLowerCase().includes(query)),
    );
  }, [devices, search]);

  const loadDevices = useCallback(async () => {
    setDevices(null);
    try {
      const data = await apiGet<DeviceOut[]>("/devices");
      setDevices(data);
      setDevicesError(null);
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      setDevicesError("Erreur lors du chargement des équipements.");
      setDevices([]);
    }
  }, [handleUnauthorized]);

  const loadLogs = useCallback(async (project: string) => {
    if (!project) {
      setLogs([]);
      return;
    }
    try {
      setLogs(await apiGet<InfrastructureLog[]>(`/gns3/projects/${project}/logs?limit=100`));
      setLogsError(null);
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      setLogsError("Impossible de charger le journal de cette infrastructure.");
    }
  }, [handleUnauthorized]);

  useEffect(() => {
    void Promise.resolve().then(() => Promise.all([loadProjects(), loadDevices()]));
  }, [loadProjects, loadDevices]);
  useEffect(() => {
    void Promise.resolve().then(() => loadLogs(selectedProject));
  }, [loadLogs, selectedProject]);

  async function handleImport() {
    if (!selectedProject) return;
    setImporting(true);
    setImportSummary({ text: "Import en cours...", error: false });

    try {
      const result = await apiPost<ImportResult>(`/gns3/projects/${selectedProject}/import`);
      const warning = result.unmatched_site_warning.length
        ? ` ⚠ Sans site détecté : ${result.unmatched_site_warning.join(", ")}`
        : "";
      setImportSummary({
        text:
          `${result.project} — ${result.devices_created} créé(s), ${result.devices_updated} mis à jour, ` +
          `${result.links_created} lien(s) créé(s), ${result.links_updated} mis à jour.${warning}`,
        error: false,
      });
      await loadDevices();
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      const text = err instanceof Error ? err.message : "Erreur inconnue";
      setImportSummary({ text: `Échec de l'import : ${text}`, error: true });
    } finally {
      setImporting(false);
    }
  }

  async function handleLogout() {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    navigate("/login");
  }

  return (
    <>
            <div className="topbar">
        <div className="brand">
          <span className="brand-dot" />
          WAN Audit
        </div>
        <nav className="topnav">
          <Link to="/infrastructure" className="topnav-link active">Infrastructure</Link>
          <Link to="/equipements" className="topnav-link">Équipements</Link>
          <Link to="/gns3-operations" className="topnav-link">GNS3 Ops</Link>
          <Link to="/sites-backbone" className="topnav-link">Sites & Backbone</Link>
        </nav>
        <button className="logout-btn" onClick={handleLogout}>Se déconnecter</button>
      </div>

      <div className="content">
        <div className="page-heading">
          <div>
            <div className="eyebrow">NETWORK CONTROL CENTER / OVERVIEW</div>
            <h1>Infrastructure</h1>
            <p className="subtitle">Vue temps réel des équipements synchronisés depuis GNS3.</p>
          </div>
          <div className="live-indicator"><span className="pulse-dot" /> SYSTÈME OPÉRATIONNEL</div>
        </div>

        <div className="stats-grid">
          <div className="stat-card"><span className="stat-label">ÉQUIPEMENTS</span><strong>{summary.total}</strong><span className="stat-meta">inventoriés</span></div>
          <div className="stat-card accent"><span className="stat-label">EN LIGNE</span><strong>{summary.online}</strong><span className="stat-meta">connectés</span></div>
          <div className="stat-card danger"><span className="stat-label">HORS LIGNE</span><strong>{summary.offline}</strong><span className="stat-meta">à vérifier</span></div>
          <div className="stat-card warn"><span className="stat-label">À CLASSER</span><strong>{summary.unassigned}</strong><span className="stat-meta">sans rattachement</span></div>
        </div>

        <div className="monitor-grid">
          <section className="monitor-card">
            <div className="card-heading"><span className="eyebrow">TOPOLOGY / DISTRIBUTION</span><span className="card-icon">◈</span></div>
            <h2>Répartition des équipements</h2>
            {topology.length === 0 ? (
              <p className="muted-copy">Importez un projet GNS3 pour initialiser la carte logique.</p>
            ) : (
              <div className="topology-bars">
                {topology.map(([name, count]) => (
                  <div className="topology-row" key={name}>
                    <span title={name}>{name}</span>
                    <div className="bar-track"><i style={{ width: `${Math.max(12, (count / summary.total) * 100)}%` }} /></div>
                    <strong>{count}</strong>
                  </div>
                ))}
              </div>
            )}
          </section>
          <section className="monitor-card">
            <div className="card-heading"><span className="eyebrow">HEALTH / SIGNAL</span><span className="card-icon">⌁</span></div>
            <h2>État du parc</h2>
            <div className="health-ring" style={{ "--health": `${summary.total ? (summary.online / summary.total) * 100 : 0}%` } as CSSProperties}>
              <strong>{summary.total ? Math.round((summary.online / summary.total) * 100) : 0}%</strong>
              <span>disponibilité</span>
            </div>
            <div className="health-caption"><span><i className="health-key ok" /> Opérationnels</span><b>{summary.online}</b><span><i className="health-key bad" /> À vérifier</span><b>{summary.offline + summary.unassigned}</b></div>
          </section>
        </div>

        <div className="control-bar">
          <label htmlFor="project-select">Projet GNS3</label>
          <select
            id="project-select"
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            disabled={projects.length === 0}
          >
            {projects.length === 0 && (
              <option value="">{projectsError || "Chargement des projets..."}</option>
            )}
            {projects.map((p) => (
              <option key={p.project_id} value={p.project_id}>
                {p.name} ({p.status})
              </option>
            ))}
          </select>

          <button className="import-btn" onClick={handleImport} disabled={!selectedProject || importing}>
            {importing ? "Import en cours..." : "Importer"}
          </button>
          <button className="refresh-btn" onClick={() => { void loadDevices(); void loadLogs(selectedProject); }}>Rafraîchir la liste</button>
          <Link to="/gns3-operations" className="refresh-btn ops-link">Ouvrir GNS3 Ops →</Link>
          <Link to="/infrastructure-logs" className="refresh-btn ops-link">Voir les logs →</Link>
          <input
            className="search-input"
            type="search"
            placeholder="Rechercher un équipement..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          {importSummary && (
            <div className={`import-summary${importSummary.error ? " error" : ""}`}>
              {importSummary.text}
            </div>
          )}
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nom</th>
                <th>Type</th>
                <th>Site / Backbone</th>
                <th>Adresse IP</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {devices === null && (
                <tr><td colSpan={5} className="empty-state">Chargement...</td></tr>
              )}
              {devices !== null && visibleDevices.length === 0 && !devicesError && (
                <tr>
                  <td colSpan={5} className="empty-state">
                    {search ? "Aucun équipement ne correspond à cette recherche." : "Aucun équipement en base. Importe un projet GNS3 pour commencer."}
                  </td>
                </tr>
              )}
              {devicesError && (
                <tr><td colSpan={5} className="empty-state">{devicesError}</td></tr>
              )}
              {visibleDevices.map((d) => (
                <tr key={d.id}>
                  <td>{d.name}</td>
                  <td><span className="type-tag">{d.device_type}</span></td>
                  <td>{d.site_name || d.backbone_name || "—"}</td>
                  <td>{d.ip_address || "—"}</td>
                  <td>
                    <span className={`badge ${d.status}`}>
                      <span className="dot" />
                      {STATUS_LABELS[d.status] || d.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <section className="monitor-card infrastructure-log-card">
          <div className="card-heading">
            <span className="eyebrow">AUDIT / INFRASTRUCTURE LOG</span>
            <button className="link-btn" onClick={() => loadLogs(selectedProject)} disabled={!selectedProject}>Actualiser</button>
          </div>
          <h2>Journal de l'infrastructure sélectionnée</h2>
          <p className="muted-copy">Historique isolé du projet GNS3 sélectionné : pings, connectivité, traceroutes et erreurs.</p>
          {logsError && <p className="empty-state">{logsError}</p>}
          {!logsError && logs.length === 0 && <p className="empty-state">Aucun événement enregistré pour cette infrastructure.</p>}
          {logs.length > 0 && <div className="infrastructure-log-list">
            {logs.map((log) => (
              <article className={`infrastructure-log-row ${log.status}`} key={log.id}>
                <span className="log-status-dot" />
                <div className="log-main">
                  <strong>{log.message}</strong>
                  <small>{log.event_type.toUpperCase()} · {log.target || "—"} · source : {log.source || "—"}</small>
                </div>
                <time dateTime={log.created_at}>{new Date(log.created_at).toLocaleString()}</time>
              </article>
            ))}
          </div>}
        </section>
      </div>
    </>
  );
}
