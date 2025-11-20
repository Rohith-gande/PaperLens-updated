import React, { useState, useContext, useEffect } from 'react';
import { AuthContext } from '../App';
import { signOut } from 'firebase/auth';
import { auth } from '../firebase';
import { useNavigate } from 'react-router-dom';
import { searchPapers, fetchPaper, comparePapers, savePaper, getUserPapers } from '../services/api';
import SearchBar from '../components/SearchBar';
import PaperCard from '../components/PaperCard';
import ChatModal from '../components/ChatModal';
import HistorySidebar from '../components/HistorySidebar';

export default function Dashboard() {
  const { user, token } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const [query, setQuery] = useState('');
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [showCompare, setShowCompare] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState(null);
  const [showBot, setShowBot] = useState(false);
  const [botMessages, setBotMessages] = useState([]);
  const [botInput, setBotInput] = useState('');
  const [botLoading, setBotLoading] = useState(false);
  const [userPapers, setUserPapers] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    loadUserPapers();
    // Check for saved dark mode preference
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    setDarkMode(savedDarkMode);
    if (savedDarkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, [token]);

  const loadUserPapers = async () => {
    try {
      const response = await getUserPapers(token);
      setUserPapers(response.papers || []);
    } catch (err) {
      console.error('Failed to load user papers:', err);
    }
  };

  const handleSearch = async (searchQuery) => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError('');
    setPapers([]);
    
    try {
      const response = await searchPapers(searchQuery, token);
      setPapers(response.results || []);
    } catch (err) {
      setError('Failed to search papers. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (paper) => {
    setSelectedPaper(paper);
    setShowChat(true);
    
    // Save paper to user's history
    try {
      await savePaper(paper, token);
      loadUserPapers(); // Refresh history
    } catch (err) {
      console.error('Failed to save paper:', err);
    }
  };

  const toggleSelectForCompare = (paper) => {
    setSelectedForCompare((prev) => {
      const exists = prev.find((p) => (p.url || p.pdf_url) === (paper.url || paper.pdf_url));
      if (exists) return prev.filter((p) => (p.url || p.pdf_url) !== (paper.url || paper.pdf_url));
      return [...prev, paper];
    });
  };

  const runCompare = async (comparisonQuery) => {
    const valid = selectedForCompare.filter((p) => (p.url || p.pdf_url || p.paper?.url));
    if (valid.length < 2) return;
    setCompareLoading(true);
    setCompareResult(null);
    try {
      // Ensure vector stores exist via enhanced fetch
      await Promise.all(valid.map((paper) => {
        const pdfUrl = paper.url || paper.pdf_url || paper.paper?.url;
        const paperInfo = {
          title: paper.title,
          authors: paper.authors,
          year: paper.year,
          abstract: paper.abstract,
          url: pdfUrl
        };
        return fetchPaper(pdfUrl, paper.title, paperInfo, token);
      }));

      const paperIds = valid.map((paper) => {
        const url = paper.url || paper.pdf_url || paper.paper?.url;
        // must match backend get_paper_id_from_url hashing; backend uses abs(hash(url)) as string
        // We can't compute Python's hash here; backend maps by URL → paper_id internally when fetching.
        // So send papers_info and let backend retrieve by URL-derived IDs.
        return url; // placeholder; backend uses papers_info order
      });

      const papersInfo = valid.map((paper) => ({
        title: paper.title,
        authors: paper.authors,
        year: paper.year,
        abstract: paper.abstract,
        url: paper.url || paper.pdf_url || paper.paper?.url
      }));

      const result = await comparePapers(paperIds, papersInfo, comparisonQuery, token);
      setCompareResult(result);
    } catch (e) {
      console.error('Comparison failed', e);
      setCompareResult({ comparison: 'Comparison failed. Please try again.' });
    } finally {
      setCompareLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate('/');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode.toString());
    
    if (newDarkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  };

  const sendBotMessage = async (e) => {
    e.preventDefault();
    const msg = botInput.trim();
    if (!msg || botLoading) return;
    setBotInput('');
    setBotMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setBotLoading(true);
    try {
      const res = await chatbotMessage(msg, token);
      setBotMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setBotMessages((prev) => [...prev, { role: 'system', content: 'Chatbot error. Please try again.' }]);
    } finally {
      setBotLoading(false);
    }
  };

  return (
    <div className="dashboard-page">
      {/* Header */}
      <header className="header">
        <div className="header-container">
          <div className="header-logo">
            <div className="header-logo-icon">
              <svg style={{ width: '1.5rem', height: '1.5rem', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span className="header-logo-text">PaperLens</span>
          </div>
          
          <div className="header-nav">
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className={`dark-mode-toggle ${darkMode ? 'active' : ''}`}
              title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              data-testid="dark-mode-toggle"
            >
              <div className="dark-mode-toggle-slider">
                {darkMode ? (
                  <svg className="dark-mode-toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                ) : (
                  <svg className="dark-mode-toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                )}
              </div>
            </button>
            
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="btn btn-ghost"
              data-testid="history-toggle-btn"
            >
              <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>History</span>
            </button>
            
            <div className="header-user-info">
              <p className="header-user-email">{user?.email}</p>
              <button
                onClick={handleLogout}
                className="btn btn-secondary"
                data-testid="logout-btn"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className={`dashboard-layout ${showHistory ? 'has-sidebar' : ''}`}>
        {/* Main Content */}
        <main className="dashboard-main">
          <div className="dashboard-content">
            {/* Search Section */}
            <div className="dashboard-search-section">
              <h1 className="dashboard-search-title">Search Research Papers</h1>
              <p className="dashboard-search-description">Search millions of papers and ask questions using AI</p>
              
              <SearchBar
                value={query}
                onChange={setQuery}
                onSearch={handleSearch}
                loading={loading}
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="dashboard-error" data-testid="search-error-message">
                {error}
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="dashboard-loading">
                <div className="dashboard-loading-content">
                  <div className="dashboard-loading-spinner"></div>
                  <p className="dashboard-loading-text">Searching papers...</p>
                </div>
              </div>
            )}

            {/* Results */}
            {!loading && papers.length > 0 && (
              <div className="dashboard-results">
                <h2 className="dashboard-results-header">
                  Found {papers.length} papers
                </h2>
                <div className="dashboard-results-actions" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <button
                    className="btn btn-secondary"
                    disabled={selectedForCompare.length < 2}
                    onClick={() => { console.log('Compare clicked'); setShowCompare(true); }}
                    type="button"
                    style={{ pointerEvents: 'auto', position: 'relative', zIndex: 2 }}
                  >
                    Compare Selected ({selectedForCompare.length})
                  </button>
                </div>
                <div className="dashboard-results-grid">
                  {papers.map((paper, index) => {
                    const urlKey = paper.url || paper.pdf_url || paper.paper?.url;
                    const isSelected = !!selectedForCompare.find((p) => (p.url || p.pdf_url || p.paper?.url) === urlKey);
                    return (
                      <PaperCard
                        key={index}
                        paper={paper}
                        onAskQuestion={() => handleAskQuestion(paper)}
                        selectable
                        selected={isSelected}
                        onToggleSelect={() => toggleSelectForCompare(paper)}
                      />
                    );
                  })}
                </div>
              </div>
            )}

            {/* No Results */}
            {!loading && query && papers.length === 0 && !error && (
              <div className="dashboard-empty">
                <svg className="dashboard-empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="dashboard-empty-text">No papers found for your query</p>
              </div>
            )}

            {/* Empty State */}
            {!loading && !query && papers.length === 0 && (
              <div className="dashboard-empty">
                <svg className="dashboard-empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <h3 className="dashboard-empty-title">Start Your Research</h3>
                <p className="dashboard-empty-text">Enter a query to search for research papers</p>
              </div>
            )}
          </div>
        </main>

        {/* History Sidebar */}
        <HistorySidebar
          show={showHistory}
          papers={userPapers}
          onSelectPaper={handleAskQuestion}
          onClose={() => setShowHistory(false)}
        />
      </div>

      {/* Chat Modal */}
      {showChat && selectedPaper && (
        <ChatModal
          paper={selectedPaper}
          token={token}
          onClose={() => {
            setShowChat(false);
            setSelectedPaper(null);
          }}
        />
      )}

      {/* Compare Modal (lightweight inline modal) */}
      {showCompare && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" style={{ zIndex: 9999 }}>
          <div className="modal">
            <div className="modal-header">
              <h3>Compare Papers</h3>
              <button className="btn btn-ghost" onClick={() => setShowCompare(false)}>Close</button>
            </div>
            <div className="modal-body">
              {/* Compare suggestions */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <button type="button" className="btn btn-outline btn-sm" disabled={compareLoading || selectedForCompare.length < 2} onClick={() => runCompare('Compare in all aspects: objectives, methods, datasets, results, efficiency, limitations.')}>All aspects</button>
                <button type="button" className="btn btn-outline btn-sm" disabled={compareLoading || selectedForCompare.length < 2} onClick={() => runCompare('Compare the methodologies used in each paper.')}>Methods</button>
                <button type="button" className="btn btn-outline btn-sm" disabled={compareLoading || selectedForCompare.length < 2} onClick={() => runCompare('Compare the key results and reported metrics across the papers.')}>Results</button>
                <button type="button" className="btn btn-outline btn-sm" disabled={compareLoading || selectedForCompare.length < 2} onClick={() => runCompare('Compare limitations and future work discussed in the papers.')}>Limitations</button>
                <button type="button" className="btn btn-outline btn-sm" disabled={compareLoading || selectedForCompare.length < 2} onClick={() => runCompare('Compare datasets and evaluation protocols used by each paper.')}>Datasets</button>
              </div>
              <p>Select at least 2 papers above, then enter a comparison query (e.g., "methods", "results", "limitations").</p>
              <form onSubmit={(e) => { e.preventDefault(); const q = e.target.elements.cq.value.trim(); if (q) runCompare(q); }}>
                <input name="cq" className="input" placeholder="Comparison query (e.g., methods, limitations)" required />
                <button type="submit" className="btn btn-primary" disabled={compareLoading || selectedForCompare.length < 2}>
                  {compareLoading ? 'Comparing...' : 'Run Compare'}
                </button>
              </form>
              {selectedForCompare.length < 2 && (
                <p style={{ marginTop: '0.5rem', color: 'var(--muted-foreground)' }}>Select at least 2 papers with valid links.</p>
              )}
              {compareResult && (
                <div className="comparison-result" style={{ marginTop: '1rem', whiteSpace: 'pre-wrap' }}>
                  {compareResult.comparison || JSON.stringify(compareResult, null, 2)}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Chatbot Modal */}
      {showBot && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" style={{ zIndex: 9999 }}>
          <div className="modal">
            <div className="modal-header">
              <h3>PaperLens Chatbot</h3>
              <button className="btn btn-ghost" onClick={() => setShowBot(false)}>Close</button>
            </div>
            <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div className="chat-log" style={{ maxHeight: '40vh', overflowY: 'auto', padding: '0.5rem', border: '1px solid var(--border)', borderRadius: 8 }}>
                {botMessages.length === 0 && (
                  <p style={{ color: 'var(--muted-foreground)' }}>Ask anything. Uses your configured Gemini API key.</p>
                )}
                {botMessages.map((m, i) => (
                  <div key={i} style={{ margin: '0.25rem 0', whiteSpace: 'pre-wrap' }}>
                    <strong>{m.role === 'user' ? 'You' : m.role === 'assistant' ? 'Assistant' : 'System'}:</strong> {m.content}
                  </div>
                ))}
              </div>
              <form onSubmit={sendBotMessage} className="chat-input-container" style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  value={botInput}
                  onChange={(e) => setBotInput(e.target.value)}
                  placeholder={botLoading ? 'Thinking...' : 'Type a message...'}
                  disabled={botLoading}
                  className="chat-input"
                />
                <button type="submit" className="btn btn-primary" disabled={botLoading || !botInput.trim()}>
                  {botLoading ? 'Sending...' : 'Send'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
