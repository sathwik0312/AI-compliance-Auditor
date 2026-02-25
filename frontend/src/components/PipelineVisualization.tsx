import { motion } from "framer-motion";
import { Brain, Search, Wrench, FileOutput, ChevronRight, Lock, Users } from "lucide-react";

export type StageStatus = "idle" | "active" | "complete";

interface PipelineStage {
  id: number;
  name: string;
  icon: React.ElementType;
  input: string;
  output: string;
  status: StageStatus;
}

interface PipelineVisualizationProps {
  stages: PipelineStage[];
}

const statusStyles: Record<StageStatus, string> = {
  idle: "stage-card opacity-60",
  active: "stage-card stage-card-active animate-pulse-glow",
  complete: "stage-card stage-card-complete",
};

const PipelineVisualization = ({ stages }: PipelineVisualizationProps) => {
  const plannedModules = [
    { name: "RAG Context", icon: Lock, label: "Planned" },
    { name: "Human-in-the-Loop", icon: Users, label: "Coming Soon" },
  ];

  return (
    <div className="space-y-6">
      {/* Main pipeline */}
      <div className="flex items-center gap-0 overflow-x-auto pb-4">
        {stages.map((stage, i) => (
          <div key={stage.id} className="flex items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`${statusStyles[stage.status]} min-w-[180px] relative`}
            >
              {stage.status === "active" && (
                <motion.div
                  className="absolute inset-0 rounded-lg border border-primary/30"
                  animate={{ opacity: [0.3, 0.8, 0.3] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
              <div className="flex items-center gap-2 mb-3">
                <div className={`p-1.5 rounded-md ${
                  stage.status === "complete" ? "bg-success/15" :
                  stage.status === "active" ? "bg-primary/15" : "bg-secondary"
                }`}>
                  <stage.icon className={`w-4 h-4 ${
                    stage.status === "complete" ? "text-success" :
                    stage.status === "active" ? "text-primary" : "text-muted-foreground"
                  }`} />
                </div>
                <span className="font-semibold text-sm">{stage.name}</span>
              </div>
              <div className="space-y-1 font-mono text-[10px]">
                <p className="text-muted-foreground">
                  <span className="text-primary/70">IN:</span> {stage.input}
                </p>
                <p className="text-muted-foreground">
                  <span className="text-success/70">OUT:</span> {stage.output}
                </p>
              </div>
              {stage.status === "active" && (
                <motion.div
                  className="mt-2 h-1 bg-primary/20 rounded-full overflow-hidden"
                >
                  <motion.div
                    className="h-full bg-primary rounded-full"
                    animate={{ width: ["0%", "100%"] }}
                    transition={{ duration: 3, repeat: Infinity }}
                  />
                </motion.div>
              )}
            </motion.div>
            {i < stages.length - 1 && (
              <div className="flex items-center px-1">
                <div className="pipeline-connector w-6" />
                <ChevronRight className="w-4 h-4 text-primary/40 -ml-1" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Planned modules */}
      <div className="flex gap-3">
        {plannedModules.map((mod) => (
          <div key={mod.name} className="stage-card opacity-40 flex items-center gap-2 py-2 px-3">
            <mod.icon className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">{mod.name}</span>
            <span className="badge-planned text-[9px] px-1.5 py-0.5 rounded-full ml-auto">
              {mod.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PipelineVisualization;
export type { PipelineStage };
