import { BrowserRouter, Route, Routes } from "react-router-dom";

import { RootLayout } from "@/components/layout/RootLayout";
import Home from "@/pages/Home";
import Dashboard from "@/pages/Dashboard";
import About from "@/pages/About";
import Solution from "@/pages/Solution";
import Resources from "@/pages/Resources";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="about" element={<About />} />
          <Route path="solution" element={<Solution />} />
          <Route path="resources" element={<Resources />} />
          <Route path="*" element={<Home />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
