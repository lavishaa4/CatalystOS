import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { AlertTriangle, Database } from 'lucide-react';
import { cn } from '../components/AppShell';

interface GapPattern {
  metal_family: string;
  experiments_affected: number;
  avg_gap_pct: number;
  dominant_direction: string;
  hypothesis: string;
}

interface IndividualGap {
  exp_id: string;
  catalyst: string;
  base_metal: string;
  temp: number;
  pressure: number;
  predicted: number;
  actual: number;
  gap: number;
  direction: string;
}

export function GapIntelligence() {
  const [patterns, setPatterns] = useState<GapPattern[]>([]);
  const [individualGaps, setIndividualGaps] = useState<IndividualGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const fetchGaps = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/gaps`);
        setPatterns(res.data.systematic_patterns);
        setIndividualGaps(res.data.individual_gaps);
        setTotal(res.data.total_gaps);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchGaps();
  }, []);

  // Generate 10x10 Heatmap Grid Data
  const heatmapData = useMemo(() => {
    const temps = [150, 180, 210, 240, 270, 300, 330, 360, 390, 420];
    const pressures = [1.0, 2.4, 3.8, 5.2, 6.6, 8.0, 9.4, 10.8, 12.2, 13.6];
    
    // Create 10x10 matrix initialized with nulls
    const grid: { temp: number; pressure: number; gap: number | null }[][] = [];
    
    // We want Y-axis to be pressure (descending visually from top to bottom, or ascending)
    // We'll map rows to Pressure (top is 15, bottom is 1)
    for (let pIdx = 9; pIdx >= 0; pIdx--) {
      const row = [];
      const pMin = pressures[pIdx];
      const pMax = pIdx === 9 ? 16 : pressures[pIdx + 1];
      
      for (let tIdx = 0; tIdx < 10; tIdx++) {
        const tMin = temps[tIdx];
        const tMax = tIdx === 9 ? 460 : temps[tIdx + 1];
        
        // Find if any gap falls in this cell
        const matchingGaps = individualGaps.filter(
          g => g.temp >= tMin && g.temp < tMax && g.pressure >= pMin && g.pressure < pMax
        );
        
        // If multiple, average them
        let avgGap = null;
        if (matchingGaps.length > 0) {
          avgGap = matchingGaps.reduce((sum, g) => sum + g.gap, 0) / matchingGaps.length;
        }
        
        row.push({ temp: tMin, pressure: pMin, gap: avgGap });
      }
      grid.push(row);
    }
    
    return { grid, temps, pressures };
  }, [individualGaps]);

  const getHeatmapColor = (gap: number | null) => {
    if (gap === null) return "bg-zinc-50 border-zinc-800";
    if (gap > 15) return "bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.6)] z-10 border-red-400";
    if (gap > 10) return "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.6)] z-10 border-amber-400";
    return "bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.6)] z-10 border-cyan-400";
  };

  if (loading) return <div className="text-cyan-500 font-mono p-10">Scanning experiment logs...</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-500" />
          <div>
            <h1 className="text-xl font-bold text-zinc-900">Gap Intelligence</h1>
            <p className="text-sm text-zinc-700">Systematic Failure Pattern Detection</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-mono text-zinc-900">{total}</div>
          <div className="text-xs text-zinc-500 uppercase tracking-wider">Total Gaps Logged</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        {/* Heatmap Section */}
        <div className="bg-zinc-50/50 border border-zinc-800 rounded-lg p-6 backdrop-blur-md">
          <h2 className="text-sm font-semibold text-zinc-700 uppercase tracking-wider mb-6">Prediction Error Heatmap (T vs P)</h2>
          
          <div className="flex">
            {/* Y-axis labels (Pressure) */}
            <div className="flex flex-col justify-between pr-4 py-2 font-mono text-[10px] text-zinc-500 h-[300px]">
              {heatmapData.pressures.slice().reverse().filter((_, i) => i % 2 === 0).map(p => (
                <span key={p}>{p.toFixed(1)} bar</span>
              ))}
              <span>1.0 bar</span>
            </div>
            
            {/* Heatmap Grid */}
            <div className="flex-1 flex flex-col h-[300px] border border-zinc-800/50 bg-white p-1 rounded gap-1 relative">
              {heatmapData.grid.map((row, rIdx) => (
                <div key={rIdx} className="flex-1 flex gap-1">
                  {row.map((cell, cIdx) => (
                    <div 
                      key={cIdx} 
                      className={cn(
                        "flex-1 rounded border transition-all duration-300 relative group",
                        getHeatmapColor(cell.gap)
                      )}
                    >
                      {/* Tooltip */}
                      {cell.gap !== null && (
                        <div className="absolute opacity-0 group-hover:opacity-100 bottom-full left-1/2 -translate-x-1/2 mb-2 bg-zinc-50 border border-zinc-700 text-zinc-900 text-xs p-2 rounded shadow-xl pointer-events-none z-50 whitespace-nowrap font-mono">
                          Temp: {cell.temp}°C<br/>
                          Pressure: {cell.pressure.toFixed(1)} bar<br/>
                          Gap: <span className="text-amber-400">{cell.gap.toFixed(1)}%</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
          
          {/* X-axis labels (Temperature) */}
          <div className="flex justify-between pl-14 pr-2 mt-3 font-mono text-[10px] text-zinc-500">
            {heatmapData.temps.filter((_, i) => i % 2 === 0).map(t => (
              <span key={t}>{t}°C</span>
            ))}
            <span>450°C</span>
          </div>
          
          <div className="mt-6 flex items-center justify-center gap-6 text-xs font-mono text-zinc-700">
             <div className="flex items-center gap-2"><div className="w-3 h-3 bg-zinc-50 border border-zinc-800 rounded"></div> No Data</div>
             <div className="flex items-center gap-2"><div className="w-3 h-3 bg-amber-500 shadow-[0_0_5px_rgba(245,158,11,0.6)] rounded"></div> &gt; 10% Gap</div>
             <div className="flex items-center gap-2"><div className="w-3 h-3 bg-red-500 shadow-[0_0_5px_rgba(239,68,68,0.6)] rounded"></div> &gt; 15% Gap</div>
          </div>
        </div>

        {/* Hypotheses Section */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-zinc-700 uppercase tracking-wider mb-2">AI Diagnostic Hypotheses</h2>
          {patterns.map((p, idx) => {
            const isSevere = p.hypothesis.includes("[Severe]");
            return (
              <div key={idx} className={cn(
                "border rounded-lg p-5 transition-all relative overflow-hidden backdrop-blur-md",
                isSevere 
                  ? "bg-red-500/5 border-red-500/30" 
                  : "bg-amber-500/5 border-amber-500/30"
              )}>
                <div className={cn(
                  "absolute top-0 left-0 w-1 h-full",
                  isSevere ? "bg-red-500" : "bg-amber-500"
                )}></div>
                <div className="flex justify-between items-start ml-2">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h2 className="text-lg font-bold text-zinc-900 font-mono">{p.metal_family} Family</h2>
                      <span className={cn(
                        "text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border",
                        isSevere ? "bg-red-500/20 text-red-400 border-red-500/30" : "bg-amber-500/20 text-amber-400 border-amber-500/30"
                      )}>
                        {isSevere ? 'Severe Gap' : 'Moderate Gap'}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-700 mb-4 flex items-center gap-2">
                      <Database className="w-3.5 h-3.5" /> Affected {p.experiments_affected} experiments
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-mono text-zinc-900">{p.avg_gap_pct}%</div>
                    <div className="text-xs text-zinc-500 uppercase tracking-wider">{p.dominant_direction}</div>
                  </div>
                </div>
                <div className="ml-2 mt-2 p-3 bg-white border border-zinc-800 rounded font-mono text-sm text-zinc-800">
                  <span className="text-zinc-500 mr-2">AI_HYPOTHESIS:</span> 
                  {p.hypothesis.replace("[Severe] ", "").replace("[Moderate] ", "")}
                </div>
              </div>
            )
          })}
          {patterns.length === 0 && (
            <div className="text-center p-10 border border-zinc-800 rounded bg-zinc-50/30 text-zinc-500 font-mono">
              No systematic gaps detected in the current training cycle.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
