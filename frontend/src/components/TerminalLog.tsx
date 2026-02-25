import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Terminal } from "lucide-react";

export interface LogEntry {
  id: number;
  timestamp: string;
  agent: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
}

interface TerminalLogProps {
  logs: LogEntry[];
}

const typeColors: Record<LogEntry["type"], string> = {
  info: "text-primary",
  success: "text-success",
  warning: "text-warning",
  error: "text-destructive",
};

const TerminalLog = ({ logs }: TerminalLogProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="terminal-bg h-full flex flex-col">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
        <Terminal className="w-4 h-4 text-primary" />
        <span className="text-xs font-semibold text-foreground">System Logs</span>
        <div className="ml-auto flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-destructive/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-warning/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-success/60" />
        </div>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-1 font-mono text-xs">
        {logs.length === 0 && (
          <p className="text-muted-foreground">Awaiting input files...</p>
        )}
        <AnimatePresence>
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-2 leading-relaxed"
            >
              <span className="text-muted-foreground shrink-0">{log.timestamp}</span>
              <span className={`shrink-0 ${typeColors[log.type]}`}>
                [{log.agent}]
              </span>
              <span className="text-secondary-foreground">{log.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {logs.length > 0 && (
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="text-primary"
          >
            █
          </motion.span>
        )}
      </div>
    </div>
  );
};

export default TerminalLog;
