import requests
from readability import Document
from bs4 import BeautifulSoup

def extract_article_text(url: str, max_retries=2):
    """
    Extract article text from URL with retry logic and proper headers.
    
    Args:
        url: The URL to extract from
        max_retries: Number of retry attempts on failure
    
    Returns:
        Extracted text (up to 5000 chars) or empty string on failure
    """
    # Skip PDFs and documents that require special handling
    if url.lower().endswith(('.pdf', '.doc', '.docx', '.xlsx')):
        print(f"  ⏭️  Skipping document file: {url[:40]}...")
        return ""
    
    # Headers to mimic a browser request (some sites block requests without User-Agent)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5, headers=headers, allow_redirects=True)
            response.raise_for_status()
            
            html = response.text
            
            # Check if we got meaningful content
            if len(html) < 500:
                print(f"  📄 Response too small ({len(html)} bytes)")
                continue

            doc = Document(html)
            summary_html = doc.summary()

            soup = BeautifulSoup(summary_html, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            
            if len(text) < 100:
                print(f"  📄 Extracted text too short ({len(text)} chars)")
                continue
            
            return text[:5000]

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"  🔒 Access denied (403) - skipping")
                return ""
            elif e.response.status_code == 404:
                print(f"  ❌ Not found (404) - skipping")
                return ""
            else:
                print(f"  ⚠️  HTTP Error {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                continue
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️  Timeout (attempt {attempt + 1}/{max_retries})")
            continue
            
        except requests.exceptions.ConnectionError:
            print(f"  🌐 Connection error (attempt {attempt + 1}/{max_retries})")
            continue
            
        except Exception as e:
            error_msg = str(e)[:40]
            print(f"  ❌ Error: {error_msg} (attempt {attempt + 1}/{max_retries})")
            continue
    
    return ""