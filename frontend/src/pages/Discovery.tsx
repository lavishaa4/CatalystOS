import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Beaker } from 'lucide-react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Candidate {
  id: number;
  name: string;
  activity: number;
  selectivity: number;
  stability: number;
  source: string;
}

export function Discovery() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState('Standard');

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/candidates`);
        setCandidates(res.data.candidates);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, []);

  if (loading) return <div className="text-cyan-500 font-mono p-10">Fetching candidates...</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between border-b border-zinc-200 pb-4">
        <div className="flex items-center gap-3">
          <Beaker className="w-6 h-6 text-cyan-600" />
          <div>
            <h1 className="text-xl font-bold text-zinc-900">Candidate Discovery</h1>
            <p className="text-sm text-zinc-700">Library of generated and sourced catalysts</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Configuration:</label>
          <select 
            value={config}
            onChange={(e) => setConfig(e.target.value)}
            className="bg-white border border-zinc-200 rounded px-3 py-1.5 text-sm text-zinc-900 focus:outline-none focus:border-cyan-500 transition-all shadow-sm"
          >
            <option>Standard</option>
            <option>High Pressure</option>
            <option>Low Temp</option>
            <option>Synergy Focus</option>
          </select>
        </div>
      </div>

      {/* Analytics Chart */}
      <div className="bg-zinc-50/50 border border-zinc-800 rounded-lg p-6 backdrop-blur-md">
        <h2 className="text-sm font-semibold text-zinc-700 uppercase tracking-wider mb-6">Activity vs. Selectivity Landscape</h2>
        <div className="h-[300px] w-full font-mono text-xs">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis 
                type="number" 
                dataKey="activity" 
                name="Activity" 
                unit="%" 
                domain={[30, 100]}
                stroke="#71717a"
                tick={{ fill: '#a1a1aa' }}
                label={{ value: 'Activity (%)', position: 'insideBottom', offset: -10, fill: '#71717a' }}
              />
              <YAxis 
                type="number" 
                dataKey="selectivity" 
                name="Selectivity" 
                unit="%" 
                domain={[30, 100]}
                stroke="#71717a"
                tick={{ fill: '#a1a1aa' }}
                label={{ value: 'Selectivity (%)', angle: -90, position: 'insideLeft', fill: '#71717a' }}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3', stroke: '#06b6d4' }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white border border-zinc-800 p-3 rounded shadow-xl">
                        <p className="text-cyan-700 font-bold mb-1">{data.name}</p>
                        <p className="text-zinc-800">Activity: {data.activity}%</p>
                        <p className="text-zinc-800">Selectivity: {data.selectivity}%</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter name="Candidates" data={candidates} fill="#06b6d4" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        {candidates.map((c) => (
          <div key={c.id} className="bg-zinc-50/50 border border-zinc-800 rounded-lg p-5 backdrop-blur-md hover:border-cyan-500/50 transition-colors group">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-mono font-bold text-zinc-900 group-hover:text-cyan-700 transition-colors">{c.name}</h3>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border border-blue-200 bg-blue-50 text-blue-700 shadow-sm">
                {c.source}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-zinc-700 uppercase">Activity</span>
                  <span className="font-mono text-zinc-800">{c.activity}%</span>
                </div>
                <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]" style={{ width: `${c.activity}%` }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-zinc-700 uppercase">Selectivity</span>
                  <span className="font-mono text-zinc-800">{c.selectivity}%</span>
                </div>
                <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500" style={{ width: `${c.selectivity}%` }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-zinc-700 uppercase">Stability</span>
                  <span className="font-mono text-zinc-800">{c.stability}%</span>
                </div>
                <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500" style={{ width: `${c.stability}%` }}></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
