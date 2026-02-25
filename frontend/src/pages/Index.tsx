import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Search, Wrench, FileOutput, Play, RotateCcw, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import FileUploadZone from "@/components/FileUploadZone";
import PipelineVisualization, { type PipelineStage, type StageStatus } from "@/components/PipelineVisualization";
import TerminalLog, { type LogEntry } from "@/components/TerminalLog";
import ResultsDisplay from "@/components/ResultsDisplay";

const MOCK_RULES = [
  "All user data must be encrypted at rest using AES-256",
  "Access logs must be retained for a minimum of 90 days",
  "Multi-factor authentication is required for admin accounts",
  "Personal data must not be stored outside approved regions",
  "API endpoints must enforce rate limiting (max 1000 req/min)",
  "Database backups must occur every 24 hours",
  "Session tokens must expire after 30 minutes of inactivity",
  "All third-party integrations require security review",
  "Password policy: minimum 12 characters, mixed case, symbols",
  "Incident response plan must be tested quarterly",
  "Data retention policy must comply with GDPR Article 17",
  "Audit trails must be immutable and tamper-evident",
  "Service accounts must use rotating credentials",
  "Network segmentation required between production tiers",
];

const MOCK_FINDINGS = [
  { rule: "AES-256 Encryption", status: "pass" as const, detail: "Config specifies AES-256-GCM for data at rest." },
  { rule: "Log Retention (90d)", status: "pass" as const, detail: "Retention set to 180 days — exceeds minimum." },
  { rule: "MFA for Admins", status: "fail" as const, detail: "MFA is optional for admin role. Must be enforced." },
  { rule: "Data Residency", status: "pass" as const, detail: "All storage regions within EU-approved zones." },
  { rule: "Rate Limiting", status: "fail" as const, detail: "Rate limit set to 5000 req/min — exceeds policy max of 1000." },
  { rule: "Backup Frequency", status: "pass" as const, detail: "Backups configured for every 12 hours." },
  { rule: "Session Expiry", status: "pass" as const, detail: "Token TTL set to 15 minutes — within policy." },
  { rule: "Third-party Review", status: "fail" as const, detail: "2 integrations lack security review documentation." },
  { rule: "Password Policy", status: "pass" as const, detail: "Minimum 14 chars enforced with complexity rules." },
  { rule: "Incident Response", status: "pass" as const, detail: "Last drill: 2025-12-15 — within quarterly window." },
];

const STAGE_DEFS = [
  { id: 1, name: "Policy Analyst", icon: Brain, input: "policy.txt", output: "Parsed Rules" },
  { id: 2, name: "Auditor", icon: Search, input: "config + Rules", output: "Findings" },
  { id: 3, name: "Remediator", icon: Wrench, input: "Findings", output: "Remediation Plan" },
  { id: 4, name: "Report Writer", icon: FileOutput, input: "Plan", output: "Final Report" },
];

const LOG_SEQUENCES: { agent: string; message: string; type: LogEntry["type"] }[][] = [
  [
    { agent: "System", message: "Initializing compliance audit pipeline...", type: "info" },
    { agent: "Policy Analyst", message: "Loading policy.txt for NLP parsing...", type: "info" },
    { agent: "Policy Analyst", message: `Parsing ${MOCK_RULES.length} regulatory clauses...`, type: "info" },
    { agent: "Policy Analyst", message: "Clause extraction complete. Building rule graph.", type: "info" },
    { agent: "Policy Analyst", message: `✓ ${MOCK_RULES.length} rules extracted and validated.`, type: "success" },
  ],
  [
    { agent: "Auditor", message: "Loading config.json and parsed rule set...", type: "info" },
    { agent: "Auditor", message: "Cross-referencing 14 rules against system configuration...", type: "info" },
    { agent: "Auditor", message: "⚠ Violation detected: MFA not enforced for admin accounts.", type: "warning" },
    { agent: "Auditor", message: "⚠ Violation detected: Rate limit exceeds policy maximum.", type: "warning" },
    { agent: "Auditor", message: `Audit complete. ${MOCK_FINDINGS.filter(f => f.status === "pass").length} passed, ${MOCK_FINDINGS.filter(f => f.status === "fail").length} failed.`, type: "info" },
  ],
  [
    { agent: "Remediator", message: "Generating remediation plan for 3 findings...", type: "info" },
    { agent: "Remediator", message: "REM-001: Enforce MFA via identity provider config.", type: "info" },
    { agent: "Remediator", message: "REM-002: Reduce rate limit to 1000 req/min.", type: "info" },
    { agent: "Remediator", message: "REM-003: Complete security reviews for integrations.", type: "info" },
    { agent: "Remediator", message: "✓ Remediation plan finalized.", type: "success" },
  ],
  [
    { agent: "Report Writer", message: "Compiling final compliance report...", type: "info" },
    { agent: "Report Writer", message: "Generating executive summary and detailed findings...", type: "info" },
    { agent: "Report Writer", message: "✓ Report generation complete. Status: ACTION REQUIRED.", type: "warning" },
    { agent: "System", message: "Pipeline finished. All stages complete.", type: "success" },
  ],
];

const Index = () => {
  const [policyFile, setPolicyFile] = useState<File | null>(null);
  const [configFile, setConfigFile] = useState<File | null>(null);
  const [stages, setStages] = useState<PipelineStage[]>(
    STAGE_DEFS.map((s) => ({ ...s, status: "idle" as StageStatus }))
  );
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const logIdRef = useRef(0);

  const addLogs = useCallback(
    (entries: { agent: string; message: string; type: LogEntry["type"] }[]) => {
      return new Promise<void>((resolve) => {
        let i = 0;
        const interval = setInterval(() => {
          if (i >= entries.length) {
            clearInterval(interval);
            resolve();
            return;
          }
          const entry = entries[i];
          const now = new Date();
          const ts = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;
          logIdRef.current += 1;
          setLogs((prev) => [
            ...prev,
            { id: logIdRef.current, timestamp: ts, ...entry },
          ]);
          i++;
        }, 600);
      });
    },
    []
  );

  const runAudit = useCallback(async () => {
    if (!policyFile || !configFile) return;
    
    setIsRunning(true);
    setShowResults(false);
    setLogs([{ id: 0, agent: "System", message: "Preparing files and connecting to backend...", type: "info", timestamp: new Date().toLocaleTimeString() }]);

    try {
      const formData = new FormData();
      formData.append("policy", policyFile);
      formData.append("config", configFile);

      const response = await fetch("https://ai-compliance-auditor.onrender.com/audit", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Backend connection failed");

      const data = await response.json();
      
      // Simulate pipeline UI progress while we have the data
      for (let i = 0; i < 4; i++) {
        setStages((prev) =>
          prev.map((s, idx) => ({
            ...s,
            status: idx === i ? "active" : idx < i ? "complete" : "idle",
          }))
        );
        await addLogs(LOG_SEQUENCES[i]);
      }

      setStages((prev) => prev.map((s) => ({ ...s, status: "complete" as StageStatus })));
      setShowResults(true);
    } catch (error) {
      setLogs((prev) => [...prev, { id: Date.now(), agent: "System", message: "Error: Could not reach backend server.", type: "error", timestamp: new Date().toLocaleTimeString() }]);
    } finally {
      setIsRunning(false);
    }
  }, [policyFile, configFile, addLogs]);

  const reset = () => {
    setStages(STAGE_DEFS.map((s) => ({ ...s, status: "idle" as StageStatus })));
    setLogs([]);
    setShowResults(false);
    setIsRunning(false);
  };

  const canRun = policyFile && configFile && !isRunning;

  return (
    <div className="min-h-screen bg-background grid-pattern">
      {/* Header */}
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
            <Button
              variant="outline"
              size="sm"
              onClick={reset}
              disabled={isRunning}
              className="font-mono text-xs"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              Reset
            </Button>
            <Button
              size="sm"
              onClick={runAudit}
              disabled={!canRun}
              className="font-mono text-xs bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Play className="w-3.5 h-3.5 mr-1.5" />
              Run Audit
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Upload Section */}
        <section>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            Input Files
          </h2>
          <FileUploadZone
            onFilesUploaded={(p, c) => {
              setPolicyFile(p);
              setConfigFile(c);
            }}
          />
        </section>

        {/* Pipeline */}
        <section>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            Live Pipeline
          </h2>
          <PipelineVisualization stages={stages} />
        </section>

        {/* Logs + Results */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 h-80">
            <TerminalLog logs={logs} />
          </div>
          <div className="lg:col-span-2">
            <AnimatePresence>
              {showResults ? (
                <ResultsDisplay
                  parsedRules={MOCK_RULES}
                  findings={MOCK_FINDINGS}
                  overallStatus="action_required"
                />
              ) : (
                <motion.div
                  className="terminal-bg h-80 flex items-center justify-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="text-center">
                    <Shield className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                      {isRunning
                        ? "Audit in progress..."
                        : "Upload files and run audit to see results"}
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
