import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiPost, API_BASE, UnauthorizedError } from "../api/client";
import type { GNS3Command, GNS3Node, GNS3Project, PingResult } from "../api/types";

export default function GNS3OperationsPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<GNS3Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [nodes, setNodes] = useState<GNS3Node[]>([]);
  const [commands, setCommands] = useState<GNS3Command[]>([]);
  const [query, setQuery] = useState("");
  const [target, setTarget] = useState("");
  const [ping, setPing] = useState<PingResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const authFailure = useCallback((error: unknown) => {
    if (error instanceof UnauthorizedError) navigate("/login");
    else setMessage(error instanceof Error ? error.message : "Opération impossible");
  }, [navigate]);

  const load = useCallback(async () => {
    try {
      const projectList = await apiGet<GNS3Project[]>("/gns3/projects");
      setProjects(projectList);
      const selected = projectId || projectList[0]?.project_id || "";
      setProjectId(selected);
      if (selected) setNodes(await apiGet<GNS3Node[]>(`/gns3/projects/${selected}/nodes`));
      setCommands(await apiGet<GNS3Command[]>("/gns3/commands"));
    } catch (error) {
      authFailure(error);
    }
  }, [authFailure, projectId]);

  useEffect(() => { void Promise.resolve().then(load); }, [load]);

  const filteredCommands = useMemo(() => {
    const value = query.toLowerCase().trim();
    if (!value) return commands;
    return commands.filter((item) => `${item.platform} ${item.category} ${item.command} ${item.purpose}`.toLowerCase().includes(value));
  }, [commands, query]);

  async function control(path: string, label: string) {
    try {
      await apiPost(path);
      setMessage(`${label} terminé.`);
      if (projectId) setNodes(await apiGet<GNS3Node[]>(`/gns3/projects/${projectId}/nodes`));
    } catch (error) { authFailure(error); }
  }

  async function runPing(event: React.FormEvent) {
    event.preventDefault();
    try {
      setPing(await apiPost<PingResult>("/gns3/diagnostics/ping", { target, count: 4 }));
    } catch (error) { authFailure(error); }
  }

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
          <Link to="/gns3-operations" className="topnav-link active">GNS3 Ops</Link>
          <Link to="/sites-backbone" className="topnav-link">Sites & Backbone</Link>
        </nav>
        <button className="logout-btn" onClick={logout}>Se déconnecter</button>
      </div>
      <main className="content">
        <div className="page-heading">
          <div><div className="eyebrow">GNS3 / OPERATIONS CENTER</div><h1>Contrôle réseau</h1><p className="subtitle">Supervision, diagnostics et opérations contrôlées sur vos projets GNS3.</p></div>
          <div className="live-indicator"><span className="pulse-dot" /> COMMAND CENTER</div>
        </div>
        <div className="control-bar">
          <label htmlFor="ops-project">Projet</label>
          <select id="ops-project" value={projectId} onChange={async (event) => { const id = event.target.value; setProjectId(id); setNodes(await apiGet<GNS3Node[]>(`/gns3/projects/${id}/nodes`)); }}>
            {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name} · {project.status}</option>)}
          </select>
          <button className="import-btn" disabled={!projectId} onClick={() => control(`/gns3/projects/${projectId}/start`, "Démarrage du projet")}>Démarrer</button>
          <button className="refresh-btn" disabled={!projectId} onClick={() => control(`/gns3/projects/${projectId}/stop`, "Arrêt du projet")}>Arrêter</button>
          {message && <span className="import-summary">{message}</span>}
        </div>
        <div className="ops-grid">
          <section className="monitor-card">
            <div className="card-heading"><span className="eyebrow">NODES / CONTROL</span><span className="card-icon">◇</span></div>
            <h2>Nœuds du projet</h2>
            <div className="node-list">{nodes.map((node) => <div className="node-row" key={node.node_id}><div><strong>{node.name}</strong><small>{node.node_type} · {node.status || "unknown"}</small></div><div><button className="link-btn" onClick={() => control(`/gns3/projects/${projectId}/nodes/${node.node_id}/start`, `Démarrage de ${node.name}`)}>Start</button><button className="link-btn danger" onClick={() => control(`/gns3/projects/${projectId}/nodes/${node.node_id}/stop`, `Arrêt de ${node.name}`)}>Stop</button></div></div>)}</div>
          </section>
          <section className="monitor-card">
            <div className="card-heading"><span className="eyebrow">DIAGNOSTICS / REACHABILITY</span><span className="card-icon">⌁</span></div>
            <h2>Ping sécurisé</h2>
            <form className="diagnostic-form" onSubmit={runPing}><input type="text" placeholder="Adresse IPv4 ou IPv6" value={target} onChange={(event) => setTarget(event.target.value)} required /><button className="import-btn">Tester</button></form>
            {ping && <pre className={`diagnostic-result ${ping.reachable ? "ok" : "bad"}`}>{ping.reachable ? "● JOIGNABLE" : "● INJOIGNABLE"}{"\n"}{ping.output}</pre>}
          </section>
        </div>
        <section className="monitor-card command-guide">
          <div className="card-heading"><span className="eyebrow">KNOWLEDGE BASE / COMMAND GUIDE</span><span className="card-icon">⌘</span></div>
          <h2>Guide de commandes réseau</h2>
          <input className="search-input" type="search" placeholder="Rechercher une commande, plateforme ou usage..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <div className="command-grid">{filteredCommands.map((item) => <article className="command-card" key={`${item.platform}-${item.command}`}><div className="command-meta"><span>{item.platform}</span><span className={item.risk === "read-only" ? "risk-safe" : "risk-change"}>{item.risk}</span></div><code>{item.command}</code><p>{item.purpose}</p></article>)}</div>
        </section>
      </main>
    </>
  );
}
