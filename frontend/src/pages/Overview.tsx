import React, { useEffect, useState } from 'react';
import { Download, LayoutDashboard, Terminal } from 'lucide-react';
import axios from 'axios';
import { cn } from '../components/AppShell';

interface PipelineStage {
  id: number;
  stage: string;
  product: string;
  catalyst: string;
  condition: string;
  status: 'Optimized' | 'Active' | 'Optimizing' | 'Pending';
}

interface ActivityItem {
  time: string;
  message: string;
}

interface TopCandidate {
  name: string;
  score: number;
  ai_tag: boolean;
}

interface DashboardData {
  pipeline: PipelineStage[];
  activity_log: ActivityItem[];
  top_candidates: TopCandidate[];
}

export function Overview() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/dashboard`);
        setData(response.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      }
    };
    fetchDashboard();
  }, []);

  const handleDownload = () => {
    if (!data) return;

    let markdown = `# CatalystOS Research Report\n`;
    markdown += `Generated: ${new Date().toLocaleString()}\n\n`;
    markdown += `## System Status\n- **Status:** Online\n- **Model:** Flash-3.1\n\n`;
    
    markdown += `## Top AI Candidates\n`;
    data.top_candidates.forEach(cat => {
      markdown += `- **${cat.name}:** ${cat.score}% ${cat.ai_tag ? '(AI Generated)' : ''}\n`;
    });
    
    markdown += `\n## Recent Activity Log\n`;
    data.activity_log.forEach(log => {
      markdown += `- [${log.time}] ${log.message}\n`;
    });

    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `catalystos-report-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!data) return <div className="text-cyan-600 font-mono p-10 animate-pulse">Initializing Overview Engine...</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">

      {/* Header Section */}
      <div className="flex items-center justify-between border-b border-zinc-200 pb-5">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-50 rounded-lg">
            <LayoutDashboard className="w-6 h-6 text-cyan-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-zinc-950 tracking-tight">System Overview</h1>
            <p className="text-sm text-zinc-500 font-medium">Real-time telemetry and catalyst pipeline status</p>
          </div>
        </div>

        <button
          onClick={handleDownload}
          className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md active:scale-95"
        >
          <Download className="w-4 h-4" />
          <span>Export Research Data</span>
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

        {/* Left Column: Reaction Pipeline */}
        <div className="xl:col-span-2 space-y-6">
          <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-xs font-bold text-zinc-400 uppercase tracking-[0.2em] mb-8">Current Reaction Pipeline</h2>

            {/* FIX: Timeline Line contrast adjusted from zinc-800 to zinc-200 */}
            <div className="space-y-8 relative before:absolute before:inset-0 before:ml-[11px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-zinc-200">
              {data.pipeline.map((stage) => (
                <div key={stage.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">

                  {/* Status Marker */}
                  <div className={cn(
                    "z-10 flex items-center justify-center w-6 h-6 rounded-full border-2 bg-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm",
                    stage.status === 'Optimized' ? "border-green-500" :
                      stage.status === 'Active' ? "border-cyan-500" :
                        stage.status === 'Optimizing' ? "border-amber-500" :
                          "border-zinc-300"
                  )}>
                    {stage.status === 'Active' && <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>}
                    {stage.status === 'Optimized' && <div className="w-2 h-2 bg-green-500 rounded-full"></div>}
                    {stage.status === 'Optimizing' && <div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce"></div>}
                  </div>

                  {/* Pipeline Card */}
                  <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2.5rem)] bg-zinc-50/50 border border-zinc-200 p-5 rounded-xl hover:border-cyan-500/50 hover:bg-white transition-all shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="font-bold text-zinc-900 text-base">{stage.stage}</h3>
                      <span className={cn(
                        "text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-full border",
                        // FIX: Darkened text colors for readability on light backgrounds
                        stage.status === 'Optimized' ? "bg-green-50 text-green-700 border-green-200" :
                          stage.status === 'Active' ? "bg-cyan-50 text-cyan-700 border-cyan-200" :
                            stage.status === 'Optimizing' ? "bg-amber-50 text-amber-700 border-amber-200" :
                              "bg-zinc-100 text-zinc-600 border-zinc-200"
                      )}>{stage.status}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-y-2 text-xs font-medium">
                      <span className="text-zinc-500">Target:</span>
                      <span className="text-zinc-900 text-right">{stage.product}</span>
                      <span className="text-zinc-500">Catalyst:</span>
                      <span className="text-zinc-900 text-right font-mono">{stage.catalyst}</span>
                      <span className="text-zinc-500">Condition:</span>
                      <span className="text-zinc-900 text-right">{stage.condition}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">

          {/* Top Candidates Card */}
          <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-xs font-bold text-zinc-400 uppercase tracking-[0.2em] mb-6">Top AI Candidates</h2>
            <div className="space-y-4">
              {data.top_candidates.map((cat, idx) => (
                <div key={idx} className="p-4 rounded-lg border border-zinc-100 bg-zinc-50/30 hover:bg-white hover:border-cyan-200 transition-all">
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-zinc-900 text-sm">{cat.name}</span>
                      {cat.ai_tag && (
                        <span className="text-[9px] bg-cyan-600 text-white px-2 py-0.5 rounded shadow-sm uppercase font-black">AI GEN</span>
                      )}
                    </div>
                    <span className="font-mono font-bold text-cyan-700">{cat.score}%</span>
                  </div>
                  <div className="w-full h-2 bg-zinc-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cyan-600 rounded-full transition-all duration-1000"
                      style={{ width: `${cat.score}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* System Log Terminal */}
          <div className="bg-zinc-900 rounded-xl p-6 shadow-2xl shadow-cyan-900/10">
            <div className="flex items-center gap-2 mb-4 border-b border-zinc-800 pb-3">
              <Terminal className="w-4 h-4 text-cyan-500" />
              <h2 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Live System Log</h2>
            </div>
            <div className="font-mono text-[11px] space-y-3 h-[250px] overflow-y-auto custom-scrollbar pr-2">
              {data.activity_log.map((log, idx) => (
                <div key={idx} className="flex gap-2 leading-relaxed">
                  <span className="text-zinc-600 shrink-0">[{log.time}]</span>
                  <span className={cn(
                    "break-words",
                    // FIX: Changed amber-400 to amber-500 for terminal readability
                    log.message.includes('Gap') ? "text-amber-500" :
                      log.message.includes('AI') ? "text-cyan-400" : "text-zinc-300"
                  )}><span className="text-zinc-500">→</span> {log.message}</span>
                </div>
              ))}
              <div className="flex gap-2 text-zinc-600 animate-pulse italic">
                <span>[sys]</span>
                <span>Awaiting new telemetry packets...</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}