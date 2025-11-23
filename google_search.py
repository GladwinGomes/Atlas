import requests
from config import Config

def search_text(query: str):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": Config.GOOGLE_API_KEY,
        "cx": Config.GOOGLE_SEARCH_ENGINE_ID,
        "q": query,
        "num": 5
    }

    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json()
    else:
        print("Error:", res.status_code, res.text)
        data = None

    results = []
    if "items" not in data:
        return results

    for item in data["items"]:
        results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")
        })

    return results
