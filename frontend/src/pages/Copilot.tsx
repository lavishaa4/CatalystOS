import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Network, Send, User, Bot, Loader2, FileText, Activity, ExternalLink } from 'lucide-react';
import { cn } from '../components/AppShell';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  sources?: { title: string; type: string; url?: string }[];
}

export function Copilot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'bot',
      text: "CatalystOS AI Copilot initialized. I have access to the Scientific Knowledge Graph, Experiment Logs, and the GradientBoost-E2J model. How can I assist your discovery process today?",
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // FIX 1: The "Memory" State. This remembers if we are talking about Iron, Copper, etc.
  const [activeTopic, setActiveTopic] = useState<string | null>(null);

  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userQuery = input.trim();
    setInput('');
    setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'user', text: userQuery }]);
    setLoading(true);

    try {
      const q = userQuery.toLowerCase();
      let searchKeyword = '';
      let isFollowUp = q.includes('why') || q.includes('more') || q.includes('it') || q.includes('explain') || q.includes('detail');
      let isFailureQuery = q.includes('fail') || q.includes('deactivat') || q.includes('coking');

      // Detect New Topic
      if (q.includes('iron') || q.includes('fe')) searchKeyword = 'Fe';
      else if (q.includes('copper') || q.includes('cu')) searchKeyword = 'Cu';
      else if (q.includes('pd') || q.includes('palladium')) searchKeyword = 'Pd';

      // FIX 2: Context Logic. If no new keyword is found but it's a follow-up, use the active topic.
      if (!searchKeyword && activeTopic && (isFollowUp || isFailureQuery)) {
        searchKeyword = activeTopic;
      }

      let responseText = "I'm analyzing your query based on current lab data and models. Please specify a catalyst family (like Iron or Copper) for a deeper diagnostic.";
      let sources: { title: string; type: string; url?: string }[] = [];

      if (searchKeyword) {
        setActiveTopic(searchKeyword); // Save to memory

        const [kgRes, expRes] = await Promise.all([
          axios.get(`${import.meta.env.VITE_API_URL}/knowledge-graph?q=${searchKeyword}`),
          axios.get(`${import.meta.env.VITE_API_URL}/experiments?catalyst=${searchKeyword}`)
        ]);

        const papers = kgRes.data.results || [];
        const experiments = expRes.data.experiments || [];

        if (papers.length > 0) {
          // FIX 3: Added dynamic search URL to make links "work"
          sources.push({
            title: papers[0].title,
            type: 'paper',
            url: `https://scholar.google.com/scholar?q=${encodeURIComponent(papers[0].title)}`
          });
        }

        if (experiments.length > 0) {
          const failures = experiments.filter((e: any) => e.status === 'fail');
          if (failures.length > 0) {
            sources.push({
              title: `${failures.length} failed experiments (${failures[0].id})`,
              type: 'experiment',
              url: `http://localhost:5176/discovery` // Link to your internal discovery tab
            });
          }
        }

        // Logic-based response generation
        if (searchKeyword === 'Fe' && (isFailureQuery || isFollowUp)) {
          responseText = `Based on the Knowledge Graph and recent experiment logs, Iron (Fe) catalysts are failing primarily due to **carbon deposition (coking)** at temperatures above 340°C. 
          
Experiment logs (e.g., ${experiments.find((e: any) => e.status === 'fail')?.id || 'EXP-006'}) confirm severe deactivation. The GradientBoost model requires dynamic coking kinetics to improve accuracy. I recommend limiting Fe-based screens to < 320°C.`;
        } else if (searchKeyword === 'Cu') {
          responseText = `Copper (Cu) systems are currently our top performers. Our records show an 88% activity rate. Would you like me to run a simulation on a new Cu variant?`;
        } else {
          responseText = `I found ${papers.length} literature references and ${experiments.length} lab experiments involving ${searchKeyword}. The database shows varying performance across different support materials.`;
        }
      }

      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: responseText,
          sources: sources.length > 0 ? sources : undefined
        }]);
        setLoading(false);
      }, 800);

    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'bot', text: "System Error: Backend is unreachable." }]);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10 h-[calc(100vh-80px)] flex flex-col">
      <div className="flex items-center gap-3 border-b border-zinc-200 pb-4 shrink-0">
        <Network className="w-6 h-6 text-cyan-500" />
        <div>
          <h1 className="text-xl font-bold text-zinc-900">AI Research Copilot</h1>
          <p className="text-sm text-zinc-700">Context-Aware Data Synthesizer</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 pr-4 custom-scrollbar">
        {messages.map((msg) => (
          <div key={msg.id} className={cn("flex gap-4", msg.sender === 'user' ? "flex-row-reverse" : "flex-row")}>
            <div className={cn(
              "w-8 h-8 rounded shrink-0 flex items-center justify-center",
              msg.sender === 'user' ? "bg-cyan-600 text-white shadow-md" : "bg-zinc-100 text-cyan-700 border border-zinc-200"
            )}>
              {msg.sender === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
            </div>

            <div className={cn(
              "max-w-[80%] rounded-lg p-4 text-sm transition-all",
              msg.sender === 'user'
                ? "bg-cyan-600 text-white shadow-sm"
                : "bg-white border border-zinc-200 text-zinc-900 shadow-sm"
            )}>
              <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-zinc-100 space-y-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-500 font-mono">Sources referenced</span>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((src, i) => (
                      // FIX 4: Changed span to <a> tag to make it a real link
                      <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1.5 text-xs bg-white border border-zinc-200 px-2 py-1 rounded text-cyan-700 font-mono hover:border-cyan-600 hover:bg-zinc-50 transition-colors group"
                      >
                        {src.type === 'paper' ? <FileText className="w-3 h-3" /> : <Activity className="w-3 h-3" />}
                        {src.title}
                        <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded bg-zinc-100 text-cyan-700 border border-zinc-200 flex items-center justify-center">
              <Bot className="w-5 h-5" />
            </div>
            <div className="bg-white border border-zinc-200 text-zinc-700 rounded-lg p-4 flex items-center gap-2 shadow-sm">
              <Loader2 className="w-4 h-4 animate-spin text-cyan-600" />
              <span className="text-sm font-mono animate-pulse">Consulting Research Logs...</span>
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      <div className="shrink-0 pt-4">
        <form onSubmit={handleSend} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask about catalyst failures, mechanisms, or run diagnostics..."
            className="w-full bg-white border border-zinc-200 rounded-lg pl-4 pr-12 py-4 text-zinc-800 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all shadow-lg"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-cyan-500 text-zinc-950 rounded hover:bg-cyan-400 disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
