import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";
import { useAuth } from "../api/AuthContext";

const navItems = [
  { to: "/dashboard/statistiques", label: "Statistiques" },
  { to: "/dashboard/equipements", label: "Équipements" },
  { to: "/dashboard/infrastructures", label: "Infrastructures" },
  { to: "/dashboard/logs", label: "Historique" },
];

export function DashboardLayout() {
  const { admin, setAdmin } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    setAdmin(null);
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 bg-panel border-r border-ink/10 flex flex-col shrink-0">
        <div className="px-6 py-6">
          <p className="text-sm font-medium text-ink">WAN Audit</p>
          <p className="text-xs text-muted font-mono">v0.1 — monitoring</p>
        </div>

        <nav className="flex-1 px-3 space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-signal-soft text-signal font-medium"
                    : "text-muted hover:bg-surface hover:text-ink"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-6 py-5 border-t border-ink/10">
          <p className="text-sm text-ink font-mono">{admin?.username}</p>
          <button
            onClick={handleLogout}
            className="text-xs text-muted hover:text-ink transition-colors mt-1"
          >
            Se déconnecter
          </button>
        </div>
      </aside>

      <main className="flex-1 px-10 py-8">
        <Outlet />
      </main>
    </div>
  );
}