import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, Plus, Save } from 'lucide-react';
import { cn } from '../components/AppShell';

interface Experiment {
  id: string;
  catalyst: string;
  status: string;
  result: string;
  notes?: string;
}

export function ExperimentLog() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeNotes, setActiveNotes] = useState<{[key: string]: string}>({});

  useEffect(() => {
    const fetchExperiments = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/experiments`);
        setExperiments(res.data.experiments);
        
        // Initialize local notes state
        const initialNotes: {[key: string]: string} = {};
        res.data.experiments.forEach((exp: Experiment) => {
          initialNotes[exp.id] = exp.notes || '';
        });
        setActiveNotes(initialNotes);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchExperiments();
  }, []);

  const handleNoteChange = (id: string, value: string) => {
    setActiveNotes(prev => ({ ...prev, [id]: value }));
  };

  if (loading) return <div className="text-cyan-600 font-mono p-10 animate-pulse">Accessing archives...</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between border-b border-zinc-200 pb-4">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-cyan-600" />
          <div>
            <h1 className="text-xl font-bold text-zinc-900">Experiment Log</h1>
            <p className="text-sm text-zinc-700">Historical records and researcher annotations</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-zinc-50 border-b border-zinc-200 text-[10px] uppercase font-bold text-zinc-500 tracking-widest">
              <th className="px-6 py-4">ID</th>
              <th className="px-6 py-4">Catalyst</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Result</th>
              <th className="px-6 py-4">Researcher Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {experiments.map((exp) => (
              <tr key={exp.id} className="hover:bg-zinc-50 transition-colors">
                <td className="px-6 py-4 font-mono text-xs text-zinc-600">{exp.id}</td>
                <td className="px-6 py-4 font-bold text-zinc-900">{exp.catalyst}</td>
                <td className="px-6 py-4">
                  <span className={cn(
                    "text-[10px] font-bold px-2 py-0.5 rounded-full border",
                    exp.status === 'success' ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"
                  )}>
                    {exp.status.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-zinc-700 font-mono">{exp.result}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <input 
                      type="text" 
                      value={activeNotes[exp.id]}
                      onChange={(e) => handleNoteChange(exp.id, e.target.value)}
                      placeholder="Add observation..."
                      className="flex-1 bg-white border border-zinc-200 rounded px-2 py-1.5 text-xs text-zinc-900 focus:outline-none focus:border-cyan-500"
                    />
                    <button className="p-1.5 text-zinc-400 hover:text-cyan-600 transition-colors">
                      <Save className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
