import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { FileText, FileJson, Upload, Check } from "lucide-react";

interface FileUploadZoneProps {
  onFilesUploaded: (policyFile: File | null, configFile: File | null) => void;
}

const FileUploadZone = ({ onFilesUploaded }: FileUploadZoneProps) => {
  const [policyFile, setPolicyFile] = useState<File | null>(null);
  const [configFile, setConfigFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState<"policy" | "config" | null>(null);

  const handleDrop = useCallback(
    (type: "policy" | "config") => (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(null);
      const file = e.dataTransfer.files[0];
      if (!file) return;
      if (type === "policy") {
        setPolicyFile(file);
        onFilesUploaded(file, configFile);
      } else {
        setConfigFile(file);
        onFilesUploaded(policyFile, file);
      }
    },
    [policyFile, configFile, onFilesUploaded]
  );

  const handleFileSelect = (type: "policy" | "config") => (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (type === "policy") {
      setPolicyFile(file);
      onFilesUploaded(file, configFile);
    } else {
      setConfigFile(file);
      onFilesUploaded(policyFile, file);
    }
  };

  const zones = [
    {
      type: "policy" as const,
      label: "policy.txt",
      subtitle: "Natural Language Policy",
      icon: FileText,
      file: policyFile,
      accept: ".txt",
    },
    {
      type: "config" as const,
      label: "config.json",
      subtitle: "System Configuration",
      icon: FileJson,
      file: configFile,
      accept: ".json",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {zones.map((zone) => (
        <motion.label
          key={zone.type}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(zone.type);
          }}
          onDragLeave={() => setDragOver(null)}
          onDrop={handleDrop(zone.type)}
          className={`upload-zone flex flex-col items-center gap-3 ${
            dragOver === zone.type ? "upload-zone-active" : ""
          } ${zone.file ? "border-success/40 bg-success/5" : ""}`}
        >
          <input
            type="file"
            accept={zone.accept}
            onChange={handleFileSelect(zone.type)}
            className="hidden"
          />
          <div className={`p-3 rounded-lg ${zone.file ? "bg-success/10" : "bg-secondary"}`}>
            {zone.file ? (
              <Check className="w-6 h-6 text-success" />
            ) : (
              <zone.icon className="w-6 h-6 text-primary" />
            )}
          </div>
          <div>
            <p className="font-mono text-sm font-medium text-foreground">
              {zone.file ? zone.file.name : zone.label}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {zone.file ? `${(zone.file.size / 1024).toFixed(1)} KB` : zone.subtitle}
            </p>
          </div>
          {!zone.file && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Upload className="w-3 h-3" />
              <span>Drop or click to upload</span>
            </div>
          )}
        </motion.label>
      ))}
    </div>
  );
};

export default FileUploadZone;
