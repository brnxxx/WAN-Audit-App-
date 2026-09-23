import { useEffect, useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiGet, apiPost, apiPut, apiDelete, API_BASE, UnauthorizedError } from "../api/client";
import type { SiteOut, BackboneOut } from "../api/types";

interface SiteForm {
  name: string;
  description: string;
  location: string;
}

interface BackboneForm {
  name: string;
  description: string;
}

const emptySiteForm: SiteForm = { name: "", description: "", location: "" };
const emptyBackboneForm: BackboneForm = { name: "", description: "" };

export default function SitesBackbonePage() {
  const navigate = useNavigate();

  const [sites, setSites] = useState<SiteOut[] | null>(null);
  const [backbones, setBackbones] = useState<BackboneOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [siteForm, setSiteForm] = useState<SiteForm>(emptySiteForm);
  const [editingSiteId, setEditingSiteId] = useState<number | null>(null);

  const [backboneForm, setBackboneForm] = useState<BackboneForm>(emptyBackboneForm);
  const [editingBackboneId, setEditingBackboneId] = useState<number | null>(null);

  const handleUnauthorized = useCallback(() => navigate("/login"), [navigate]);

  const loadAll = useCallback(async () => {
    try {
      const [s, b] = await Promise.all([
        apiGet<SiteOut[]>("/sites"),
        apiGet<BackboneOut[]>("/backbone"),
      ]);
      setSites(s);
      setBackbones(b);
      setError(null);
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      setError("Erreur lors du chargement.");
    }
  }, [handleUnauthorized]);

  useEffect(() => {
    void Promise.resolve().then(loadAll);
  }, [loadAll]);

  // ---------- Sites ----------

  function startEditSite(site: SiteOut) {
    setEditingSiteId(site.id);
    setSiteForm({
      name: site.name,
      description: site.description || "",
      location: site.location || "",
    });
  }

  function cancelSiteEdit() {
    setEditingSiteId(null);
    setSiteForm(emptySiteForm);
  }

  async function submitSite(e: React.FormEvent) {
    e.preventDefault();
    const payload = {
      name: siteForm.name,
      description: siteForm.description || null,
      location: siteForm.location || null,
    };
    try {
      if (editingSiteId) {
        await apiPut(`/sites/${editingSiteId}`, payload);
      } else {
        await apiPost("/sites", payload);
      }
      cancelSiteEdit();
      await loadAll();
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      const text = err instanceof Error ? err.message : "Erreur inconnue";
      setError(text);
    }
  }

  async function removeSite(site: SiteOut) {
    if (!confirm(`Supprimer le site "${site.name}" ? Les équipements rattachés seront aussi supprimés (cascade).`)) return;
    try {
      await apiDelete(`/sites/${site.id}`);
      await loadAll();
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      const text = err instanceof Error ? err.message : "Erreur inconnue";
      setError(text);
    }
  }

  // ---------- Backbone ----------

  function startEditBackbone(b: BackboneOut) {
    setEditingBackboneId(b.id);
    setBackboneForm({ name: b.name, description: b.description || "" });
  }

  function cancelBackboneEdit() {
    setEditingBackboneId(null);
    setBackboneForm(emptyBackboneForm);
  }

  async function submitBackbone(e: React.FormEvent) {
    e.preventDefault();
    const payload = {
      name: backboneForm.name,
      description: backboneForm.description || null,
    };
    try {
      if (editingBackboneId) {
        await apiPut(`/backbone/${editingBackboneId}`, payload);
      } else {
        await apiPost("/backbone", payload);
      }
      cancelBackboneEdit();
      await loadAll();
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      const text = err instanceof Error ? err.message : "Erreur inconnue";
      setError(text);
    }
  }

  async function removeBackbone(b: BackboneOut) {
    if (!confirm(`Supprimer le backbone "${b.name}" ? Les équipements rattachés seront aussi supprimés (cascade).`)) return;
    try {
      await apiDelete(`/backbone/${b.id}`);
      await loadAll();
    } catch (err) {
      if (err instanceof UnauthorizedError) return handleUnauthorized();
      const text = err instanceof Error ? err.message : "Erreur inconnue";
      setError(text);
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
          <Link to="/equipements" className="topnav-link">Équipements</Link>
          <Link to="/gns3-operations" className="topnav-link">GNS3 Ops</Link>
          <Link to="/infrastructure-logs" className="topnav-link">Logs</Link>
          <Link to="/sites-backbone" className="topnav-link active">Sites & Backbone</Link>
        </nav>
        <button className="logout-btn" onClick={handleLogout}>Se déconnecter</button>
      </div>

      <div className="content">
        <h1>Sites & Backbone</h1>
        <p className="subtitle">Gestion des sites et du backbone de l'infrastructure.</p>

        {error && <div className="import-summary error">{error}</div>}

        {/* ---------- SITES ---------- */}
        <h2 className="section-title">Sites</h2>

        <form className="entity-form" onSubmit={submitSite}>
          <input
            type="text" placeholder="Nom (ex: SITE1)" required
            value={siteForm.name}
            onChange={(e) => setSiteForm({ ...siteForm, name: e.target.value })}
          />
          <input
            type="text" placeholder="Description"
            value={siteForm.description}
            onChange={(e) => setSiteForm({ ...siteForm, description: e.target.value })}
          />
          <input
            type="text" placeholder="Localisation"
            value={siteForm.location}
            onChange={(e) => setSiteForm({ ...siteForm, location: e.target.value })}
          />
          <button type="submit" className="import-btn">
            {editingSiteId ? "Enregistrer" : "Ajouter"}
          </button>
          {editingSiteId && (
            <button type="button" className="refresh-btn" onClick={cancelSiteEdit}>Annuler</button>
          )}
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nom</th>
                <th>Description</th>
                <th>Localisation</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sites === null && (
                <tr><td colSpan={4} className="empty-state">Chargement...</td></tr>
              )}
              {sites?.length === 0 && (
                <tr><td colSpan={4} className="empty-state">Aucun site pour l'instant.</td></tr>
              )}
              {sites?.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>{s.description || "—"}</td>
                  <td>{s.location || "—"}</td>
                  <td className="row-actions">
                    <button className="link-btn" onClick={() => startEditSite(s)}>Modifier</button>
                    <button className="link-btn danger" onClick={() => removeSite(s)}>Supprimer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* ---------- BACKBONE ---------- */}
        <h2 className="section-title">Backbone</h2>

        <form className="entity-form" onSubmit={submitBackbone}>
          <input
            type="text" placeholder="Nom (ex: Backbone)" required
            value={backboneForm.name}
            onChange={(e) => setBackboneForm({ ...backboneForm, name: e.target.value })}
          />
          <input
            type="text" placeholder="Description"
            value={backboneForm.description}
            onChange={(e) => setBackboneForm({ ...backboneForm, description: e.target.value })}
          />
          <button type="submit" className="import-btn">
            {editingBackboneId ? "Enregistrer" : "Ajouter"}
          </button>
          {editingBackboneId && (
            <button type="button" className="refresh-btn" onClick={cancelBackboneEdit}>Annuler</button>
          )}
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nom</th>
                <th>Description</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {backbones === null && (
                <tr><td colSpan={3} className="empty-state">Chargement...</td></tr>
              )}
              {backbones?.length === 0 && (
                <tr><td colSpan={3} className="empty-state">Aucun backbone pour l'instant.</td></tr>
              )}
              {backbones?.map((b) => (
                <tr key={b.id}>
                  <td>{b.name}</td>
                  <td>{b.description || "—"}</td>
                  <td className="row-actions">
                    <button className="link-btn" onClick={() => startEditBackbone(b)}>Modifier</button>
                    <button className="link-btn danger" onClick={() => removeBackbone(b)}>Supprimer</button>
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