import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import axios from 'axios';
import { LayoutDashboard, Network, GitFork, AlertTriangle, Beaker, Database, Search, FileText, X } from 'lucide-react';

export function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

interface Paper {
  id: number;
  title: string;
  year: number;
  relevance: string;
}

export function AppShell() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Paper[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setShowResults(true);
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL}/knowledge-graph?q=${searchQuery}`);
      setSearchResults(res.data.results || []);
    } catch (err) {
      console.error(err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
  };

  return (
    <div className="flex h-screen bg-white text-zinc-900 overflow-hidden font-sans selection:bg-cyan-500/30">

      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-200 bg-zinc-50 flex flex-col z-20 relative">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <Beaker className="w-8 h-8 text-cyan-600" />
            <h1 className="text-xl font-bold tracking-tight uppercase text-zinc-950">
              Catalyst<span className="text-cyan-700">OS</span>
            </h1>
          </div>

          {/* Global Search */}
          <div className="mb-6 relative">
            <form onSubmit={handleSearch}>
              <div className="relative flex items-center">
                <Search className="w-4 h-4 text-zinc-500 absolute left-3" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search research..."
                  className="w-full bg-white border border-zinc-300 rounded pl-9 pr-8 py-2 text-sm text-zinc-900 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-zinc-400"
                />
                {searchQuery && (
                  <button type="button" onClick={clearSearch} className="absolute right-2 text-zinc-400 hover:text-zinc-600">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </form>

            {/* Search Results Overlay */}
            {showResults && (
              <div className="absolute top-full left-0 w-full mt-2 bg-white border border-zinc-200 rounded shadow-xl max-h-64 overflow-y-auto z-50">
                {isSearching ? (
                  <div className="p-4 text-xs font-mono text-cyan-700 text-center animate-pulse">Scanning Graph...</div>
                ) : searchResults.length > 0 ? (
                  <div className="py-1">
                    {searchResults.map(paper => (
                      <div key={paper.id} className="px-3 py-2 hover:bg-zinc-100 cursor-pointer border-b border-zinc-50 last:border-0 transition-colors">
                        <p className="text-xs text-zinc-900 font-medium line-clamp-2 mb-1 leading-snug">{paper.title}</p>
                        <div className="flex justify-between items-center text-[10px] font-mono">
                          <span className="text-zinc-500">{paper.year}</span>
                          <span className="text-cyan-700 font-bold bg-cyan-50 px-1.5 rounded">{paper.relevance}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-xs font-mono text-zinc-500 text-center">No matches found.</div>
                )}
              </div>
            )}
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-1.5">
          {[
            { to: "/", icon: LayoutDashboard, label: "Overview" },
            { to: "/copilot", icon: Network, label: "AI Copilot" },
            { to: "/discovery", icon: Database, label: "Discovery" },
            { to: "/prediction", icon: GitFork, label: "Prediction" },
            { to: "/gaps", icon: AlertTriangle, label: "Gap Intelligence" },
            { to: "/experiments", icon: FileText, label: "Experiment Log" },
          ].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md transition-all group",
                  isActive
                    ? "bg-cyan-100 text-cyan-900 border border-cyan-200 shadow-sm"
                    : "text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100"
                )
              }
            >
              <item.icon className={cn("w-4 h-4 transition-colors", "group-hover:text-cyan-600")} />
              <span className="text-sm font-semibold">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer Profile Section */}
        <div className="p-4 border-t border-zinc-200 bg-white/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-zinc-900 flex items-center justify-center font-bold text-white shadow-md">
              AN
            </div>
            <div>
              <p className="text-sm font-bold text-zinc-900">Ananya</p>
              <p className="text-[10px] text-cyan-700 font-bold uppercase tracking-tighter">DTU Software Eng.</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative z-10">
        <header className="h-16 border-b border-zinc-200 flex items-center justify-between px-8 bg-white/60 backdrop-blur-xl">
          <div className="text-xs font-mono text-zinc-500 uppercase tracking-[0.2em]">
            Surgical Mode <span className="text-cyan-600 ml-2 animate-pulse">● Active</span>
          </div>
          <div className="flex items-center gap-6 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
            <span>Server: <span className="text-green-600">Online</span></span>
            <span>Model: <span className="text-zinc-900 font-mono">Flash-3.1</span></span>
          </div>
        </header>

        <div className="flex-1 overflow-auto p-8 relative">
          <Outlet />
        </div>
      </main>

    </div>
  );
}
