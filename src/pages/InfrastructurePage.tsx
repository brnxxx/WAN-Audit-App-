import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiPost, API_BASE, UnauthorizedError } from "../api/client";
import type { DeviceOut, GNS3Project, ImportResult } from "../api/types";

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

  useEffect(() => {
    loadProjects();
    loadDevices();
  }, [loadProjects, loadDevices]);

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
                    <Link to="/sites-backbone" className="topnav-link">Sites & Backbone</Link>
        </nav>
        <button className="logout-btn" onClick={handleLogout}>Se déconnecter</button>
      </div>

      <div className="content">
        <h1>Infrastructure</h1>
        <p className="subtitle">Équipements synchronisés depuis GNS3 et stockés en base.</p>

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
          <button className="refresh-btn" onClick={loadDevices}>Rafraîchir la liste</button>

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
              {devices !== null && devices.length === 0 && !devicesError && (
                <tr>
                  <td colSpan={5} className="empty-state">
                    Aucun équipement en base. Importe un projet GNS3 pour commencer.
                  </td>
                </tr>
              )}
              {devicesError && (
                <tr><td colSpan={5} className="empty-state">{devicesError}</td></tr>
              )}
              {devices?.map((d) => (
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
      </div>
    </>
  );
}
