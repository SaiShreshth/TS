import { useState } from "react";
import axios from "axios";

function App() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [file, setFile] = useState(null);
  const [uploadType, setUploadType] = useState("pdf");
  const [loading, setLoading] = useState(false);

  const baseUrl = "http://localhost:8000";

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadMessage("Please choose a file to upload.");
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

    try {
      setLoading(true);
      const response = await axios.post(`${baseUrl}${endpoint}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadMessage(response.data.message);
    } catch (error) {
      setUploadMessage(
        "Upload failed: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    if (!query) {
      return;
    }
    try {
      setLoading(true);
      const response = await axios.post(`${baseUrl}/query`, { text: query });
      setResult(response.data.response);
    } catch (error) {
      setResult({ answer: "Query failed", error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1>Legal / Policy Document Assistant</h1>

      <section style={styles.card}>
        <h2>Upload Document</h2>
        <div style={styles.row}>
          <label>
            <input
              type="radio"
              checked={uploadType === "pdf"}
              onChange={() => setUploadType("pdf")}
            />
            PDF
          </label>
          <label>
            <input
              type="radio"
              checked={uploadType === "image"}
              onChange={() => setUploadType("image")}
            />
            Image
          </label>
          <label>
            <input
              type="radio"
              checked={uploadType === "audio"}
              onChange={() => setUploadType("audio")}
            />
            Audio
          </label>
        </div>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={loading} style={styles.button}>
          Upload
        </button>
        {uploadMessage && <p>{uploadMessage}</p>}
      </section>

      <section style={styles.card}>
        <h2>Ask a Question</h2>
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          rows={4}
          style={styles.textarea}
          placeholder="Enter your legal or policy question"
        />
        <button onClick={handleQuery} disabled={loading} style={styles.button}>
          Query
        </button>
      </section>

      <section style={styles.card}>
        <h2>Response</h2>
        {loading && <p>Working...</p>}
        {result ? (
          <div>
            <p>
              <strong>Answer:</strong> {result.answer}
            </p>
            {result.context && (
              <div>
                <h3>Context</h3>
                <ul>
                  {result.context.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p>Upload files and ask a query to see results.</p>
        )}
      </section>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: 760,
    margin: "24px auto",
    fontFamily: "Arial, sans-serif",
    padding: 16,
  },
  card: {
    border: "1px solid #ddd",
    borderRadius: 10,
    padding: 16,
    marginBottom: 20,
    backgroundColor: "#fff",
  },
  row: {
    display: "flex",
    gap: 16,
    marginBottom: 12,
  },
  textarea: {
    width: "100%",
    padding: 12,
    fontSize: 16,
    borderRadius: 8,
    border: "1px solid #ccc",
  },
  button: {
    marginTop: 12,
    padding: "10px 18px",
    borderRadius: 8,
    backgroundColor: "#0033cc",
    color: "#fff",
    border: "none",
    cursor: "pointer",
  },
};

export default App;