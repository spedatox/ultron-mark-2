"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { fetchEvents, fetchConflicts } from "@/lib/api";

export default function Home() {
  const [events, setEvents] = useState<any[]>([]);
  const [conflicts, setConflicts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const now = new Date();
      const start = new Date(now.setHours(0, 0, 0, 0)).toISOString();
      const end = new Date(now.setHours(23, 59, 59, 999)).toISOString();
      
      const [eventsData, conflictsData] = await Promise.all([
        fetchEvents(start, end),
        fetchConflicts()
      ]);
      
      setEvents(eventsData);
      setConflicts(conflictsData);
    } catch (err) {
      console.error(err);
      setError("Could not load data. Is Google Calendar connected?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-12">
      {/* Header Section */}
      <div className="relative py-8 border-b border-slate-100 dark:border-slate-800">
        <div className="absolute top-0 left-0 text-[10px] font-mono text-cyan-500 tracking-widest">ID: DASHBOARD</div>
        <h1 className="text-5xl font-light tracking-tight text-slate-900 dark:text-slate-100 uppercase">
          <span className="font-bold text-cyan-500">System</span> Overview
        </h1>
        <p className="mt-2 text-sm font-mono text-slate-400 dark:text-slate-500 tracking-widest uppercase">
          Academic Timekeeper Module Active
        </p>
        
        {/* Quick Actions */}
        <div className="absolute right-0 bottom-8 flex gap-4">
             <Link
            href="/tasks"
            className="group relative inline-flex items-center justify-center px-6 py-2 overflow-hidden font-medium text-cyan-600 dark:text-cyan-400 transition duration-300 ease-out border border-cyan-500 rounded-none hover:text-white"
          >
            <span className="absolute inset-0 w-full h-full bg-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-out"></span>
            <span className="relative uppercase tracking-widest text-xs">Manage Tasks</span>
          </Link>
          <Link
            href="/settings"
            className="group relative inline-flex items-center justify-center px-6 py-2 overflow-hidden font-medium text-slate-500 dark:text-slate-400 transition duration-300 ease-out border border-slate-300 dark:border-slate-600 rounded-none hover:text-slate-900 dark:hover:text-white hover:border-slate-900 dark:hover:border-slate-400"
          >
            <span className="relative uppercase tracking-widest text-xs">Settings</span>
          </Link>
        </div>
      </div>

      {/* Conflicts Alert */}
      {conflicts.length > 0 && (
        <div className="relative bg-red-50/50 dark:bg-red-950/20 border-l-2 border-red-500 p-6">
            <div className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full animate-ping"></div>
            <div className="flex items-start gap-4">
                <div className="text-red-500 font-mono text-xs uppercase tracking-widest mt-1">Warning</div>
                <div>
                    <h3 className="text-lg font-medium text-red-900 dark:text-red-400 uppercase tracking-wide">
                        Scheduling Conflicts Detected
                    </h3>
                    <div className="mt-2 text-sm text-red-700 dark:text-red-300 font-light">
                        <ul className="space-y-1">
                            {conflicts.map((c, i) => (
                                <li key={i} className="flex items-center gap-2">
                                    <span className="w-1 h-1 bg-red-400 rounded-full"></span>
                                    "{c.task_title}" overlaps with "{c.conflict_with}"
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
      )}

      {/* Schedule Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Left Column: Status */}
        <div className="lg:col-span-1 space-y-8">
            <div className="p-6 border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/50 relative overflow-hidden group hover:border-cyan-200 dark:hover:border-cyan-800 transition-colors">
                <div className="absolute top-0 right-0 p-2">
                    <div className={`w-3 h-3 rounded-full border-2 ${loading ? 'border-yellow-400 animate-pulse' : error ? 'border-red-500' : 'border-cyan-400'}`}></div>
                </div>
                <h3 className="text-xs font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-4">System Status</h3>
                <div className="text-4xl font-light text-slate-900 dark:text-slate-100">
                    {loading ? "SYNCING..." : error ? "ERROR" : "ONLINE"}
                </div>
                <div className="mt-4 text-xs text-slate-400 dark:text-slate-500 font-mono">
                    LAST SYNC: {new Date().toLocaleTimeString()}
                </div>
            </div>
            
            <div className="p-6 border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900/50 relative">
                 <h3 className="text-xs font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-4">Date</h3>
                 <div className="text-6xl font-thin text-slate-900 dark:text-slate-100">
                    {new Date().getDate()}
                 </div>
                 <div className="text-xl font-light text-cyan-500 uppercase tracking-widest mt-2">
                    {new Date().toLocaleDateString('en-US', { month: 'long' })}
                 </div>
                 <div className="text-sm font-mono text-slate-400 dark:text-slate-500 mt-1">
                    {new Date().toLocaleDateString('en-US', { weekday: 'long' })}
                 </div>
            </div>
        </div>

        {/* Right Column: Timeline */}
        <div className="lg:col-span-2">
          <div className="flex justify-between items-end mb-6 border-b border-slate-100 dark:border-slate-800 pb-2">
            <h3 className="text-lg font-light uppercase tracking-widest text-slate-900 dark:text-slate-100">
              Today's Timeline
            </h3>
            <span className="text-xs font-mono text-cyan-500">
                {events.length} EVENTS
            </span>
          </div>
          
          <div className="relative">
            {/* Vertical Line */}
            <div className="absolute left-2 top-0 bottom-0 w-px bg-slate-100 dark:bg-slate-800"></div>

            {loading ? (
              <div className="py-12 text-center">
                  <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
                  <p className="mt-4 text-xs font-mono text-cyan-500 uppercase tracking-widest">Loading Data...</p>
              </div>
            ) : error ? (
              <div className="py-12 text-center text-red-500 font-mono text-sm">{error}</div>
            ) : events.length === 0 ? (
              <div className="py-12 pl-8 text-slate-400 dark:text-slate-500 font-light italic">No events scheduled for today.</div>
            ) : (
              <ul className="space-y-6 pl-8">
                {events.map((event, idx) => {
                    const start = new Date(event.start.dateTime || event.start.date);
                    const end = new Date(event.end.dateTime || event.end.date);
                    const isUltron = event.description?.includes("Ultron");
                    const isPast = end < new Date();
                    
                    return (
                        <li key={event.id || idx} className={`relative group ${isPast ? 'opacity-50 grayscale' : ''}`}>
                            {/* Dot on line */}
                            <div className={`absolute -left-[29px] top-2 w-3 h-3 rounded-full border-2 bg-white dark:bg-slate-900 transition-colors ${isUltron ? 'border-cyan-400 group-hover:bg-cyan-400' : 'border-slate-300 dark:border-slate-600 group-hover:bg-slate-300 dark:group-hover:bg-slate-600'}`}></div>
                            
                            <div className={`p-4 border-l-2 transition-all duration-300 ${isUltron ? 'border-cyan-400 bg-cyan-50/30 dark:bg-cyan-950/20 hover:bg-cyan-50 dark:hover:bg-cyan-950/30' : 'border-transparent hover:border-slate-200 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50'}`}>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <span className="font-mono text-xs text-slate-400 dark:text-slate-500">
                                                {start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                            </span>
                                            <h4 className={`text-sm font-medium uppercase tracking-wide ${isUltron ? 'text-cyan-900 dark:text-cyan-300' : 'text-slate-900 dark:text-slate-100'}`}>
                                                {event.summary}
                                            </h4>
                                        </div>
                                        <div className="mt-1 pl-[4.5rem] text-xs text-slate-500 dark:text-slate-400 font-light">
                                            Duration: {Math.round((end.getTime() - start.getTime()) / 60000)} min
                                        </div>
                                    </div>
                                    {isUltron && (
                                        <span className="px-2 py-1 text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800">
                                            Ultron
                                        </span>
                                    )}
                                </div>
                            </div>
                        </li>
                    );
                })}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
