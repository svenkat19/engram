import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import DashboardPage from "./pages/DashboardPage";
import SearchPage from "./pages/SearchPage";
import GraphPage from "./pages/GraphPage";
import EntityDetailPage from "./pages/EntityDetailPage";

function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="/entity/:id" element={<EntityDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
