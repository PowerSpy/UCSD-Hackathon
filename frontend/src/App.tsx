import { Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { Learn } from "./pages/Learn";
import { ProgressPage } from "./pages/ProgressPage";
import { QuizPage } from "./pages/QuizPage";

export default function App() {
  return (
    <div className="min-h-screen">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow"
      >
        Skip to content
      </a>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/learn" element={<Learn />} />
        <Route path="/quiz/:topic" element={<QuizPage />} />
        <Route path="/progress" element={<ProgressPage />} />
      </Routes>
    </div>
  );
}
