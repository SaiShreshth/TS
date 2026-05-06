import { useEffect, useRef, useState } from "react";
import axios from "axios";

const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const buildStagesForType = (type) => {
  if (type === "image") {
    return [
      { name: "Upload" },
      { name: "Image embedding" },
      { name: "Knowledge graph update" },
    ];
  }
  if (type === "audio") {
    return [
      { name: "Upload" },
      { name: "Transcription" },
      { name: "RAG indexing" },
      { name: "Knowledge graph update" },
    ];
  }
  return [
    { name: "Upload" },
    { name: "RAG indexing" },
    { name: "Knowledge graph update" },
    { name: "Summary" },
  ];
};

const makeId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [uploadType, setUploadType] = useState("pdf");
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const threadRef = useRef(null);

  useEffect(() => {
    if (!threadRef.current) {
      return;
    }
    threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [messages, isQuerying]);

  const handleFileChange = (event) => {
    setFile(event.target.files[0] || null);
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus({
        message: "Please choose a file to upload.",
        stages: [],
        type: uploadType,
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    let endpoint = "/upload/pdf";
    if (uploadType === "image") {
      endpoint = "/upload/image";
    } else if (uploadType === "audio") {
      endpoint = "/upload/audio";
    }

    const initialStages = buildStagesForType(uploadType).map((stage, index) => ({
      ...stage,
      status: index === 0 ? "active" : "pending",
    }));

    setIsUploading(true);
    setUploadStatus({
      fileName: file.name,
      type: uploadType,
      message: "Uploading and processing...",
      stages: initialStages,
    });

    try {
      const response = await axios.post(`${baseUrl}${endpoint}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const responseStages = response.data.stages?.length
        ? response.data.stages
        : buildStagesForType(uploadType).map((stage) => ({
            ...stage,
            status: "done",
          }));

      setUploadStatus({
        fileName: file.name,
        type: uploadType,
        message: response.data.message || "Upload complete",
        stages: responseStages,
        summary: response.data.summary || "",
        stats: response.data.stats || null,
      });
    } catch (error) {
      setUploadStatus({
        fileName: file.name,
        type: uploadType,
        message:
          "Upload failed: " + (error.response?.data?.detail || error.message),
        stages: initialStages.map((stage) => ({
          ...stage,
          status: "error",
        })),
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text) {
      return;
    }

    const userMessage = { id: makeId(), role: "user", text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsQuerying(true);

    try {
      const response = await axios.post(`${baseUrl}/query`, { text });
      const payload = response.data.response;
      const assistantMessage = {
        id: makeId(),
        role: "assistant",
        answer: payload.answer,
        explanation: payload.explanation,
        context: payload.context || [],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "assistant",
          answer: "Query failed",
          explanation: error.response?.data?.detail || error.message,
          context: [],
        },
      ]);
    } finally {
      setIsQuerying(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="page">
      <style>{`
        :root {
          color-scheme: light;
          --ink: #1d1b16;
          --muted: #6a655b;
          --accent: #1f6f5c;
          --accent-strong: #0f4b3b;
          --warm: #c86a2b;
          --panel: rgba(255, 255, 255, 0.86);
          --stroke: rgba(36, 30, 22, 0.08);
          --shadow: 0 24px 60px rgba(15, 24, 20, 0.12);
        }

        .page {
          min-height: 100vh;
          background: radial-gradient(circle at top, #f8f2ea, #e7f3f1 55%, #f4efe6 100%);
          color: var(--ink);
          font-family: "Space Grotesk", sans-serif;
        }

        .header {
          padding: 32px 40px 8px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .title {
          font-size: 28px;
          font-weight: 600;
          letter-spacing: 0.4px;
        }

        .subtitle {
          color: var(--muted);
          font-size: 14px;
        }

        .layout {
          display: grid;
          grid-template-columns: minmax(280px, 360px) 1fr;
          gap: 24px;
          padding: 20px 40px 48px;
        }

        .stack {
          display: flex;
          flex-direction: column;
          gap: 18px;
        }

        .panel {
          background: var(--panel);
          border: 1px solid var(--stroke);
          border-radius: 18px;
          padding: 18px;
          box-shadow: var(--shadow);
          animation: fadeUp 0.4s ease both;
        }

        .panel h3 {
          margin: 0 0 10px;
          font-size: 16px;
          letter-spacing: 0.2px;
        }

        .upload-row {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          margin-bottom: 12px;
        }

        .radio {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
        }

        .file-input {
          width: 100%;
          padding: 10px;
          border-radius: 10px;
          border: 1px dashed var(--stroke);
          background: #fff;
          font-size: 13px;
        }

        .primary-btn {
          margin-top: 12px;
          padding: 10px 16px;
          border-radius: 12px;
          border: none;
          background: var(--accent);
          color: #fff;
          font-weight: 500;
          cursor: pointer;
          transition: transform 0.2s ease, background 0.2s ease;
        }

        .primary-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .primary-btn:hover:not(:disabled) {
          background: var(--accent-strong);
          transform: translateY(-1px);
        }

        .status-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: var(--muted);
          margin-bottom: 10px;
        }

        .pill {
          background: rgba(31, 111, 92, 0.12);
          color: var(--accent-strong);
          padding: 4px 8px;
          border-radius: 999px;
          font-size: 11px;
          font-weight: 600;
        }

        .status-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: grid;
          gap: 8px;
        }

        .status-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: var(--muted);
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #d9d4cb;
        }

        .status-dot.done {
          background: var(--accent);
        }

        .status-dot.active {
          background: var(--warm);
          box-shadow: 0 0 0 4px rgba(200, 106, 43, 0.2);
        }

        .status-dot.error {
          background: #a93b2b;
        }

        .summary-box {
          margin-top: 12px;
          background: rgba(15, 75, 59, 0.08);
          border-radius: 12px;
          padding: 12px;
          font-size: 13px;
          color: #1b2a25;
        }

        .chat-panel {
          display: flex;
          flex-direction: column;
          min-height: 520px;
        }

        .chat-thread {
          flex: 1;
          overflow-y: auto;
          padding-right: 8px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .message-row {
          display: flex;
        }

        .message-row.user {
          justify-content: flex-end;
        }

        .bubble {
          max-width: 78%;
          padding: 12px 14px;
          border-radius: 16px;
          font-size: 14px;
          line-height: 1.4;
          animation: fadeUp 0.3s ease both;
        }

        .bubble.user {
          background: var(--accent);
          color: #fff;
          border-bottom-right-radius: 4px;
        }

        .bubble.assistant {
          background: #fff;
          border: 1px solid var(--stroke);
          border-bottom-left-radius: 4px;
        }

        .assistant-title {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--muted);
          margin-bottom: 6px;
        }

        .context-block {
          margin-top: 10px;
          padding-top: 8px;
          border-top: 1px solid var(--stroke);
          font-size: 12px;
          color: var(--muted);
        }

        .context-block summary {
          cursor: pointer;
          font-weight: 600;
        }

        .composer {
          margin-top: 12px;
          display: flex;
          gap: 10px;
        }

        .composer textarea {
          flex: 1;
          border-radius: 12px;
          border: 1px solid var(--stroke);
          padding: 10px 12px;
          font-family: "Space Grotesk", sans-serif;
          font-size: 14px;
          resize: none;
          min-height: 52px;
        }

        .send-btn {
          padding: 10px 16px;
          border-radius: 12px;
          border: none;
          background: var(--warm);
          color: #fff;
          font-weight: 600;
          cursor: pointer;
        }

        .muted {
          color: var(--muted);
          font-size: 13px;
        }

        @keyframes fadeUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (max-width: 900px) {
          .layout {
            grid-template-columns: 1fr;
            padding: 16px 20px 36px;
          }

          .header {
            padding: 24px 20px 8px;
          }

          .bubble {
            max-width: 100%;
          }
        }
      `}</style>

      <header className="header">
        <div className="title">Legal / Policy Document Assistant</div>
        <div className="subtitle">
          Upload documents, watch RAG + knowledge graph progress, and chat for
          explanations.
        </div>
      </header>

      <main className="layout">
        <aside className="stack">
          <section className="panel">
            <h3>Upload document</h3>
            <div className="upload-row">
              <label className="radio">
                <input
                  type="radio"
                  checked={uploadType === "pdf"}
                  onChange={() => setUploadType("pdf")}
                />
                PDF
              </label>
              <label className="radio">
                <input
                  type="radio"
                  checked={uploadType === "image"}
                  onChange={() => setUploadType("image")}
                />
                Image
              </label>
              <label className="radio">
                <input
                  type="radio"
                  checked={uploadType === "audio"}
                  onChange={() => setUploadType("audio")}
                />
                Audio
              </label>
            </div>
            <input className="file-input" type="file" onChange={handleFileChange} />
            <button
              className="primary-btn"
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading ? "Processing..." : "Upload"}
            </button>
          </section>

          <section className="panel">
            <h3>Ingestion status</h3>
            {uploadStatus ? (
              <>
                <div className="status-meta">
                  <span className="pill">{uploadStatus.type?.toUpperCase()}</span>
                  <span>{uploadStatus.fileName}</span>
                </div>
                <div className="muted">{uploadStatus.message}</div>
                <ul className="status-list" style={{ marginTop: 10 }}>
                  {uploadStatus.stages?.map((stage) => (
                    <li key={stage.name} className="status-item">
                      <span
                        className={`status-dot ${stage.status || "pending"}`}
                      />
                      <span>{stage.name}</span>
                      {stage.detail ? (
                        <span className="muted">({stage.detail})</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
                {uploadStatus.stats ? (
                  <div className="status-meta" style={{ marginTop: 10 }}>
                    <span>{uploadStatus.stats.pages} pages</span>
                    <span>|</span>
                    <span>{uploadStatus.stats.chunks} chunks</span>
                  </div>
                ) : null}
                {uploadStatus.summary ? (
                  <div className="summary-box">
                    <strong>PDF summary</strong>
                    <div>{uploadStatus.summary}</div>
                  </div>
                ) : null}
              </>
            ) : (
              <div className="muted">
                No uploads yet. Progress will appear here after processing.
              </div>
            )}
          </section>
        </aside>

        <section className="panel chat-panel">
          <h3>Chat</h3>
          <div className="chat-thread" ref={threadRef}>
            {messages.length === 0 ? (
              <div className="muted">
                Ask a question about your uploaded documents to start the
                conversation.
              </div>
            ) : null}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message-row ${message.role}`}
              >
                <div className={`bubble ${message.role}`}>
                  {message.role === "user" ? (
                    <div>{message.text}</div>
                  ) : (
                    <>
                      <div className="assistant-title">Assistant</div>
                      <div>{message.answer}</div>
                      {message.explanation ? (
                        <div className="context-block">
                          <strong>Explanation</strong>
                          <div>{message.explanation}</div>
                        </div>
                      ) : null}
                      {message.context?.length ? (
                        <details className="context-block">
                          <summary>Context</summary>
                          <ul>
                            {message.context.map((item, index) => (
                              <li key={`${message.id}-${index}`}>{item}</li>
                            ))}
                          </ul>
                        </details>
                      ) : null}
                    </>
                  )}
                </div>
              </div>
            ))}
            {isQuerying ? (
              <div className="message-row assistant">
                <div className="bubble assistant">
                  <div className="assistant-title">Assistant</div>
                  <div className="muted">Thinking...</div>
                </div>
              </div>
            ) : null}
          </div>

          <div className="composer">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about obligations, clauses, or key facts..."
            />
            <button className="send-btn" onClick={handleSend} disabled={isQuerying}>
              Send
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;