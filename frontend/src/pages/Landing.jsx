import React from 'react';
import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="landing-nav-container">
          <Link to="/" className="header-logo">
            <div className="header-logo-icon">
              <svg style={{ width: '1.5rem', height: '1.5rem', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span className="header-logo-text">PaperLens</span>
          </Link>
          <div className="flex items-center gap-md">
            <Link
              to="/login"
              className="btn btn-ghost"
              data-testid="nav-login-btn"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="btn btn-primary"
              data-testid="nav-register-btn"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-container">
          <div className="landing-badge">
            AI-Powered Research Assistant
          </div>
          <h1 className="landing-hero-title">
            Unlock Research Papers
            <br />
            <span className="landing-hero-gradient">
              with AI Intelligence
            </span>
          </h1>
          <p className="landing-hero-description">
            Search, analyze, and interact with research papers using advanced AI.
            Get instant answers to your questions with RAG-powered insights.
          </p>
          <div className="landing-hero-cta">
            <Link
              to="/register"
              className="btn btn-primary btn-xl"
              style={{ boxShadow: '0 20px 40px rgba(37, 99, 235, 0.4)' }}
              data-testid="hero-get-started-btn"
            >
              Start Researching
            </Link>
            <a
              href="#features"
              className="btn btn-outline btn-xl"
              data-testid="hero-learn-more-btn"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="landing-features">
        <div className="landing-features-container">
          <div className="landing-features-header">
            <h2 className="landing-features-title">Powerful Features</h2>
            <p className="landing-features-description">Everything you need for efficient research</p>
          </div>

          <div className="landing-features-grid">
            {/* Feature 1 */}
            <div className="landing-feature-card" data-testid="feature-card-search">
              <div className="landing-feature-icon">
                <svg style={{ width: '2rem', height: '2rem', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="landing-feature-title">Smart Search</h3>
              <p className="landing-feature-description">
                Search millions of research papers from Semantic Scholar with intelligent ranking based on relevance.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="landing-feature-card" data-testid="feature-card-rag">
              <div className="landing-feature-icon">
                <svg style={{ width: '2rem', height: '2rem', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="landing-feature-title">RAG-Powered Q&A</h3>
              <p className="landing-feature-description">
                Ask questions about any paper and get accurate answers extracted from the content using AI.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="landing-feature-card" data-testid="feature-card-history">
              <div className="landing-feature-icon">
                <svg style={{ width: '2rem', height: '2rem', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="landing-feature-title">Research History</h3>
              <p className="landing-feature-description">
                Keep track of papers you've explored and quickly access your research history anytime.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="landing-cta">
        <div className="landing-cta-container">
          <h2 className="landing-cta-title">
            Ready to Transform Your Research?
          </h2>
          <p className="landing-cta-description">
            Join researchers using AI to accelerate their discoveries
          </p>
          <Link
            to="/register"
            className="btn btn-xl"
            style={{ 
              background: 'white', 
              color: 'var(--color-primary)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)'
            }}
            data-testid="cta-get-started-btn"
          >
            Get Started for Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-container">
          <div className="flex items-center justify-center gap-sm" style={{ marginBottom: '1rem' }}>
            <div className="header-logo-icon" style={{ width: '2rem', height: '2rem' }}>
              <svg style={{ width: '1.25rem', height: '1.25rem', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'white' }}>PaperLens</span>
          </div>
          <p>© 2025 PaperLens. Powered by AI.</p>
        </div>
      </footer>
    </div>
  );
}
