import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Search, Wrench, FileOutput, Play, RotateCcw, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import FileUploadZone from "@/components/FileUploadZone";
import PipelineVisualization, { type PipelineStage, type StageStatus } from "@/components/PipelineVisualization";
import TerminalLog, { type LogEntry } from "@/components/TerminalLog";
import ResultsDisplay from "@/components/ResultsDisplay";

const STAGE_DEFS = [
  { id: 1, name: "Policy Analyst", icon: Brain, input: "policy.txt", output: "Parsed Rules" },
  { id: 2, name: "Auditor", icon: Search, input: "config + Rules", output: "Findings" },
  { id: 3, name: "Remediator", icon: Wrench, input: "Findings", output: "Remediation Plan" },
  { id: 4, name: "Report Writer", icon: FileOutput, input: "Plan", output: "Final Report" },
];

const Index = () => {
  const [policyFile, setPolicyFile] = useState<File | null>(null);
  const [configFile, setConfigFile] = useState<File | null>(null);
  const [stages, setStages] = useState<PipelineStage[]>(
    STAGE_DEFS.map((s) => ({ ...s, status: "idle" as StageStatus }))
  );
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [results, setResults] = useState<any>(null);
  const [showResults, setShowResults] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const logIdRef = useRef(0);

  const addLog = useCallback((agent: string, message: string, type: LogEntry["type"] = "info") => {
    const now = new Date();
    const ts = now.toLocaleTimeString();
    logIdRef.current += 1;
    setLogs((prev) => [
      ...prev,
      { id: logIdRef.current, timestamp: ts, agent, message, type },
    ]);
  }, []);

  const runAudit = useCallback(async () => {
    if (!policyFile || !configFile) return;
    
    setIsRunning(true);
    setShowResults(false);
    setResults(null);
    setLogs([]);
    addLog("System", "Preparing files and connecting to backend...", "info");

    try {
      const formData = new FormData();
      formData.append("policy", policyFile);
      formData.append("config", configFile);

      const response = await fetch("https://ai-compliance-auditor.onrender.com/audit", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(`Backend Error: ${response.statusText}`);

      const data = await response.json();
      
      if (data.status === "success") {
        // Correcting the data mapping to ensure parsed_rules is a list of strings
        const rawRules = data.results.parsed_rules || [];
        const formattedRules = Array.isArray(rawRules) 
          ? rawRules.map((r: any) => typeof r === 'string' ? r : `${r.resource_type} ${r.property} must be ${r.expected_value}`)
          : [];

        // Correcting the findings parsing
        let parsedFindings = [];
        try {
          parsedFindings = typeof data.results.findings === 'string' 
            ? JSON.parse(data.results.findings) 
            : data.results.findings;
        } catch (e) {
          console.error("Failed to parse findings:", e);
        }

        setResults({
          ...data.results,
          parsed_rules_list: formattedRules,
          findings_list: parsedFindings
        });

        setStages(STAGE_DEFS.map(s => ({ ...s, status: "complete" as StageStatus })));
        addLog("System", "Audit complete. Processing results...", "success");
        setShowResults(true);
      } else {
        throw new Error(data.message || "Audit failed");
      }

    } catch (error: any) {
      addLog("System", `Error: ${error.message}`, "error");
    } finally {
      setIsRunning(false);
    }
  }, [policyFile, configFile, addLog]);

  const reset = () => {
    setStages(STAGE_DEFS.map((s) => ({ ...s, status: "idle" as StageStatus })));
    setLogs([]);
    setResults(null);
    setShowResults(false);
    setIsRunning(false);
  };

  const canRun = policyFile && configFile && !isRunning;

  return (
    <div className="min-h-screen bg-background grid-pattern">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 glow-primary">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">AI Compliance Auditor</h1>
              <p className="text-xs text-muted-foreground">Agentic Workflow Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={reset} disabled={isRunning} className="font-mono text-xs">
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Reset
            </Button>
            <Button size="sm" onClick={runAudit} disabled={!canRun} className="font-mono text-xs bg-primary text-primary-foreground hover:bg-primary/90">
              <Play className="w-3.5 h-3.5 mr-1.5" /> Run Audit
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <section>
          <FileUploadZone onFilesUploaded={(p, c) => { setPolicyFile(p); setConfigFile(c); }} />
        </section>

        <section>
          <PipelineVisualization stages={stages} />
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 h-80">
            <TerminalLog logs={logs} />
          </div>
          <div className="lg:col-span-2">
            <AnimatePresence>
              {showResults ? (
                <ResultsDisplay
                  parsedRules={results.parsed_rules_list}
                  findings={results.findings_list}
                  overallStatus="action_required"
                />
              ) : (
                <div className="terminal-bg h-80 flex items-center justify-center">
                  <div className="text-center">
                    <Shield className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                      {isRunning ? "Audit in progress..." : "Upload files and run audit to see live results"}
                    </p>
                  </div>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
