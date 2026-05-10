import { NavLink } from "react-router-dom";
import { Logo } from "./Logo";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Home", to: "/" },
  { label: "Dashboard", to: "/dashboard" },
  { label: "About", to: "/about" },
  { label: "Solution", to: "/solution" },
  { label: "Resources", to: "/resources" },
] as const;

/**
 * Top navigation bar — brand on the left, links on the right. Sticky with a
 * blurred backdrop so it floats above page content.
 */
export function Navbar() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-background/70 backdrop-blur-lg">
      <div className="container flex h-16 items-center justify-between">
        <NavLink to="/" className="flex items-center gap-3">
          <Logo className="h-9 w-9" />
          <div className="leading-tight">
            <div className="font-display text-lg font-bold tracking-tight">
              Sentinel
            </div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              Early Mental-Health Signals
            </div>
          </div>
        </NavLink>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-full px-4 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-white/10 text-foreground"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Mobile: simple compact nav (links wrap; no JS hamburger for PR A) */}
        <nav className="flex items-center gap-1 md:hidden">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-full px-2.5 py-1.5 text-[11px] font-medium uppercase tracking-wide transition-colors",
                  isActive
                    ? "bg-white/10 text-foreground"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                )
              }
            >
              {item.label[0]}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
