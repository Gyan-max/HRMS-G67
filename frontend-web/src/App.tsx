import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { RootLayout } from "@/components/layout/RootLayout";
import Home from "@/pages/Home";
import About from "@/pages/About";
import Solution from "@/pages/Solution";
import Resources from "@/pages/Resources";

// Dashboard pulls in recharts, react-query, react-hook-form & zod, so we
// lazy-load it. Landing pages stay light and TTI is low.
const Dashboard = lazy(() => import("@/pages/Dashboard"));

const DashboardFallback = () => (
  <div className="container py-24 text-center text-sm text-muted-foreground">
    Loading dashboard…
  </div>
);

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<Home />} />
          <Route
            path="dashboard"
            element={
              <Suspense fallback={<DashboardFallback />}>
                <Dashboard />
              </Suspense>
            }
          />
          <Route path="about" element={<About />} />
          <Route path="solution" element={<Solution />} />
          <Route path="resources" element={<Resources />} />
          <Route path="*" element={<Home />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
