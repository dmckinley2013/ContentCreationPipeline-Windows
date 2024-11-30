import React, { useState } from "react";
import Dashboard from "./components/Dashboard";
import FileUploader from "./components/Uploader";
import "./App.css";

function App() {
  const [page, setPage] = useState("dashboard");

  const renderPage = () => {
    switch (page) {
      case "upload":
        return <FileUploader />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="App">
      <nav className="dashboard-header">
        <div className="header-content">
          <button
            onClick={() => setPage("dashboard")}
            className={`nav-link ${page === "dashboard" ? "active" : ""}`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setPage("upload")}
            className={`nav-link ${page === "upload" ? "active" : ""}`}
          >
            File Uploader
          </button>
        </div>
      </nav>

      <div className="dashboard-wrapper">{renderPage()}</div>
    </div>
  );
}

export default App;
