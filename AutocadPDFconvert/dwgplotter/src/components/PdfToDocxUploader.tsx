import React, { useState } from "react";
import { convertPdfToDocx } from "../api/convertPdfToDocx";
import "./PdfToDocxUploader.css"; // <-- add this import

const PdfToDocxUploader: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [previewURL, setPreviewURL] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0] || null;
    setFile(picked);
    setMessage(null);

    if (previewURL) {
      URL.revokeObjectURL(previewURL);
      setPreviewURL(null);
    }

    if (picked) {
      const url = URL.createObjectURL(picked);
      setPreviewURL(url);
    }
  }

  async function handleConvert() {
    if (!file) return;
    setLoading(true);
    setMessage(null);

    try {
      const { blob, filename } = await convertPdfToDocx(file);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setMessage("✅ Conversion completed. DOCX download started.");
    } catch (err) {
      console.error(err);
      setMessage("❌ Conversion failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="pdf-page">
      <div className="pdf-card">
        <div className="pdf-header">
          <h1 className="pdf-title">PDF → DOCX Converter</h1>
          <p className="pdf-subtitle">
            Upload a PDF file and automatically convert it into a Word document.
          </p>
        </div>

        <div className="pdf-layout">
          {/* Left: upload + button */}
          <div className="pdf-left">
            <label className="pdf-upload-box">
              <div className="pdf-upload-inner">
                {!file ? (
                  <>
                    <div className="pdf-upload-icon">📄</div>
                    <div className="pdf-upload-text-main">
                      Click to choose a PDF file
                    </div>
                    <div className="pdf-upload-text-sub">
                      or drag & drop it here
                    </div>
                  </>
                ) : (
                  <>
                    <div className="pdf-upload-icon">📄</div>
                    <div className="pdf-upload-text-main">{file.name}</div>
                    <div className="pdf-upload-text-sub">
                      Click again to change file
                    </div>
                  </>
                )}
              </div>
              <input
                type="file"
                accept="application/pdf"
                className="pdf-file-input"
                onChange={handleFileSelect}
              />
            </label>

            <button
              className={
                "pdf-button" +
                (loading || !file ? " pdf-button-disabled" : "")
              }
              onClick={handleConvert}
              disabled={loading || !file}
            >
              {loading ? "Converting…" : "Convert to DOCX"}
            </button>

            {message && <div className="pdf-message">{message}</div>}
          </div>

          {/* Right: preview */}
          <div className="pdf-right">
            <div className="pdf-preview-header">PDF Preview</div>
            <div className="pdf-preview-body">
              {previewURL ? (
                <iframe
                  title="PDF Preview"
                  src={previewURL}
                  className="pdf-preview-frame"
                />
              ) : (
                <div className="pdf-preview-placeholder">
                  No file selected yet.
                  <br />
                  Choose a PDF on the left to see a preview here.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PdfToDocxUploader;
