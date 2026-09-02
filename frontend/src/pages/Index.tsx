import { useState, useCallback, useRef, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Brain, Search, Wrench, FileOutput, Play, RotateCcw, Shield, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import PipelineVisualization, { type PipelineStage, type StageStatus } from "@/components/PipelineVisualization";
import TerminalLog, { type LogEntry } from "@/components/TerminalLog";
import ResultsDisplay from "@/components/ResultsDisplay";
import { SAMPLE_SCENARIOS } from "@/lib/sampleScenarios";
import { streamAudit } from "@/lib/api";

const STAGE_DEFS = [
  { id: 1, name: "Policy Analyst", icon: Brain, input: "policy.txt", output: "Parsed Rules" },
  { id: 2, name: "Config Auditor", icon: Search, input: "config + Rules", output: "Findings" },
  { id: 3, name: "Remediator", icon: Wrench, input: "Findings", output: "Remediation Plan" },
  { id: 4, name: "Report Writer", icon: FileOutput, input: "Plan", output: "Final Report" },
];

// Backend SSE events key stages by name ("policy", "auditor", "remediator", "report");
// PipelineVisualization keys them by numeric id — map between the two here.
const KEY_TO_ID: Record<string, number> = { policy: 1, auditor: 2, remediator: 3, report: 4 };

const POLICY_MAX = 2000;
const CONFIG_MAX = 5000;

const idleStages = (): PipelineStage[] => STAGE_DEFS.map((s) => ({ ...s, status: "idle" as StageStatus }));

const Index = () => {
  const [scenarioId, setScenarioId] = useState(SAMPLE_SCENARIOS[0].id);
  const [policyText, setPolicyText] = useState(SAMPLE_SCENARIOS[0].policy);
  const [configText, setConfigText] = useState(SAMPLE_SCENARIOS[0].config);
  const [stages, setStages] = useState<PipelineStage[]>(idleStages());
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [results, setResults] = useState<any>(null);
  const [showResults, setShowResults] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const logIdRef = useRef(0);

  const scenario = useMemo(() => SAMPLE_SCENARIOS.find((s) => s.id === scenarioId)!, [scenarioId]);

  const addLog = useCallback((agent: string, message: string, type: LogEntry["type"] = "info") => {
    const ts = new Date().toLocaleTimeString();
    logIdRef.current += 1;
    setLogs((prev) => [...prev, { id: logIdRef.current, timestamp: ts, agent, message, type }]);
  }, []);

  const selectScenario = (id: string) => {
    const s = SAMPLE_SCENARIOS.find((sc) => sc.id === id);
    if (!s) return;
    setScenarioId(id);
    setPolicyText(s.policy);
    setConfigText(s.config);
  };

  const setStageStatus = (stageKey: string, status: StageStatus) => {
    const id = KEY_TO_ID[stageKey];
    setStages((prev) => prev.map((s) => (s.id === id ? { ...s, status } : s)));
  };

  const runAudit = useCallback(async () => {
    setIsRunning(true);
    setShowResults(false);
    setResults(null);
    setLogs([]);
    setStages(idleStages());
    addLog("System", "Connecting to audit pipeline...", "info");

    try {
      let finalPayload: any = null;
      await streamAudit(policyText, configText, (evt) => {
        switch (evt.event) {
          case "stage_start":
            setStageStatus(evt.data.stage, "active");
            addLog(evt.data.name, "started", "info");
            break;
          case "stage_complete":
            setStageStatus(evt.data.stage, "complete");
            addLog(evt.data.name, "complete", "success");
            break;
          case "error":
            addLog("System", evt.data.message, "error");
            throw new Error(evt.data.message);
          case "done":
            finalPayload = evt.data;
            break;
        }
      });

      if (finalPayload) {
        const rawRules = finalPayload.parsed_rules || [];
        const parsed_rules_list = Array.isArray(rawRules)
          ? rawRules.map((r: any) =>
              typeof r === "string" ? r : `${r.resource_type} ${r.property} must be ${r.expected_value}`
            )
          : [];
        const findings_list = Array.isArray(finalPayload.findings) ? finalPayload.findings : [];
        const overallStatus = findings_list.some((f: any) => f.status === "fail") ? "action_required" : "compliant";

        setResults({ ...finalPayload, parsed_rules_list, findings_list, overallStatus });
        addLog("System", "Audit complete.", "success");
        setShowResults(true);
      }
    } catch (error: any) {
      addLog("System", `Error: ${error.message}`, "error");
    } finally {
      setIsRunning(false);
    }
  }, [policyText, configText, addLog]);

  const reset = () => {
    setStages(idleStages());
    setLogs([]);
    setResults(null);
    setShowResults(false);
    setIsRunning(false);
  };

  const overLimit = policyText.length > POLICY_MAX || configText.length > CONFIG_MAX;
  const canRun = policyText.trim().length > 0 && configText.trim().length > 0 && !isRunning && !overLimit;

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
        <section className="space-y-3">
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wide">Sample scenarios</p>
          <div className="flex flex-wrap gap-3">
            {SAMPLE_SCENARIOS.map((s) => (
              <button
                key={s.id}
                onClick={() => selectScenario(s.id)}
                disabled={isRunning}
                className={`stage-card text-left px-4 py-2.5 min-w-[200px] transition-colors ${
                  s.id === scenarioId ? "stage-card-active" : "opacity-70 hover:opacity-100"
                }`}
              >
                <p className="font-semibold text-sm">{s.label}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{s.description}</p>
              </button>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono text-muted-foreground uppercase tracking-wide">Policy text</label>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-mono ${policyText.length > POLICY_MAX ? "text-destructive" : "text-muted-foreground"}`}>
                  {policyText.length}/{POLICY_MAX}
                </span>
                <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => setPolicyText(scenario.policy)}>
                  Reset to sample
                </Button>
              </div>
            </div>
            <Textarea
              value={policyText}
              onChange={(e) => setPolicyText(e.target.value)}
              className="font-mono text-xs h-56 resize-none"
              spellCheck={false}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono text-muted-foreground uppercase tracking-wide">Config JSON</label>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-mono ${configText.length > CONFIG_MAX ? "text-destructive" : "text-muted-foreground"}`}>
                  {configText.length}/{CONFIG_MAX}
                </span>
                <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => setConfigText(scenario.config)}>
                  Reset to sample
                </Button>
              </div>
            </div>
            <Textarea
              value={configText}
              onChange={(e) => setConfigText(e.target.value)}
              className="font-mono text-xs h-56 resize-none"
              spellCheck={false}
            />
          </div>
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
                  overallStatus={results.overallStatus}
                />
              ) : (
                <div className="terminal-bg h-80 flex items-center justify-center">
                  <div className="text-center">
                    <Shield className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                      {isRunning ? "Audit in progress..." : "Pick a scenario and run the audit to see live results"}
                    </p>
                  </div>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {showResults && results?.final_report && (
          <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="terminal-bg overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
              <FileText className="w-4 h-4 text-primary" />
              <span className="text-sm font-semibold">Final Report</span>
            </div>
            <div className="p-4 max-h-[32rem] overflow-y-auto">
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{results.final_report}</p>
            </div>
          </motion.section>
        )}
      </main>
    </div>
  );
};

export default Index;
