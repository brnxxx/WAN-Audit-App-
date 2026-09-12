import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import InfrastructurePage from "./pages/InfrastructurePage";
import EquipmentsPage from "./pages/EquipmentsPage";
import SitesBackbonePage from "./pages/SitesBackbonePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/infrastructure" element={<InfrastructurePage />} />
        <Route path="/equipements" element={<EquipmentsPage />} />
        <Route path="/sites-backbone" element={<SitesBackbonePage />} />
      </Routes>
    </BrowserRouter>
  );
}