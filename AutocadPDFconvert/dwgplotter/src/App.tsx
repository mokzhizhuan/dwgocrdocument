// src/App.tsx
import React from "react";
import ConvertUploader from "./components/BatchPdfUploader";

function App() {
  return (
    <div className="app-wrapper">
      <div className="app-container">
        <ConvertUploader />
      </div>
    </div>
  );
}

export default App;