import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./api/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Login } from "./pages/Login";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { Equipements } from "./pages/Equipements";
import { Infrastructures } from "./pages/Infrastructures";
import { Statistiques } from "./pages/Statistiques";
import { Logs } from "./pages/Logs";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardLayout />}>
              <Route index element={<Navigate to="statistiques" replace />} />
              <Route path="equipements" element={<Equipements />} />
              <Route path="infrastructures" element={<Infrastructures />} />
              <Route path="statistiques" element={<Statistiques />} />
              <Route path="logs" element={<Logs />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;