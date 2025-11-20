import React, { useState, useContext } from "react";
import { searchPapers } from "../services/api";
import ResultCard from "./ResultCard";
import { AuthContext } from "../App";

export default function ResearchQuery() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const { token } = useContext(AuthContext);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await searchPapers(query, token);
      setResults(data.results);
    } catch (error) {
      console.error("Error fetching papers:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-secondary)', padding: 'var(--spacing-xl)' }}>
      <div style={{ marginBottom: 'var(--spacing-xl)' }}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your research query..."
          className="input"
          style={{ width: '100%', height: '5rem', marginBottom: 'var(--spacing-sm)' }}
        />
        <button
          onClick={handleSearch}
          className="btn btn-primary w-full"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
        {results.map((paper, index) => (
          <ResultCard key={index} paper={paper} />
        ))}
      </div>
    </div>
  );
}
