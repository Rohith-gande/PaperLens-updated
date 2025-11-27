import React, { useState, useEffect, useRef } from 'react';
import { fetchPaper, askQuestion } from '../services/api';

export default function ChatModal({ paper, token, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [paperReady, setPaperReady] = useState(false);
  const [processingPaper, setProcessingPaper] = useState(true);
  const [sourceType, setSourceType] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initializePaper();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializePaper = async () => {
    setProcessingPaper(true);

    const pdfUrl = paper.url || paper.pdf_url || paper.paper?.url;

    if (!pdfUrl) {
      setMessages([{
        role: 'system',
        content: 'Sorry, no PDF URL found for this paper. Unable to process.'
      }]);
      setProcessingPaper(false);
      return;
    }

    try {
      const paperInfo = {
        title: paper.title,
        authors: paper.authors,
        year: paper.year,
        abstract: paper.abstract,
        url: pdfUrl,
        pdf_url: paper.pdf_url || pdfUrl,
        externalIds: paper.external_ids || paper.externalIds || {},
      };

      const result = await fetchPaper(pdfUrl, paper.title, paperInfo, token);
      setSourceType(result.source_type);
      setPaperReady(true);

      let sourceMsg = '';
      if (result.source_type === 'semantic_scholar_pdf') {
        sourceMsg = '📄 Successfully processed full paper (Semantic Scholar PDF)';
      } else if (result.source_type === 'arxiv_pdf') {
        sourceMsg = '📄 Successfully processed full paper (arXiv PDF)';
      } else if (result.source_type === 'metadata') {
        sourceMsg = '📋 Using paper metadata only (abstract + title). Full text not available.';
      } else {
        sourceMsg = '⚠️ Limited data available. Will use general knowledge when needed.';
      }

      setMessages([{
        role: 'assistant',
        content: `I'm ready to answer questions about: "${paper.title}"\n\nWhat would you like to know?`,
        sourceType: result.source_type
      }]);
    } catch (err) {
      console.error('Paper processing error:', err);
      setMessages([{
        role: 'system',
        content: 'Failed to process the paper. The PDF might not be accessible or there was a processing error. You can still try asking questions.'
      }]);
      setPaperReady(true);
    } finally {
      setProcessingPaper(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !paperReady) return;

    const userMessage = input.trim();
    setInput('');

    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const pdfUrl = paper.url || paper.pdf_url || paper.paper?.url;

      const paperInfo = {
        title: paper.title,
        authors: paper.authors,
        year: paper.year,
        abstract: paper.abstract,
        url: pdfUrl,
        pdf_url: paper.pdf_url || pdfUrl,
        externalIds: paper.external_ids || paper.externalIds || {},
      };

      const response = await askQuestion(pdfUrl, userMessage, paperInfo, token);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer,
        //confidence: response.confidence,
        // confidenceLabel: response.confidence_label,
        sourceType: response.source_type,
        citation: response.citation,
        disclaimer: response.disclaimer
      }]);
    } catch (err) {
      console.error('Question error:', err);
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Failed to get answer. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const quickAsk = async (template) => {
    if (loading || !paperReady) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: template }]);
    setLoading(true);
    try {
      const pdfUrl = paper.url || paper.pdf_url || paper.paper?.url;
      const paperInfo = {
        title: paper.title,
        authors: paper.authors,
        year: paper.year,
        abstract: paper.abstract,
        url: pdfUrl,
        pdf_url: paper.pdf_url || pdfUrl,
        externalIds: paper.external_ids || paper.externalIds || {},
      };
      const response = await askQuestion(pdfUrl, template, paperInfo, token);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer || 'No answer.',
        //confidence: response.confidence,
        sourceType: response.source_type,
        disclaimer: response.disclaimer,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: 'Failed to get answer. Try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div 
        className="modal"
        onClick={(e) => e.stopPropagation()}
        data-testid="chat-modal"
      >
        {/* Header */}
        <div className="modal-header">
          <div style={{ flex: 1, marginRight: 'var(--spacing-md)' }}>
            <h2 className="modal-title">{paper.title || paper.paper?.title}</h2>
            <p className="modal-subtitle">
              {paper.authors || paper.paper?.authors} {paper.year && `(${paper.year})`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="modal-close"
            data-testid="close-chat-btn"
          >
            <svg style={{ width: '1.5rem', height: '1.5rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="modal-body" data-testid="chat-messages">
          {/* Quick suggestions */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => quickAsk('Summarize this paper in 5 bullet points.')}>Summarize</button>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => quickAsk('What are the main contributions of this paper?')}>Contributions</button>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => quickAsk('Describe the methodology and key components.')}>Methods</button>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => quickAsk('Summarize the key results and metrics.')}>Results</button>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => quickAsk('What are the limitations and future work?')}>Limitations</button>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => quickAsk('List 5 open questions or future directions implied by this work.')}>Open questions</button>
          </div>
          {processingPaper && (
            <div className="processing-indicator">
              <div className="processing-spinner"></div>
              <p>Processing paper PDF...</p>
            </div>
          )}

          <div className="chat-messages">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`chat-message ${
                  message.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'
                }`}
              >
                <div className={`chat-message-content ${message.role === 'system' ? 'chat-message-system' : ''}`}>
                  {message.role === 'assistant' && (
                    <div className="chat-assistant-header">
                      <div className="chat-assistant-avatar">
                        <svg style={{ width: '1rem', height: '1rem', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                      <span className="chat-assistant-name">AI Assistant</span>
                      {/* {message.confidence !== undefined && (
                        <div className="confidence-badge" title={message.confidenceLabel || ''}>
                          <svg style={{ width: '0.875rem', height: '0.875rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{message.confidence}%</span>
                        </div>
                      )} */}
                    </div>
                  )}
                  <p style={{ whiteSpace: 'pre-wrap' }}>{message.content}</p>
                  {message.disclaimer && (
                    <div className="answer-disclaimer">
                      ⚠️ {message.disclaimer}
                    </div>
                  )}
                 
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-message chat-message-assistant">
                <div className="chat-message-content">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="modal-footer">
          <form onSubmit={handleSendMessage} className="chat-input-container">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={paperReady ? "Ask a question about this paper..." : "Processing paper..."}
              disabled={loading || !paperReady}
              className="chat-input"
              data-testid="chat-input"
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !paperReady}
              className="btn btn-primary"
              data-testid="send-message-btn"
            >
              {loading ? (
                <div className="spinner-sm"></div>
              ) : (
                <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
