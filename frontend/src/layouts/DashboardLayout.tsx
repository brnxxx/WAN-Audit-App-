import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { BarChart3, Router, Network, ScrollText, LogOut } from "lucide-react";
import { logout } from "../api/auth";
import { useAuth } from "../api/AuthContext";

const navItems = [
  { to: "/dashboard/statistiques", label: "Statistiques", icon: BarChart3 },
  { to: "/dashboard/equipements", label: "Équipements", icon: Router },
  { to: "/dashboard/infrastructures", label: "Infrastructures", icon: Network },
  { to: "/dashboard/logs", label: "Historique", icon: ScrollText },
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
    <div className="min-h-screen flex bg-surface">
      <aside className="w-60 bg-panel shadow-panel flex flex-col shrink-0 z-10">
        <div className="px-6 py-6 flex items-center gap-2.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-status-online pulse-live" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-status-online" />
          </span>
          <div>
            <p className="text-sm font-medium text-ink leading-none">WAN Audit</p>
            <p className="text-xs text-muted font-mono mt-1">v0.1 — monitoring</p>
          </div>
        </div>

        <nav className="flex-1 px-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                    isActive
                      ? "bg-signal/15 text-signal shadow-glow translate-x-0.5"
                      : "text-muted hover:bg-white/5 hover:text-ink hover:translate-x-0.5"
                  }`
                }
              >
                <Icon size={17} strokeWidth={2} className="transition-transform duration-200 group-hover:scale-110" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="px-6 py-5 border-t border-ink/10">
          <p className="text-sm text-ink font-mono">{admin?.username}</p>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-xs text-muted hover:text-status-offline transition-colors mt-2"
          >
            <LogOut size={13} />
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