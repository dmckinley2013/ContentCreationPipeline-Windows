import React, { useState } from "react";
import { Upload, X, File, Image, Music, Video } from "lucide-react";

const FileUploader = () => {
  const [files, setFiles] = useState({
    document: null,
    image: null,
    audio: [],
    video: null,
  });

  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const handleFileSelect = (type, event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (type === "audio") {
      setFiles((prev) => ({
        ...prev,
        audio: [...prev.audio, file],
      }));
    } else {
      setFiles((prev) => ({
        ...prev,
        [type]: file,
      }));
    }
  };

  const removeFile = (type, index = null) => {
    if (type === "audio") {
      setFiles((prev) => ({
        ...prev,
        audio: prev.audio.filter((_, i) => i !== index),
      }));
    } else {
      setFiles((prev) => ({
        ...prev,
        [type]: null,
      }));
    }
  };

  const handleUpload = async () => {
    if (
      !files.document &&
      !files.image &&
      files.audio.length === 0 &&
      !files.video
    ) {
      setError("Please select at least one file to upload");
      return;
    }

    setStatus("Uploading...");
    setError("");

    try {
      const formData = new FormData();

      if (files.document) formData.append("document", files.document);
      if (files.image) formData.append("image", files.image);
      files.audio.forEach((audioFile) => formData.append("audio", audioFile));
      if (files.video) formData.append("video", files.video);

      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");

      setStatus("Files uploaded successfully!");
      setFiles({
        document: null,
        image: null,
        audio: [],
        video: null,
      });
    } catch (err) {
      setError(err.message);
      setStatus("");
    }
  };

  const FileSection = ({ type, icon: Icon, accept, fileData }) => {
    const isAudio = type === "audio";
    const currentFiles = isAudio ? fileData.audio : fileData[type];

    return (
      <div className="stat-card">
        <h3 className="text-lg font-semibold mb-2 capitalize">{type}</h3>

        <div className="flex flex-col gap-2">
          {isAudio ? (
            currentFiles.map((file, index) => (
              <div
                key={index}
                className="content-type document flex items-center justify-between p-2"
              >
                <div className="flex items-center gap-2">
                  <Icon size={20} />
                  <span className="truncate">{file.name}</span>
                </div>
                <button
                  onClick={() => removeFile("audio", index)}
                  className="status-indicator disconnected"
                >
                  <X size={20} />
                </button>
              </div>
            ))
          ) : currentFiles ? (
            <div className="content-type document flex items-center justify-between p-2">
              <div className="flex items-center gap-2">
                <Icon size={20} />
                <span className="truncate">{currentFiles.name}</span>
              </div>
              <button
                onClick={() => removeFile(type)}
                className="status-indicator disconnected"
              >
                <X size={20} />
              </button>
            </div>
          ) : null}

          <label className="cursor-pointer">
            <div className="table-controls">
              <input
                type="file"
                accept={accept}
                onChange={(e) => handleFileSelect(type, e)}
                className="hidden"
              />
              <span className="text-secondary">
                {isAudio
                  ? "Add Audio File"
                  : `Select ${type.charAt(0).toUpperCase() + type.slice(1)}`}
              </span>
            </div>
          </label>
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard-wrapper">
      <div className="dashboard-header">
        <h1 className="text-2xl font-bold text-center">File Uploader</h1>
      </div>

      <div className="stats-section">
        <FileSection
          type="document"
          icon={File}
          accept=".pdf"
          fileData={files}
        />
        <FileSection
          type="image"
          icon={Image}
          accept="image/*"
          fileData={files}
        />
        <FileSection
          type="audio"
          icon={Music}
          accept="audio/*"
          fileData={files}
        />
        <FileSection
          type="video"
          icon={Video}
          accept="video/*"
          fileData={files}
        />
      </div>

      {error && (
        <div className="stats-section">
          <div className="status-indicator disconnected">
            <span>{error}</span>
          </div>
        </div>
      )}

      {status && (
        <div className="stats-section">
          <div className="status-indicator connected">
            <span>{status}</span>
          </div>
        </div>
      )}

      <div className="table-container">
        <button
          onClick={handleUpload}
          className="page-button flex items-center justify-center gap-2 w-full"
          style={{
            background: "var(--primary-color)",
            color: "white",
            border: "none",
            padding: "1rem",
          }}
        >
          <Upload size={20} />
          Upload Files
        </button>
      </div>
    </div>
  );
};

export default FileUploader;
