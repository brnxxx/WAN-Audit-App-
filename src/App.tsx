import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import InfrastructurePage from "./pages/InfrastructurePage";
import EquipmentsPage from "./pages/EquipmentsPage";
import SitesBackbonePage from "./pages/SitesBackbonePage";
import GNS3OperationsPage from "./pages/GNS3OperationsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/infrastructure" element={<InfrastructurePage />} />
        <Route path="/equipements" element={<EquipmentsPage />} />
        <Route path="/sites-backbone" element={<SitesBackbonePage />} />
        <Route path="/gns3-operations" element={<GNS3OperationsPage />} />
      </Routes>
    </BrowserRouter>
  );
}