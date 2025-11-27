const API_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_BACKEND_URL)
  ? import.meta.env.VITE_BACKEND_URL
  : (typeof window !== 'undefined' ? (window.__BACKEND_URL__ || 'http://localhost:8000') : 'http://localhost:8000');

// Helper to get cached data
const getCachedData = (key) => {
  try {
    const cached = localStorage.getItem(key);
    if (cached) {
      const { data, timestamp } = JSON.parse(cached);
      // Cache valid for 1 hour
      if (Date.now() - timestamp < 3600000) {
        return data;
      }
    }
  } catch (e) {
    console.error('Cache error:', e);
  }
  return null;
};

// Helper to set cached data
const setCachedData = (key, data) => {
  try {
    localStorage.setItem(key, JSON.stringify({
      data,
      timestamp: Date.now()
    }));
  } catch (e) {
    console.error('Cache error:', e);
  }
};

// ==================== CORE API METHODS ====================

export const searchPapers = async ({ query, page = 1, pageSize = 5 }, token) => {
  if (!query || !query.trim()) {
    throw new Error('Query is required');
  }

  // Check cache first
  const normalizedQuery = query.toLowerCase().trim();
  const cacheKey = `search_${normalizedQuery}_${page}_${pageSize}`;
  const cached = getCachedData(cacheKey);
  
  if (cached) {
    console.log('Using cached results for:', query);
    return cached;
  }
  
  // Fetch from API
  const response = await fetch(`${API_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ query, page, page_size: pageSize })
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch papers');
  }
  
  const data = await response.json();
  
  // Cache the results
  setCachedData(cacheKey, data);
  
  return data;
};

export const fetchPaper = async (pdfUrl, paperTitle, paperInfo, token) => {
  const response = await fetch(`${API_URL}/api/fetch-paper`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ 
      pdf_url: pdfUrl, 
      paper_title: paperTitle,
      paper_info: paperInfo 
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch paper');
  }
  
  return response.json();
};

export const askQuestion = async (pdfUrl, question, paperInfo, token) => {
  const response = await fetch(`${API_URL}/api/ask-question`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ 
      pdf_url: pdfUrl, 
      question,
      paper_info: paperInfo 
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to get answer');
  }
  
  return response.json();
};

export const comparePapers = async (paperIds, papersInfo, comparisonQuery, token) => {
  const response = await fetch(`${API_URL}/api/compare-papers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      paper_ids: paperIds,
      papers_info: papersInfo,
      comparison_query: comparisonQuery
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to compare papers');
  }
  
  return response.json();
};

export const savePaper = async (paper, token) => {
  const response = await fetch(`${API_URL}/api/user/save-paper`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ paper })
  });
  
  if (!response.ok) {
    throw new Error('Failed to save paper');
  }
  
  return response.json();
};

export const getUserPapers = async (token) => {
  const response = await fetch(`${API_URL}/api/user/papers`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to get user papers');
  }
  
  return response.json();
};
