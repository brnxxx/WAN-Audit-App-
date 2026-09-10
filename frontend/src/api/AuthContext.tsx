import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getCurrentAdmin } from "./auth";
import type { Admin } from "../types/admin";

interface AuthContextType {
  admin: Admin | null;
  loading: boolean;
  setAdmin: (admin: Admin | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<Admin | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurrentAdmin()
      .then(setAdmin)
      .catch(() => setAdmin(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AuthContext.Provider value={{ admin, loading, setAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé dans AuthProvider");
  return ctx;
}