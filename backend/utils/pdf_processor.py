"""PDF downloading and text extraction utilities"""
import io
import requests
import PyPDF2
import time
from typing import Optional
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, parse_qs


def is_pdf_bytes(data: Optional[bytes]) -> bool:
    """Check if bytes represent a valid PDF"""
    try:
        return bool(data) and data[:4] == b'%PDF'
    except Exception:
        return False


def resolve_pdf_url(url: str) -> Optional[str]:
    """Resolve landing page URLs to direct PDF URLs (arXiv, OpenReview)"""
    try:
        u = (url or '').strip()
        if not u:
            return None
        if u.lower().endswith('.pdf'):
            return u

        # arXiv abs -> pdf
        if 'arxiv.org/abs/' in u:
            paper_id = u.split('arxiv.org/abs/')[1].split('#')[0].split('?')[0]
            return f"https://arxiv.org/pdf/{paper_id}.pdf"

        # arXiv /pdf without .pdf
        if 'arxiv.org/pdf/' in u and not u.lower().endswith('.pdf'):
            return u + '.pdf'

        # OpenReview forum -> pdf?id=
        if 'openreview.net/forum' in u and 'id=' in u:
            parsed = urlparse(u)
            q = parse_qs(parsed.query)
            pid = q.get('id', [None])[0]
            if pid:
                return f"https://openreview.net/pdf?id={pid}"

        # Follow redirects to a direct PDF
        try:
            r = requests.get(u, allow_redirects=True, timeout=25, stream=True)
            if r.status_code == 200 and 'pdf' in (r.headers.get('Content-Type') or '').lower():
                return r.url
        except Exception:
            pass

        # Simple HTML crawl for .pdf links
        try:
            r2 = requests.get(u, timeout=25)
            if r2.status_code == 200 and 'text/html' in (r2.headers.get('Content-Type') or '') and r2.text:
                pdf_links = []

                class LinkParser(HTMLParser):
                    def handle_starttag(self, tag, attrs):
                        if tag.lower() == 'a':
                            href = dict(attrs).get('href', '')
                            if href and '.pdf' in href.lower():
                                pdf_links.append(href)

                parser = LinkParser()
                parser.feed(r2.text)

                for href in pdf_links:
                    candidate = urljoin(u, href)
                    try:
                        ok = requests.head(candidate, allow_redirects=True, timeout=15)
                        if 'pdf' in (ok.headers.get('Content-Type') or '').lower():
                            return candidate
                    except Exception:
                        continue
        except Exception:
            pass

        return None
    except Exception:
        return None


def download_pdf(url: str, max_retries: int = 3) -> Optional[bytes]:
    """Download PDF with retry logic and status code handling"""
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (PaperLens/1.0)'}
            response = requests.get(url, timeout=60, allow_redirects=True, headers=headers, stream=True)

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                raw_bytes = response.content if response.content else response.raw.read()
                if 'pdf' in content_type.lower() or url.lower().endswith('.pdf') or is_pdf_bytes(raw_bytes):
                    return raw_bytes
                else:
                    print(f"[WARN] URL returned non-PDF content: {content_type}")
                    return None

            elif response.status_code == 202:
                wait_time = 5 * (attempt + 1)
                print(f"[INFO] PDF processing (202), waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)
                continue

            elif response.status_code == 404:
                print(f"[WARN] PDF not found (404): {url}")
                return None

            else:
                print(f"[WARN] Unexpected status code {response.status_code} for {url}")
                return None

        except requests.exceptions.Timeout:
            print(f"[WARN] Timeout downloading PDF (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(3)
        except Exception as e:
            print(f"[ERROR] Failed to download PDF (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(3)

    return None


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text = ""
        for page in pdf_reader.pages:
            try:
                page_text = page.extract_text()
            except Exception:
                page_text = None
            if page_text:
                text += page_text + "\n"

        return text.strip()
    except Exception as e:
        print(f"[ERROR] PDF text extraction failed: {e}")
        return ""

