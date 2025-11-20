"""Semantic Scholar API integration service"""
import asyncio
import httpx
from typing import List, Dict, Optional
import requests


class SemanticScholarService:
    """Service for interacting with Semantic Scholar API"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    @staticmethod
    async def search_papers(query: str, limit: int = 20, retries: int = 5) -> List[Dict]:
        """Search papers using Semantic Scholar API with retry logic"""
        url = f"{SemanticScholarService.BASE_URL}/paper/search"
        params = {
            "query": query,
            "fields": "title,abstract,authors,url,year,openAccessPdf,citationCount,venue,externalIds,publicationTypes",
            "limit": limit,
        }

        delay = 5
        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(retries):
                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        papers = [
                            {
                                "title": p.get("title"),
                                "abstract": p.get("abstract"),
                                "authors": ", ".join([a["name"] for a in p.get("authors", [])]),
                                "year": p.get("year"),
                                "url": p.get("url"),
                                "pdf_url": (p.get("openAccessPdf") or {}).get("url"),
                                "citation_count": p.get("citationCount", 0),
                                "venue": p.get("venue"),
                                "external_ids": p.get("externalIds", {}),
                                "publication_types": p.get("publicationTypes", []),
                                "open_access": bool(p.get("openAccessPdf"))
                            }
                            for p in data.get("data", [])
                        ]
                        print(f"[DEBUG] Fetched {len(papers)} papers for query: '{query}'")
                        return papers
                    elif response.status_code == 429:
                        print(f"[WARN] Rate limited. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        raise Exception(f"Semantic Scholar API error: {response.status_code}")
                except Exception as e:
                    print(f"[ERROR] Fetch attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(delay)
                    delay *= 2

        raise Exception("Failed to fetch papers after retries")

    @staticmethod
    def get_paper_pdf_url(paper_url: str, external_ids: Optional[Dict] = None, title: str = '') -> Optional[str]:
        """Fetch PDF URL from Semantic Scholar for a specific paper"""
        try:
            # Extract paper ID from URL if needed
            if external_ids and external_ids.get('DOI'):
                s2_paper_id = external_ids['DOI']
                api_url = f"{SemanticScholarService.BASE_URL}/paper/DOI:{s2_paper_id}"
            elif 'semanticscholar.org' in paper_url:
                parts = paper_url.rstrip('/').split('/')
                s2_paper_id = parts[-1]
                api_url = f"{SemanticScholarService.BASE_URL}/paper/{s2_paper_id}"
            else:
                return None

            params = {'fields': 'openAccessPdf,externalIds'}
            response = requests.get(api_url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                open_access_pdf = data.get('openAccessPdf')
                if open_access_pdf and open_access_pdf.get('url'):
                    print(f"[INFO] Found Semantic Scholar PDF: {open_access_pdf['url']}")
                    return open_access_pdf['url']

            # Search by title as fallback
            if title:
                try:
                    api_search = f"{SemanticScholarService.BASE_URL}/paper/search"
                    params = {'query': title.strip(), 'fields': 'openAccessPdf,externalIds', 'limit': 1}
                    resp = requests.get(api_search, params=params, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        hits = data.get('data') or []
                        if hits:
                            hit = hits[0]
                            oapdf = (hit.get('openAccessPdf') or {}).get('url')
                            if oapdf:
                                print(f"[INFO] Found S2 PDF via search: {oapdf}")
                                return oapdf
                except Exception as e:
                    print(f"[WARN] S2 search by title failed: {e}")

            return None

        except Exception as e:
            print(f"[ERROR] Failed to fetch S2 PDF URL: {e}")
            return None

