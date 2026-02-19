"use client";

import { useState, useEffect } from "react";
import { fetchTasks, scheduleTask, fetchFixedSchedules, createFixedSchedule, deleteFixedSchedule } from "@/lib/api";

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [fixedSchedules, setFixedSchedules] = useState<any[]>([]);
  const [newSchedule, setNewSchedule] = useState({
    title: "",
    category: "university",
    day_of_week: "Monday",
    start_time: "09:00",
    end_time: "10:00",
  });
  const [schedulingId, setSchedulingId] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [tasksData, fixedData] = await Promise.all([
        fetchTasks(),
        fetchFixedSchedules()
      ]);
      setTasks(tasksData);
      setFixedSchedules(fixedData);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleAddSchedule(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createFixedSchedule(newSchedule);
      setNewSchedule({
        title: "",
        category: "university",
        day_of_week: "Monday",
        start_time: "09:00",
        end_time: "10:00",
      });
      loadData();
    } catch (error) {
      console.error(error);
    }
  }

  async function handleDeleteSchedule(id: number) {
    try {
        await deleteFixedSchedule(id);
        loadData();
    } catch (error) {
        console.error(error);
    }
  }

  async function handleSchedule(taskId: number) {
    setSchedulingId(taskId);
    try {
        await scheduleTask(taskId);
        alert("Task scheduled successfully!");
        loadData();
    } catch (error: any) {
        alert(`Scheduling failed: ${error.message}`);
    } finally {
        setSchedulingId(null);
    }
  }

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  return (
    <div className="space-y-12">
      <div className="relative py-8 border-b border-slate-100 dark:border-slate-800">
        <div className="absolute top-0 left-0 text-[10px] font-mono text-cyan-500 tracking-widest">ID: TASKS & SCHEDULE</div>
        <h1 className="text-5xl font-light tracking-tight text-slate-900 dark:text-slate-100 uppercase">
          Schedule <span className="font-bold text-cyan-500">Management</span>
        </h1>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Fixed Schedule Editor */}
        <div className="lg:col-span-1 space-y-8">
            <div className="p-8 border border-slate-200 dark:border-slate-700 relative bg-slate-50/50 dark:bg-slate-900/50">
                <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-cyan-500"></div>
                <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-500"></div>
                <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-500"></div>
                <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-cyan-500"></div>
                
                <h2 className="text-sm font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-6">Fixed Weekly Schedule</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
                    Define your recurring classes, work shifts, and other fixed commitments. Ultron will schedule study sessions around these blocks.
                </p>
                
                <form onSubmit={handleAddSchedule} className="space-y-6">
                    <div>
                        <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Category</label>
                        <div className="flex gap-4">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input 
                                    type="radio" 
                                    name="category" 
                                    value="university"
                                    checked={newSchedule.category === 'university'}
                                    onChange={(e) => setNewSchedule({ ...newSchedule, category: e.target.value })}
                                    className="text-cyan-500 focus:ring-cyan-500"
                                />
                                <span className="text-sm text-slate-700 dark:text-slate-300">University</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input 
                                    type="radio" 
                                    name="category" 
                                    value="work"
                                    checked={newSchedule.category === 'work'}
                                    onChange={(e) => setNewSchedule({ ...newSchedule, category: e.target.value })}
                                    className="text-cyan-500 focus:ring-cyan-500"
                                />
                                <span className="text-sm text-slate-700 dark:text-slate-300">Work</span>
                            </label>
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Activity Name</label>
                        <input
                        type="text"
                        required
                        value={newSchedule.title}
                        onChange={(e) => setNewSchedule({ ...newSchedule, title: e.target.value })}
                        className="block w-full bg-white dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm text-slate-900 dark:text-slate-100 transition-colors placeholder-slate-300 dark:placeholder-slate-500"
                        placeholder="e.g. Math 101, Work"
                        />
                    </div>
                    
                    <div>
                        <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Day</label>
                        <select
                            value={newSchedule.day_of_week}
                            onChange={(e) => setNewSchedule({ ...newSchedule, day_of_week: e.target.value })}
                            className="block w-full bg-white dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm text-slate-900 dark:text-slate-100"
                        >
                            {days.map(day => <option key={day} value={day}>{day}</option>)}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">Start</label>
                            <input
                                type="time"
                                required
                                value={newSchedule.start_time}
                                onChange={(e) => setNewSchedule({ ...newSchedule, start_time: e.target.value })}
                                className="block w-full bg-white dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm text-slate-900 dark:text-slate-100"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-2">End</label>
                            <input
                                type="time"
                                required
                                value={newSchedule.end_time}
                                onChange={(e) => setNewSchedule({ ...newSchedule, end_time: e.target.value })}
                                className="block w-full bg-white dark:bg-slate-800 border-b border-slate-300 dark:border-slate-600 focus:border-cyan-500 focus:ring-0 px-0 py-2 text-sm text-slate-900 dark:text-slate-100"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="w-full py-3 bg-white dark:bg-slate-800 border border-cyan-500 text-cyan-500 text-xs font-bold uppercase tracking-widest hover:bg-cyan-500 hover:text-white transition-all"
                    >
                        Add Fixed Block
                    </button>
                </form>
            </div>
        </div>

        {/* Active Directives (Tasks) */}
        <div className="lg:col-span-2 space-y-12">
            <div>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-sm font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest">Active Directives</h2>
                    <div className="text-xs text-slate-500 dark:text-slate-400">{tasks.length} TASKS</div>
                </div>
                
                <div className="space-y-4">
                    {tasks.map((task) => (
                        <div key={task.id} className="group relative p-6 bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 hover:border-cyan-200 dark:hover:border-cyan-800 transition-all shadow-sm hover:shadow-md">
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className={`w-2 h-2 rounded-full ${
                                            task.status === 'completed' ? 'bg-green-400' : 
                                            task.status === 'scheduled' ? 'bg-cyan-400' : 'bg-amber-400'
                                        }`}></span>
                                        <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100">{task.title}</h3>
                                    </div>
                                    <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 font-mono">
                                        <span>EST: {task.total_required_time} MIN</span>
                                        <span>•</span>
                                        <span>DUE: {new Date(task.deadline).toLocaleDateString()}</span>
                                        {task.course_tag && (
                                            <>
                                                <span>•</span>
                                                <span className="text-cyan-600 dark:text-cyan-400">{task.course_tag}</span>
                                            </>
                                        )}
                                    </div>
                                </div>
                                
                                <div className="flex items-center gap-2">
                                    {task.status === 'pending' && (
                                        <button 
                                            onClick={() => handleSchedule(task.id)}
                                            disabled={schedulingId === task.id}
                                            className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-cyan-500 hover:text-cyan-500 transition-colors disabled:opacity-50"
                                        >
                                            {schedulingId === task.id ? "Processing..." : "Plan"}
                                        </button>
                                    )}
                                    <div className="text-xs font-bold uppercase tracking-wider text-slate-300 dark:text-slate-600">
                                        {task.status}
                                    </div>
                                </div>
                            </div>
                            
                            {/* Progress Bar */}
                            <div className="mt-4 h-1 w-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                                <div 
                                    className="h-full bg-cyan-400 transition-all duration-500"
                                    style={{ width: `${(task.scheduled_minutes / task.total_required_time) * 100}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                    
                    {tasks.length === 0 && (
                        <div className="p-12 border-2 border-dashed border-slate-100 dark:border-slate-800 text-center">
                            <p className="text-slate-400 dark:text-slate-500 text-sm">No active directives found.</p>
                            <p className="text-slate-300 dark:text-slate-600 text-xs mt-2">Initialize new tasks via the Neural Net interface.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* List of Fixed Schedules */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* University Section */}
                <div>
                    <h3 className="text-xs font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-wider mb-3 border-b border-cyan-100 dark:border-cyan-900 pb-1">University</h3>
                    <div className="space-y-2">
                        {fixedSchedules.filter(s => s.category === 'university' || !s.category).map((item) => (
                            <div key={item.id} className="flex items-center justify-between p-3 bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 hover:border-cyan-200 dark:hover:border-cyan-800 transition-colors border-l-4 border-l-cyan-500">
                                <div>
                                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase">{item.title}</div>
                                    <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
                                        {item.day_of_week} • {item.start_time} - {item.end_time}
                                    </div>
                                </div>
                                <button 
                                    onClick={() => handleDeleteSchedule(item.id)}
                                    className="text-slate-300 dark:text-slate-600 hover:text-red-500 transition-colors"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>
                        ))}
                        {fixedSchedules.filter(s => s.category === 'university' || !s.category).length === 0 && (
                            <div className="text-xs text-slate-400 dark:text-slate-500 italic">No classes scheduled.</div>
                        )}
                    </div>
                </div>

                {/* Work Section */}
                <div>
                    <h3 className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider mb-3 border-b border-amber-100 dark:border-amber-900 pb-1">Work</h3>
                    <div className="space-y-2">
                        {fixedSchedules.filter(s => s.category === 'work').map((item) => (
                            <div key={item.id} className="flex items-center justify-between p-3 bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800 hover:border-amber-200 dark:hover:border-amber-800 transition-colors border-l-4 border-l-amber-500">
                                <div>
                                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase">{item.title}</div>
                                    <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
                                        {item.day_of_week} • {item.start_time} - {item.end_time}
                                    </div>
                                </div>
                                <button 
                                    onClick={() => handleDeleteSchedule(item.id)}
                                    className="text-slate-300 dark:text-slate-600 hover:text-red-500 transition-colors"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>
                        ))}
                        {fixedSchedules.filter(s => s.category === 'work').length === 0 && (
                            <div className="text-xs text-slate-400 dark:text-slate-500 italic">No work shifts scheduled.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}

