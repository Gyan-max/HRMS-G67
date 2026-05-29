import { useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { Logo } from "./Logo";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Home",      to: "/" },
  { label: "Dashboard", to: "/dashboard" },
  { label: "Solution",  to: "/solution" },
  { label: "Resources", to: "/resources" },
  { label: "About",     to: "/about" },
] as const;

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Close mobile panel on route change
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Prevent body scroll while mobile menu is open
  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-background/75 backdrop-blur-lg">
      <div className="container flex h-16 items-center justify-between">
        {/* Brand */}
        <NavLink to="/" className="flex items-center gap-3 shrink-0">
          <Logo className="h-9 w-9" />
          <div className="leading-tight">
            <div className="font-display text-[17px] font-bold tracking-tight">
              Sentinel
            </div>
            <div className="hidden text-[9px] uppercase tracking-[0.22em] text-muted-foreground sm:block">
              Early Mental‑Health Signals
            </div>
          </div>
        </NavLink>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-0.5 md:flex">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-full px-4 py-2 text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "bg-white/10 text-foreground"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
          <Button asChild size="sm" className="ml-3">
            <NavLink to="/dashboard">Check in →</NavLink>
          </Button>
        </nav>

        {/* Mobile hamburger */}
        <button
          type="button"
          aria-label={isOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={isOpen}
          onClick={() => setIsOpen((v) => !v)}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg transition-colors duration-150 md:hidden",
            isOpen
              ? "bg-white/10 text-foreground"
              : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
          )}
        >
          {isOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Mobile slide-down panel */}
      <div
        className={cn(
          "overflow-hidden border-b border-white/5 bg-background/95 backdrop-blur-xl transition-all duration-200 ease-in-out md:hidden",
          isOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0 pointer-events-none",
        )}
      >
        <nav className="container flex flex-col gap-1 pb-5 pt-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-xl px-4 py-3 text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "bg-white/10 text-foreground"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
          <div className="mt-2">
            <Button asChild size="md" className="w-full">
              <NavLink to="/dashboard">Open Dashboard →</NavLink>
            </Button>
          </div>
        </nav>
      </div>
    </header>
  );
}
