import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { GitFork, ShieldAlert, Zap } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { MoleculeViewer } from '../components/MoleculeViewer';

interface PredictionResult {
  catalyst: string;
  predicted_activity: number;
  predicted_selectivity: number;
  confidence: number;
  energy_ev: number;
  recommendation: string;
}

export function Prediction() {
  const [catalyst, setCatalyst] = useState('Cu-Zn/SiO2');
  const [temp, setTemp] = useState(330);
  const [pressure, setPressure] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);

  const runSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/predict`, {
        catalyst,
        temperature: temp,
        pressure,
        reaction: "EtOH→Jet"
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert('Failed to run simulation. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // Generate a synthetic reaction coordinate curve based on the predicted energy
  const chartData = useMemo(() => {
    if (!result) return [];
    const peak = result.energy_ev;
    // Simple interpolation curve: Reactants -> Transition State -> Products
    return [
      { step: 'Reactants', energy: 0.0 },
      { step: 'RC-1', energy: peak * 0.3 },
      { step: 'RC-2', energy: peak * 0.7 },
      { step: 'TS', energy: peak },
      { step: 'RC-3', energy: peak * 0.8 },
      { step: 'RC-4', energy: peak * 0.4 },
      { step: 'Products', energy: -0.5 }, // Assuming exothermic product state
    ];
  }, [result]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="flex items-center gap-3 border-b border-zinc-800 pb-4">
        <GitFork className="w-6 h-6 text-cyan-500" />
        <div>
          <h1 className="text-xl font-bold text-zinc-900">Prediction Engine</h1>
          <p className="text-sm text-zinc-700">GradientBoost-E2J Virtual Screening & Structural Analysis</p>
        </div>
      </div>

      {/* Top Row: Input & 3D Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Input Form */}
        <div className="bg-zinc-50/50 border border-zinc-800 rounded-lg p-6 backdrop-blur-md flex flex-col justify-between">
          <form onSubmit={runSimulation} className="space-y-5 flex-1">
            <div>
              <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Catalyst Configuration</label>
              <input 
                type="text" 
                value={catalyst}
                onChange={(e) => setCatalyst(e.target.value)}
                className="w-full bg-white border border-zinc-800 rounded px-4 py-2.5 text-zinc-800 font-mono focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
                placeholder="e.g. Cu-Zn/SiO2"
              />
            </div>
            
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs uppercase tracking-wider text-zinc-500">Temperature</label>
                <span className="font-mono text-cyan-700 text-sm">{temp}°C</span>
              </div>
              <input 
                type="range" 
                min="150" max="450" step="5"
                value={temp}
                onChange={(e) => setTemp(Number(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-zinc-500 mb-2">Pressure (bar)</label>
              <select 
                value={pressure}
                onChange={(e) => setPressure(Number(e.target.value))}
                className="w-full bg-white border border-zinc-800 rounded px-4 py-2.5 text-zinc-800 font-mono focus:outline-none focus:border-cyan-500 transition-all"
              >
                <option value={1}>1.0</option>
                <option value={5}>5.0</option>
                <option value={10}>10.0</option>
                <option value={15}>15.0</option>
              </select>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-cyan-500/10 text-cyan-700 border border-cyan-500/50 rounded py-3 mt-4 hover:bg-cyan-500 hover:text-zinc-950 font-medium transition-all flex justify-center items-center gap-2"
            >
              {loading ? <span className="animate-pulse">Computing...</span> : <><Zap className="w-4 h-4" /> Run Simulation</>}
            </button>
          </form>
          
          {result && (
            <div className="mt-6 p-3 bg-white border border-zinc-800 rounded text-sm text-zinc-800 font-mono flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <span>{result.recommendation}</span>
            </div>
          )}
        </div>

        {/* 3D Molecule Viewer */}
        <div className="bg-zinc-50/50 border border-zinc-800 rounded-lg p-6 backdrop-blur-md flex flex-col">
          <h2 className="text-sm font-semibold text-zinc-700 uppercase tracking-wider mb-4">Molecular Structure (Ethanol)</h2>
          <div className="flex-1 min-h-[300px]">
            <MoleculeViewer />
          </div>
        </div>

      </div>

      {/* Bottom Row: Energy Profile AreaChart */}
      <div className="bg-zinc-50/50 border border-zinc-800 rounded-lg p-6 backdrop-blur-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-sm font-semibold text-zinc-700 uppercase tracking-wider">Reaction Energy Profile (ΔG)</h2>
          {result && <span className="font-mono text-cyan-700 text-lg font-bold">Peak: {result.energy_ev} eV</span>}
        </div>
        
        <div className="h-[300px] w-full font-mono text-xs">
          {result ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                <defs>
                  <linearGradient id="colorEnergy" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis 
                  dataKey="step" 
                  stroke="#71717a" 
                  tick={{ fill: '#a1a1aa' }} 
                />
                <YAxis 
                  stroke="#71717a" 
                  tick={{ fill: '#a1a1aa' }} 
                  domain={[-1, 'auto']}
                  label={{ value: 'Energy (eV)', angle: -90, position: 'insideLeft', fill: '#71717a' }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '4px', color: '#e4e4e7' }}
                  itemStyle={{ color: '#06b6d4', fontWeight: 'bold' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="energy" 
                  stroke="#06b6d4" 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorEnergy)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center border border-zinc-800/50 rounded-lg bg-white">
               <div className="text-zinc-600 font-mono">Awaiting input to generate curve...</div>
            </div>
          )}
        </div>
        
        {/* Metric Summary */}
        {result && (
           <div className="mt-6 flex justify-around gap-6 pt-6 border-t border-zinc-800">
              <div className="text-center">
                <p className="text-[10px] text-zinc-500 uppercase">Predicted Activity</p>
                <p className="text-2xl font-mono text-zinc-900">{result.predicted_activity}%</p>
              </div>
              <div className="text-center">
                <p className="text-[10px] text-zinc-500 uppercase">Predicted Selectivity</p>
                <p className="text-2xl font-mono text-zinc-900">{result.predicted_selectivity}%</p>
              </div>
              <div className="text-center">
                <p className="text-[10px] text-zinc-500 uppercase">Model Confidence</p>
                <p className="text-2xl font-mono text-cyan-700">±{result.confidence}</p>
              </div>
           </div>
        )}
      </div>

    </div>
  );
}
