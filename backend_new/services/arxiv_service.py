"""arXiv API integration service"""
import requests
import xml.etree.ElementTree as ET
import time
from typing import List, Dict, Optional


class ArxivService:
    """Service for interacting with arXiv API"""

    BASE_URL = "http://export.arxiv.org/api/query"

    @staticmethod
    def search_by_title(title: str, max_results: int = 5) -> List[Dict]:
        """Search arXiv by paper title"""
        try:
            clean_title = title.replace('"', '').strip()

            params = {
                'search_query': f'ti:"{clean_title}"',
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }

            response = requests.get(ArxivService.BASE_URL, params=params, timeout=30)

            if response.status_code == 200:
                return ArxivService._parse_arxiv_response(response.text)
            else:
                print(f"[WARN] arXiv API returned status {response.status_code}")
                return []

        except Exception as e:
            print(f"[ERROR] arXiv search failed: {e}")
            return []

    @staticmethod
    def _parse_arxiv_response(xml_text: str) -> List[Dict]:
        """Parse arXiv XML response"""
        try:
            root = ET.fromstring(xml_text)

            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            papers = []

            for entry in root.findall('atom:entry', ns):
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None and name.text:
                        authors.append(name.text)

                pdf_url = None
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        pdf_url = link.get('href')
                        break

                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                published_elem = entry.find('atom:published', ns)
                arxiv_id_elem = entry.find('atom:id', ns)

                paper = {
                    'title': title_elem.text.strip() if title_elem is not None else None,
                    'abstract': summary_elem.text.strip() if summary_elem is not None else None,
                    'authors': ', '.join(authors),
                    'pdf_url': pdf_url,
                    'arxiv_id': arxiv_id_elem.text.strip() if arxiv_id_elem is not None else None,
                    'year': published_elem.text[:4] if published_elem is not None else None,
                    'source': 'arXiv'
                }

                papers.append(paper)

            return papers

        except Exception as e:
            print(f"[ERROR] Failed to parse arXiv response: {e}")
            return []

    @staticmethod
    def download_pdf(pdf_url: str, max_retries: int = 3) -> Optional[bytes]:
        """Download PDF from arXiv with retry logic"""
        for attempt in range(max_retries):
            try:
                response = requests.get(pdf_url, timeout=60)

                if response.status_code == 200:
                    return response.content
                elif response.status_code == 202:
                    print(f"[INFO] arXiv PDF generating (202), retry {attempt + 1}/{max_retries}")
                    time.sleep(5 * (attempt + 1))
                    continue
                elif response.status_code == 404:
                    print(f"[WARN] arXiv PDF not found (404): {pdf_url}")
                    return None
                else:
                    print(f"[WARN] arXiv returned status {response.status_code}")
                    return None

            except Exception as e:
                print(f"[ERROR] arXiv PDF download failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)

        return None


def search_arxiv_for_paper(title: str, authors: str = None) -> Optional[Dict]:
    """Search arXiv for a specific paper and return best match"""
    results = ArxivService.search_by_title(title, max_results=3)

    if not results:
        return None

    return results[0]

