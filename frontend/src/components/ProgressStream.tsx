"use client";

import { useEffect, useState, useRef } from "react";
import { Terminal, CheckCircle, Loader2, AlertCircle } from "lucide-react";

interface ProgressStreamProps {
  campaignId: string;
  onCompleted?: () => void;
}

export default function ProgressStream({ campaignId, onCompleted }: ProgressStreamProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const [percent, setPercent] = useState<number>(10);
  const [status, setStatus] = useState<string>("running");
  const [isDone, setIsDone] = useState<boolean>(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";
      eventSource = new EventSource(`${apiBase}/campaigns/${campaignId}/stream`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.all_logs && Array.isArray(data.all_logs)) {
            setLogs(data.all_logs);
          }
          if (data.progress_percent !== undefined) {
            setPercent(data.progress_percent);
          }
          if (data.status) {
            setStatus(data.status);
          }
          if (data.completed) {
            setIsDone(true);
            if (onCompleted) onCompleted();
          }
        } catch (e) {
          console.error("Failed to parse SSE payload", e);
        }
      };

      eventSource.addEventListener("done", () => {
        setIsDone(true);
        setPercent(100);
        setStatus("completed");
        if (onCompleted) onCompleted();
        if (eventSource) eventSource.close();
      });

      eventSource.onerror = (err) => {
        console.warn("SSE connection error or closed", err);
        if (eventSource) eventSource.close();
      };
    } catch (err) {
      console.error("SSE init error", err);
    }

    return () => {
      if (eventSource) eventSource.close();
    };
  }, [campaignId, onCompleted]);

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      <div className="bg-slate-850 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="font-mono text-xs font-semibold text-slate-200">
            Autonomous Pipeline Stream (LangGraph Agent Execution)
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isDone ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Complete</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-950/60 text-blue-400 border border-blue-800/60">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Running ({percent}%)</span>
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 h-1.5">
        <div
          className="bg-emerald-500 h-1.5 transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Terminal Logs Window */}
      <div
        ref={logContainerRef}
        className="p-4 bg-slate-950/90 font-mono text-xs text-slate-300 space-y-1.5 max-h-56 overflow-y-auto"
      >
        {logs.length === 0 ? (
          <div className="text-slate-600 italic">Initializing agent network...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex items-start gap-2">
              <span className="text-emerald-500 select-none">›</span>
              <span className={log.includes("✓") ? "text-emerald-300 font-semibold" : "text-slate-300"}>
                {log}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
