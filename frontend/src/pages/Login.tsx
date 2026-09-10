import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useAuth } from "../api/AuthContext";

export function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { setAdmin } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const admin = await login(username, password);
      setAdmin(admin);
      navigate("/dashboard");
    } catch {
      setError("Identifiants incorrects.");
    } finally {
      setSubmitting(false);
    }
  }

      return (
    <div className="min-h-screen flex items-center justify-center bg-surface">
      <form
        onSubmit={handleSubmit}
        className="bg-panel border border-ink/10 rounded-lg p-8 w-full max-w-sm"
      >
        <p className="text-xs text-muted font-mono mb-1">wan-audit</p>
        <h1 className="text-lg font-medium text-ink mb-6">Connexion</h1>

        <label className="block text-sm text-muted mb-1">Nom d'utilisateur</label>
        <input
          className="w-full border border-ink/15 rounded-md px-3 py-2 mb-4 text-sm font-mono focus:outline-none focus:border-signal focus:ring-1 focus:ring-signal"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <label className="block text-sm text-muted mb-1">Mot de passe</label>
        <input
          type="password"
          className="w-full border border-ink/15 rounded-md px-3 py-2 mb-5 text-sm focus:outline-none focus:border-signal focus:ring-1 focus:ring-signal"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <p className="text-sm text-status-offline mb-4">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-ink text-white rounded-md py-2 text-sm font-medium hover:bg-signal transition-colors disabled:opacity-50"
        >
          {submitting ? "Connexion…" : "Se connecter"}
        </button>
      </form>
    </div>
  );
}