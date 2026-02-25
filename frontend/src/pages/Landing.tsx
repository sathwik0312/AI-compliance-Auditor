import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Shield, Cpu, FileText, Wrench, ArrowRight, Zap, GitBranch, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";

const FEATURES = [
  {
    icon: Cpu,
    title: "Agentic Orchestration",
    description:
      "Powered by a 4-stage pipeline — Policy Analyst, Auditor, Remediator, and Report Writer — each agent builds on the previous one's output.",
  },
  {
    icon: FileText,
    title: "Policy-as-Code",
    description:
      "Automatically parse natural language .txt policy documents into structured, machine-readable JSON rules using LLM-powered extraction.",
  },
  {
    icon: Wrench,
    title: "Real-time Remediation",
    description:
      "Get precise, actionable fix commands — not just a list of problems. Each violation is paired with the exact remediation step.",
  },
];

const PIPELINE_STEPS = [
  { label: "Policy Analyst", detail: "Parse policy → JSON rules" },
  { label: "Config Auditor", detail: "Audit config against rules" },
  { label: "Remediator", detail: "Generate fix commands" },
  { label: "Report Writer", detail: "Compile final report" },
];

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background grid-pattern overflow-hidden">
      {/* Nav */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 glow-primary">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <span className="font-bold text-lg tracking-tight">ComplianceAI</span>
          </div>
          <Button
            size="sm"
            className="font-mono text-xs"
            onClick={() => navigate("/dashboard")}
          >
            Open Dashboard
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
        {/* Ambient glow */}
        <div className="absolute inset-0 -z-10 flex items-center justify-center">
          <div className="w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px]" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-card/80 text-xs text-muted-foreground font-mono mb-8">
            <Zap className="w-3 h-3 text-primary" />
            Built with Google ADK &middot; Multi-Agent Architecture
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight mb-6">
            The Agentic
            <br />
            <span className="text-primary">Compliance Engine</span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Transform natural language policies into automated security audits
            using a multi-agent orchestration framework. Audit AI configurations
            at the speed of thought.
          </p>

          <div className="flex items-center justify-center gap-4">
            <Button
              size="lg"
              className="font-mono text-sm glow-primary"
              onClick={() => navigate("/dashboard")}
            >
              Enter Dashboard
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="font-mono text-sm"
              onClick={() =>
                document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })
              }
            >
              <GitBranch className="w-4 h-4 mr-2" />
              View Architecture
            </Button>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15, duration: 0.5 }}
              className="stage-card hover:border-primary/40 transition-colors group"
            >
              <div className="p-2 rounded-md bg-primary/10 w-fit mb-4 group-hover:glow-primary transition-shadow">
                <f.icon className="w-5 h-5 text-primary" />
              </div>
              <h3 className="font-semibold text-base mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {f.description}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="max-w-6xl mx-auto px-6 pb-24">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2 text-center">
            Architecture
          </h2>
          <p className="text-2xl sm:text-3xl font-bold text-center mb-12">
            A 4-Agent Sequential Pipeline
          </p>

          <div className="relative flex flex-col md:flex-row items-center md:items-stretch gap-4 md:gap-0">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={step.label} className="flex items-center md:flex-1">
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.12, duration: 0.4 }}
                  className="stage-card w-full text-center hover:border-primary/40 transition-colors"
                >
                  <div className="text-xs font-mono text-primary/70 mb-1">
                    Agent {i + 1}
                  </div>
                  <div className="font-semibold text-sm mb-1">{step.label}</div>
                  <div className="text-xs text-muted-foreground">{step.detail}</div>
                </motion.div>
                {i < PIPELINE_STEPS.length - 1 && (
                  <ArrowRight className="hidden md:block w-5 h-5 text-primary/40 mx-2 shrink-0" />
                )}
              </div>
            ))}
          </div>

          <div className="mt-8 terminal-bg p-5 font-mono text-xs text-muted-foreground leading-relaxed max-w-3xl mx-auto">
            <p className="text-primary/80 mb-2">// Shared State Architecture</p>
            <p>
              Each agent reads from and writes to a shared{" "}
              <span className="text-primary">ToolContext.state</span> object — a
              "digital whiteboard" that enables stateful, sequential
              communication across the pipeline.
            </p>
          </div>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="border-t border-border bg-card/30">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { value: "4", label: "AI Agents" },
              { value: "14+", label: "Policy Rules Parsed" },
              { value: "<30s", label: "Full Audit Cycle" },
              { value: "100%", label: "Actionable Fixes" },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="text-3xl font-bold text-primary font-mono">
                  {stat.value}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <BarChart3 className="w-8 h-8 text-primary mx-auto mb-4 opacity-60" />
        <h2 className="text-2xl sm:text-3xl font-bold mb-4">
          Ready to Audit?
        </h2>
        <p className="text-muted-foreground mb-8 max-w-md mx-auto">
          Upload your policy document and system configuration to get started
          with automated compliance analysis.
        </p>
        <Button
          size="lg"
          className="font-mono text-sm glow-primary"
          onClick={() => navigate("/dashboard")}
        >
          Launch the Dashboard
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground font-mono">
        Built with Google ADK &middot; Gemini &middot; React &middot; Tailwind CSS
      </footer>
    </div>
  );
};

export default Landing;
