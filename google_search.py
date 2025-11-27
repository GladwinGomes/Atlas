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

    try:
        response = requests.get(url, params=params, timeout=10)       
        if response.status_code != 200:
            print(f"Google Search API error: {response.status_code}")
            return []
        
        data = response.json()       
        if data is None or "items" not in data:
            return []
        
        results = []
        for item in data["items"]:
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        return results
    
    except requests.exceptions.Timeout:
        print("Google Search API timeout")
        return []
    except requests.exceptions.ConnectionError:
        print("Google Search API connection error")
        return []
    except Exception as e:
        print(f"Error calling Google Search API: {str(e)}")
        return []