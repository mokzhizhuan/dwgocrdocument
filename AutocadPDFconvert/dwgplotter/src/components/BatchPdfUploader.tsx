import React, { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";
import "./BatchPdfUploader.css";

type LogItem = {
  name: string;
  status: string;
  progress: number;
  output?: boolean;
  combined?: string;
};

export default function BatchPdfUploader() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [log, setLog] = useState<LogItem[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [converting, setConverting] = useState(false);
  const [folder, setFolder] = useState<string>("converted_batch");
  const [collapsed, setCollapsed] = useState(false);
  const [batchDone, setBatchDone] = useState(false);

  const [summary, setSummary] = useState<{
    total: number;
    converted: number;
    failed: number;
  } | null>(null);

  // -------------------------
  // File selection
  // -------------------------
  function handleSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (!e.target.files) return;

    const fileList = e.target.files;
    setFiles(fileList);
    setLog([]);
    setJobId(null);
    setBatchDone(false);
    setSummary(null);

    const first = fileList[0];
    if (first && (first as any).webkitRelativePath) {
      setFolder(first.webkitRelativePath.split("/")[0]);
    }
  }

  // -------------------------
  // Start batch
  // -------------------------
  async function handleConvert() {
    if (!files) return;

    const formData = new FormData();
    Array.from(files).forEach((f) => {
      formData.append("files", f, f.webkitRelativePath || f.name);
    });

    setConverting(true);
    setCollapsed(true);

    const res = await fetch(`${API_BASE_URL}/convert/batch`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    setJobId(data.job_id);
  }

  // -------------------------
  // Polling
  // -------------------------
  useEffect(() => {
    if (!jobId) return;

    const timer = setInterval(async () => {
      try {
        const statusRes = await fetch(
          `${API_BASE_URL}/convert/status/${jobId}`
        );
        if (!statusRes.ok) return;

        const statusData: LogItem[] = await statusRes.json();


        setLog(statusData.filter((f) => typeof f.status === "string"));

        const summaryRes = await fetch(
          `${API_BASE_URL}/convert/summary/${jobId}`
        );
        if (!summaryRes.ok) return;

        const s = await summaryRes.json();
        setSummary(s);

        if (s.converted + s.failed === s.total) {
          setBatchDone(true);
          setConverting(false);
          clearInterval(timer);
        }
      } catch {
        console.warn("Polling failed");
      }
    }, 1500);

    return () => clearInterval(timer);
  }, [jobId]);

  // -------------------------
  // Downloads
  // -------------------------
  async function downloadZip(includeMerged: number) {
    if (!jobId) return;

    const res = await fetch(
      `${API_BASE_URL}/convert/download/${jobId}?include_merged=${includeMerged}`
    );
    if (!res.ok) return alert("ZIP not ready");

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${folder.replace(/\s+/g, "_")}_converted.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  // -------------------------
  // UI
  // -------------------------
  return (
    <div className="page">
      <header className="pageHeader">
        <h1>📁 Batch PDF → DOCX Converter</h1>
      </header>

      {batchDone && summary && (
        <div className="card summaryCard">
          <div>Total PDFs: {summary.total}</div>
          <div>Converted: {summary.converted}</div>
          <div>Failed: {summary.failed}</div>
        </div>
      )}

      <div className="card controls">
         <div className="filePickerRow">
            <label className="fileBtn">
              Choose Files
              <input
                type="file"
                webkitdirectory="true"
                multiple
                onChange={handleSelect}
                disabled={converting}
                hidden
              />
            </label>
          

        {files && (
          <span className="fileInfo">
            {folder} ({files.length} files)
          </span>
        )}
        </div> <br/>
        <button
          className="primaryBtn"
          disabled={!files || converting}
          onClick={handleConvert}
        >
          {converting ? "Converting…" : "Convert"}
        </button>
      </div>

      <div className={`card collapsible ${collapsed ? "collapsed" : ""}`}>
        <h3 className="sectionTitle" onClick={() => setCollapsed(!collapsed)}>
          📄 Conversion Status
        </h3>

        <div className="table">
          {log.map((f, i) => (
            <div key={i} className="row">
              <div className="fileName">{f.name}</div>
              
              <div className="progressCell">
                <div className="progressBar">
                  <div
                    className={`progressFill ${
                      f.status.includes("❌")
                        ? "progress-error"
                        : f.status.includes("✔")
                        ? "progress-success"
                        : "progress-running"
                    }`}
                    style={{ width: `${f.progress}%` }}
                  />
                </div>
              </div>

              <div
                className={`status ${
                  f.status.includes("✔")
                    ? "done"
                    : f.status.includes("❌")
                    ? "fail"
                    : "running"
                }`}
              >
                {f.status}
              </div>
            </div>
          ))}
        </div>
      </div>

      {!converting && jobId && (
        <div className="downloadActions">
          <button
            className="primaryBtn downloadBtn"
            onClick={() => downloadZip(0)}
          >
            📦 Download 
          </button>
          <br /> <br />
            <button
              className="secondaryBtn downloadBtn"
              onClick={() => downloadZip(1)}
            >
              🧩📦 Download & (Merged)
            </button>
        </div>
      )}
    </div>
  );
}
