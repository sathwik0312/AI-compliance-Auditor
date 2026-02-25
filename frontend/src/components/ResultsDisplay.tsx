import { motion } from "framer-motion";
import { CheckCircle2, AlertTriangle, FileText, Shield } from "lucide-react";

interface ResultsDisplayProps {
  parsedRules: string[];
  findings: { rule: string; status: "pass" | "fail"; detail: string }[];
  overallStatus: "compliant" | "action_required" | null;
}

const ResultsDisplay = ({ parsedRules, findings, overallStatus }: ResultsDisplayProps) => {
  const passCount = findings.filter((f) => f.status === "pass").length;
  const failCount = findings.filter((f) => f.status === "fail").length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 lg:grid-cols-2 gap-4"
    >
      {/* Parsed Rules */}
      <div className="terminal-bg overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <FileText className="w-4 h-4 text-primary" />
          <span className="text-sm font-semibold">Parsed Rules</span>
          <span className="ml-auto text-xs text-muted-foreground font-mono">
            {parsedRules.length} clauses
          </span>
        </div>
        <div className="p-4 space-y-2 max-h-80 overflow-y-auto">
          {parsedRules.map((rule, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex gap-3 text-xs font-mono"
            >
              <span className="text-primary/50 shrink-0 w-6 text-right">{String(i + 1).padStart(2, "0")}</span>
              <span className="text-secondary-foreground">{rule}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Compliance Report */}
      <div className="terminal-bg overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <Shield className="w-4 h-4 text-primary" />
          <span className="text-sm font-semibold">Compliance Report</span>
          {overallStatus && (
            <span className={`ml-auto text-xs px-2 py-0.5 rounded-full font-medium ${
              overallStatus === "compliant" ? "badge-compliant" : "badge-action-required"
            }`}>
              {overallStatus === "compliant" ? "✓ Compliant" : "⚠ Action Required"}
            </span>
          )}
        </div>
        <div className="p-4">
          {/* Summary bar */}
          <div className="flex gap-4 mb-4 text-xs font-mono">
            <span className="text-success">{passCount} Passed</span>
            <span className="text-destructive">{failCount} Failed</span>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {findings.map((finding, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-2 p-2 rounded-md bg-secondary/30 text-xs"
              >
                {finding.status === "pass" ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-success shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 text-warning shrink-0 mt-0.5" />
                )}
                <div>
                  <p className="font-medium text-foreground">{finding.rule}</p>
                  <p className="text-muted-foreground mt-0.5">{finding.detail}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ResultsDisplay;
