import requests
from readability import Document
from bs4 import BeautifulSoup

def extract_article_text(url: str):
    try:
        response = requests.get(url, timeout=3)
        html = response.text

        doc = Document(html)
        summary_html = doc.summary()

        soup = BeautifulSoup(summary_html, "html.parser")

        text = soup.get_text(separator=" ", strip=True)
        return text[:5000]

    except Exception:
        return ""
