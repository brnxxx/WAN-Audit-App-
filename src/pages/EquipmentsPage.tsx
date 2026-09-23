import { useEffect, useState, useCallback, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiPut, API_BASE, UnauthorizedError } from "../api/client";
import type { DeviceOut, SiteOut, BackboneOut, DeviceUpdatePayload } from "../api/types";

const STATUS_LABELS: Record<string, string> = {
  online: "En ligne",
  offline: "Hors ligne",
  warning: "Avertissement",
  unknown: "Inconnu",
};

type LocationChoice = string; // "site:3" | "backbone:1" | "none"

function locationValue(d: DeviceOut): LocationChoice {
  if (d.site_id != null) return `site:${d.site_id}`;
  if (d.backbone_id != null) return `backbone:${d.backbone_id}`;
  return "none";
}

export default function EquipmentsPage() {
  const navigate = useNavigate();

  const [devices, setDevices] = useState<DeviceOut[] | null>(null);
  const [devicesError, setDevicesError] = useState<string | null>(null);
  const [sites, setSites] = useState<SiteOut[]>([]);
  const [backbones, setBackbones] = useState<BackboneOut[]>([]);

  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [rowError, setRowError] = useState<{ id: number; text: string } | null>(null);

  const handleUnauthorized = useCallback(() => navigate("/login"), [navigate]);

  const loadAll = useCallback(async () => {
    setDevices(null);
    try {
      const [d, s, b] = await Promise.all([
        apiGet<DeviceOut[]>("/devices"),
        apiGet<SiteOut[]>("/sites"),
        apiGet<BackboneOut[]>("/backbone"),
      ]);
      setDevices(d);
      setSites(s);
      setBackbones(b);
      setDevicesError(null);
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      setDevicesError("Erreur lors du chargement des équipements.");
      setDevices([]);
    }
  }, [handleUnauthorized]);

  useEffect(() => {
    void Promise.resolve().then(loadAll);
  }, [loadAll]);

  const types = useMemo(
    () => Array.from(new Set((devices || []).map((d) => d.device_type))).sort(),
    [devices]
  );

  const filtered = useMemo(() => {
    if (!devices) return [];
    return devices.filter((d) => {
      if (typeFilter !== "all" && d.device_type !== typeFilter) return false;
      if (statusFilter !== "all" && d.status !== statusFilter) return false;
      return true;
    });
  }, [devices, typeFilter, statusFilter]);

  async function handleLocationChange(device: DeviceOut, value: LocationChoice) {
    setSavingId(device.id);
    setRowError(null);

    let site_id: number | null = null;
    let backbone_id: number | null = null;
    if (value.startsWith("site:")) site_id = Number(value.split(":")[1]);
    else if (value.startsWith("backbone:")) backbone_id = Number(value.split(":")[1]);

    const payload: DeviceUpdatePayload = {
      name: device.name,
      hostname: device.hostname,
      ip_address: device.ip_address,
      device_type: device.device_type,
      vendor: device.vendor,
      model: device.model,
      site_id,
      backbone_id,
      management_protocol: device.management_protocol,
      username: device.username,
      port: device.port,
    };

    try {
      await apiPut<DeviceOut>(`/devices/${device.id}`, payload);
      await loadAll();
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      const text = err instanceof Error ? err.message : "Erreur inconnue";
      setRowError({ id: device.id, text: `Échec : ${text}` });
    } finally {
      setSavingId(null);
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
          <Link to="/infrastructure" className="topnav-link">Infrastructure</Link>
          <Link to="/equipements" className="topnav-link active">Équipements</Link>
          <Link to="/gns3-operations" className="topnav-link">GNS3 Ops</Link>
          <Link to="/infrastructure-logs" className="topnav-link">Logs</Link>
          <Link to="/sites-backbone" className="topnav-link">Sites & Backbone</Link>
        </nav>
        <button className="logout-btn" onClick={handleLogout}>Se déconnecter</button>
      </div>

      <div className="content">
        <h1>Équipements</h1>
        <p className="subtitle">Gestion des équipements et de leur affectation site / backbone.</p>

        <div className="control-bar">
          <label htmlFor="type-filter">Type</label>
          <select id="type-filter" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="all">Tous</option>
            {types.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>

          <label htmlFor="status-filter">Statut</label>
          <select id="status-filter" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">Tous</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          <button className="refresh-btn" onClick={loadAll}>Rafraîchir</button>
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
              {devices !== null && filtered.length === 0 && !devicesError && (
                <tr><td colSpan={5} className="empty-state">Aucun équipement ne correspond aux filtres.</td></tr>
              )}
              {devicesError && (
                <tr><td colSpan={5} className="empty-state">{devicesError}</td></tr>
              )}
              {filtered.map((d) => {
                const unassigned = d.site_id == null && d.backbone_id == null;
                return (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td><span className="type-tag">{d.device_type}</span></td>
                    <td>
                      <div className="location-cell">
                        {unassigned && <span className="badge unassigned"><span className="dot" />Non assigné</span>}
                        <select
                          className="location-select"
                          value={locationValue(d)}
                          disabled={savingId === d.id}
                          onChange={(e) => handleLocationChange(d, e.target.value)}
                        >
                          <option value="none">— Aucun —</option>
                          {sites.map((s) => (
                            <option key={`site:${s.id}`} value={`site:${s.id}`}>{s.name}</option>
                          ))}
                          {backbones.map((b) => (
                            <option key={`backbone:${b.id}`} value={`backbone:${b.id}`}>{b.name} (backbone)</option>
                          ))}
                        </select>
                        {rowError?.id === d.id && <span className="row-error">{rowError.text}</span>}
                      </div>
                    </td>
                    <td>{d.ip_address || "—"}</td>
                    <td>
                      <span className={`badge ${d.status}`}>
                        <span className="dot" />
                        {STATUS_LABELS[d.status] || d.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}