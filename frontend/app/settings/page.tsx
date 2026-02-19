"use client";

import { useState, useEffect, Suspense } from "react";
import { fetchPreferences, updatePreferences, getAuthUrl, getAuthStatus, clearAllChatHistory } from "@/lib/api";
import { useSearchParams } from "next/navigation";

function SettingsContent() {
  const [preferences, setPreferences] = useState({
    wake_time: "08:00",
    sleep_time: "23:00",
    study_block_length: 50,
    max_study_minutes_per_day: 240,
  });
  const [loading, setLoading] = useState(true);
  const [isConnected, setConnected] = useState(false);
  const [authStatus, setAuthStatus] = useState<string>("none");
  const [authMessage, setAuthMessage] = useState<string>("");
  const searchParams = useSearchParams();

  useEffect(() => {
    loadData();
    if (searchParams.get("connected") === "true") {
        setConnected(true);
        setAuthStatus("valid");
    }
  }, [searchParams]);

  async function loadData() {
    try {
      const [prefData, authData] = await Promise.all([
        fetchPreferences(),
        getAuthStatus()
      ]);
      
      if (prefData) {
        setPreferences({
            wake_time: prefData.wake_time,
            sleep_time: prefData.sleep_time,
            study_block_length: prefData.study_block_length,
            max_study_minutes_per_day: prefData.max_study_minutes_per_day
        });
      }
      setConnected(authData.connected);
      setAuthStatus(authData.status || "none");
      setAuthMessage(authData.message || "");
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect() {
    try {
        const data = await getAuthUrl();
        window.location.href = data.url;
    } catch (error) {
        alert("Error connecting to Google Calendar. Check backend logs (credentials.json missing?)");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await updatePreferences(preferences);
      alert("Preferences updated!");
    } catch (error) {
      console.error(error);
      alert("Failed to update preferences");
    }
  }

  if (loading) return <div className="text-center py-12 font-mono text-cyan-500 animate-pulse">LOADING SYSTEM CONFIG...</div>;

  return (
    <div className="space-y-12">
      <div className="relative py-8 border-b border-slate-100 dark:border-slate-800">
        <div className="absolute top-0 left-0 text-[10px] font-mono text-cyan-500 tracking-widest">ID: SETTINGS</div>
        <h1 className="text-5xl font-light tracking-tight text-slate-900 dark:text-slate-100 uppercase">
          System <span className="font-bold text-cyan-500">Configuration</span>
        </h1>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Google Calendar Integration */}
        <div className="p-8 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50 relative group hover:border-cyan-200 dark:hover:border-cyan-800 transition-colors">
            <div className="absolute top-0 right-0 p-2">
                <div className={`w-2 h-2 rounded-full ${isConnected && authStatus === 'valid' ? 'bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)]' : authStatus === 'expired' ? 'bg-amber-400' : 'bg-slate-300 dark:bg-slate-600'}`}></div>
            </div>
            
            <h2 className="text-sm font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-6">External Integrations</h2>
            
            <div className="flex items-center justify-between mb-4">
                <div>
                    <p className="text-lg font-medium text-slate-900 dark:text-slate-100 uppercase tracking-wide">Google Calendar</p>
                    <p className={`text-xs font-mono mt-1 ${isConnected && authStatus === 'valid' ? 'text-cyan-600 dark:text-cyan-400' : authStatus === 'expired' ? 'text-amber-600 dark:text-amber-400' : 'text-slate-400 dark:text-slate-500'}`}>
                        STATUS: {authStatus === 'valid' ? 'CONNECTED' : authStatus === 'expired' ? 'TOKEN EXPIRED' : 'DISCONNECTED'}
                    </p>
                </div>
                {(!isConnected || authStatus === 'expired') ? (
                    <button
                        onClick={handleConnect}
                        className="px-4 py-2 border border-cyan-500 text-cyan-600 dark:text-cyan-400 text-xs font-bold uppercase tracking-widest hover:bg-cyan-50 dark:hover:bg-cyan-900/20 transition-colors"
                    >
                        {authStatus === 'expired' ? 'Reconnect' : 'Connect'}
                    </button>
                ) : (
                     <span className="px-4 py-2 border border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-500 text-xs font-bold uppercase tracking-widest cursor-not-allowed">
                        Linked
                    </span>
                )}
            </div>
            
            {authMessage && authStatus === 'expired' && (
                <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 text-xs font-mono">
                    ⚠️ {authMessage}
                </div>
            )}
            
            <div className="text-xs text-slate-400 dark:text-slate-500 font-light leading-relaxed">
                Connecting allows Ultron to read existing events and write study blocks directly to your primary calendar.
            </div>
        </div>

        {/* Study Preferences */}
        <div className="p-8 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50 relative">
            <h2 className="text-sm font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-6">Chronometrics</h2>
            
            <form onSubmit={handleSubmit} className="space-y-8">
                <div className="grid grid-cols-2 gap-8">
                    <div>
                        <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Wake Time</label>
                        <input
                            type="time"
                            value={preferences.wake_time}
                            onChange={(e) => setPreferences({ ...preferences, wake_time: e.target.value })}
                            className="block w-full bg-slate-50 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm font-mono text-slate-900 dark:text-slate-100 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Sleep Time</label>
                        <input
                            type="time"
                            value={preferences.sleep_time}
                            onChange={(e) => setPreferences({ ...preferences, sleep_time: e.target.value })}
                            className="block w-full bg-slate-50 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm font-mono text-slate-900 dark:text-slate-100 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Block Length (Min)</label>
                        <input
                            type="number"
                            value={preferences.study_block_length}
                            onChange={(e) => setPreferences({ ...preferences, study_block_length: parseInt(e.target.value) })}
                            className="block w-full bg-slate-50 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm font-mono text-slate-900 dark:text-slate-100 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Max Daily (Min)</label>
                        <input
                            type="number"
                            value={preferences.max_study_minutes_per_day}
                            onChange={(e) => setPreferences({ ...preferences, max_study_minutes_per_day: parseInt(e.target.value) })}
                            className="block w-full bg-slate-50 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm font-mono text-slate-900 dark:text-slate-100 transition-colors"
                        />
                    </div>
                </div>

                <div className="flex justify-end pt-4">
                    <button
                    type="submit"
                    className="group relative inline-flex items-center justify-center px-8 py-3 overflow-hidden font-medium text-cyan-600 dark:text-cyan-400 transition duration-300 ease-out border border-cyan-500 rounded-none hover:text-white"
                    >
                    <span className="absolute inset-0 w-full h-full bg-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-out"></span>
                    <span className="relative uppercase tracking-widest text-xs font-bold">Save Configuration</span>
                    </button>
                </div>
            </form>
        </div>

        {/* Memory Management */}
        <div className="p-8 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50 relative group hover:border-red-200 dark:hover:border-red-800 transition-colors lg:col-span-2">
            <h2 className="text-sm font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-6">Memory Management</h2>
            
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-lg font-medium text-slate-900 dark:text-slate-100 uppercase tracking-wide">Clear All Memory</p>
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                        This will delete all chat history and reset Ultron's long-term memory. This action cannot be undone.
                    </p>
                </div>
                <button
                    onClick={async () => {
                        if (confirm("Are you sure you want to clear all chat history and memory? This cannot be undone.")) {
                            try {
                                const result = await clearAllChatHistory();
                                alert(`Memory cleared! ${result.sessions_deleted} chat sessions deleted.`);
                            } catch (error) {
                                console.error(error);
                                alert("Failed to clear memory");
                            }
                        }
                    }}
                    className="px-4 py-2 border border-red-500 text-red-600 dark:text-red-400 text-xs font-bold uppercase tracking-widest hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                    Clear Memory
                </button>
            </div>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="text-center py-12 font-mono text-cyan-500 animate-pulse">LOADING SYSTEM CONFIG...</div>}>
      <SettingsContent />
    </Suspense>
  );
}
