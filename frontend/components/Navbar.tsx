"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Dashboard" },
    { href: "/tasks", label: "Tasks" },
    { href: "/chat", label: "Neural Net" },
    { href: "/settings", label: "Settings" },
  ];

  return (
    <nav className="border-b border-slate-100 dark:border-slate-800 bg-white/80 dark:bg-[#0a0f1a]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20 items-center">
          <div className="flex items-center gap-8">
            <div className="flex-shrink-0 flex items-center gap-2">
              <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse"></div>
              <span className="font-bold text-2xl tracking-widest uppercase text-slate-900 dark:text-slate-100">
                Ultron <span className="font-light text-cyan-500">MKII</span>
              </span>
            </div>
            <div className="hidden sm:flex sm:space-x-8 h-full items-center">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`group relative px-1 py-2 text-sm font-medium uppercase tracking-wider transition-colors ${
                    pathname === link.href ? "text-cyan-500" : "text-slate-500 dark:text-slate-400 hover:text-cyan-500"
                  }`}
                >
                  {link.label}
                  <span className={`absolute bottom-0 left-0 h-0.5 bg-cyan-400 transition-all ${
                    pathname === link.href ? "w-full" : "w-0 group-hover:w-full"
                  }`}></span>
                </Link>
              ))}
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-xs font-mono text-slate-300 dark:text-slate-600 tracking-widest">
                SYS.VER.0.2.0
            </div>
            
            {/* Mobile menu button */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="sm:hidden p-2 rounded-md text-slate-400 hover:text-cyan-500 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="sm:hidden border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-[#0f172a]">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setIsOpen(false)}
                className={`block px-3 py-2 rounded-md text-base font-medium uppercase tracking-wider ${
                    pathname === link.href 
                    ? "bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400" 
                    : "text-slate-500 dark:text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
