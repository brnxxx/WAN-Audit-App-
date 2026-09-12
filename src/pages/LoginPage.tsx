import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE, apiPost } from "../api/client";
import type { AdminOut } from "../api/types";

function TopologyIllustration() {
  return (
    <svg viewBox="0 0 320 300" xmlns="http://www.w3.org/2000/svg">
      <line className="link-line" x1="160" y1="30" x2="160" y2="90" />
      <line className="link-line" x1="160" y1="90" x2="60" y2="170" />
      <line className="link-line" x1="160" y1="90" x2="160" y2="170" />
      <line className="link-line" x1="160" y1="90" x2="260" y2="170" />

      <circle cx="160" cy="20" r="5" fill="none" stroke="#4A5560" strokeWidth="1.5" />
      <text x="172" y="18" className="node-label">Internet</text>

      <circle cx="160" cy="90" r="6" fill="none" stroke="var(--accent)" strokeWidth="1.8" />
      <text x="174" y="94" className="node-label">Backbone</text>

      <circle cx="60" cy="180" r="5" fill="#2FAE66" />
      <text x="30" y="205" className="node-label" textAnchor="middle">Site 1</text>
      <text x="30" y="219" className="node-sublabel" textAnchor="middle">online</text>

      <circle cx="160" cy="180" r="5" fill="#2FAE66" />
      <text x="160" y="205" className="node-label" textAnchor="middle">Site 2</text>
      <text x="160" y="219" className="node-sublabel" textAnchor="middle">online</text>

      <circle cx="260" cy="180" r="5" fill="#D98E04" />
      <text x="260" y="205" className="node-label" textAnchor="middle">Site 3</text>
      <text x="260" y="219" className="node-sublabel" textAnchor="middle">warning</text>
    </svg>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "error" | "success" } | null>(null);
  const [apiStatus, setApiStatus] = useState<"checking" | "ok" | "bad">("checking");

  useEffect(() => {
    fetch(`${API_BASE}/`)
      .then((res) => setApiStatus(res.ok ? "ok" : "bad"))
      .catch(() => setApiStatus("bad"));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);

    try {
      const admin = await apiPost<AdminOut>("/auth/login", { username, password });
      setMessage({ text: `Connecté en tant que ${admin.username}.`, type: "success" });
      navigate("/infrastructure");
    } catch (err) {
      const text = err instanceof Error ? err.message : "Erreur inconnue";
      setMessage({ text, type: "error" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="layout">
      <div className="panel-network">
        <div className="brand">
          <span className="brand-dot" />
          WAN Audit
        </div>

        <div className="topology">
          <TopologyIllustration />
        </div>

        <div className="panel-footer">
          Surveillance de l'infrastructure multi-sites
          <br />
          <strong>Site 1 · Site 2 · Site 3 · Backbone</strong>
        </div>
      </div>

      <div className="panel-form">
        <div className="form-wrap">
          <h1>Connexion</h1>
          <p className="lead">Accès réservé à l'administration du monitoring réseau.</p>

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="username">Nom d'utilisateur</label>
              <input
                type="text"
                id="username"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div className="field">
              <div className="field-row">
                <label htmlFor="password" style={{ marginBottom: 0 }}>Mot de passe</label>
                <button
                  type="button"
                  className="toggle-visibility"
                  onClick={() => setShowPassword((v) => !v)}
                >
                  {showPassword ? "Masquer" : "Afficher"}
                </button>
              </div>
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                autoComplete="current-password"
                required
                style={{ marginTop: 6 }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button type="submit" className="submit-btn" disabled={submitting}>
              {submitting ? "Connexion..." : "Se connecter"}
            </button>

            {message && <div className={`message ${message.type}`}>{message.text}</div>}
          </form>

          <div className="api-status">
            <span className={`dot ${apiStatus === "ok" ? "ok" : apiStatus === "bad" ? "bad" : ""}`} />
            <span>
              {apiStatus === "checking" && "Vérification de l'API..."}
              {apiStatus === "ok" && "API connectée"}
              {apiStatus === "bad" && "API injoignable (vérifie qu'uvicorn tourne)"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
