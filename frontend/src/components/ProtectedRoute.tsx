import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../api/AuthContext";

export function ProtectedRoute() {
  const { admin, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Chargement...
      </div>
    );
  }

  if (!admin) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}