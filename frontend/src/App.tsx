import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import BinPage from "./pages/BinPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/b/:binId" element={<BinPage />} />
    </Routes>
  );
}
