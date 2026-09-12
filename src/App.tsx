import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import InfrastructurePage from "./pages/InfrastructurePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/infrastructure" element={<InfrastructurePage />} />
      </Routes>
    </BrowserRouter>
  );
}
