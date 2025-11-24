import requests
import json
import time
from google_search import search_text
from extract_article import extract_article_text
from search_filter import get_domain, HIGH_TRUST, MEDIUM_TRUST
from llama import llama

def get_trust_level(url):
    domain = get_domain(url)
    
    if any(k in domain for k in HIGH_TRUST):
        return "high"
    elif any(k in domain for k in MEDIUM_TRUST):
        return "medium"
    return "low"

def fact_check_with_consensus(claim: str, timeout_per_article=5) -> dict:
    """
    Search for claim, extract articles from trusted sources,
    and ask LLM to synthesize consensus verdict.
    """
    print(f"  Searching for sources...")
    results = search_text(claim)
    
    if not results:
        return {
            "claim": claim,
            "verdict": "INSUFFICIENT DATA",
            "confidence": 0.2,
            "summary": "No search results found",
            "reasoning": "No search results found",
            "key_quotes": "",
            "sources_used": 0,
            "sources": []
        }
    
    print(f"  Found {len(results)} results, extracting trusted sources...")
    trusted_articles = []
    
    for result in results:
        trust_level = get_trust_level(result["link"])
        
        if trust_level in ["high", "medium"]:
            try:
                article_text = extract_article_text(result["link"])
                
                if article_text and len(article_text) > 100:
                    trusted_articles.append({
                        "title": result["title"],
                        "url": result["link"],
                        "trust": trust_level,
                        "text": article_text[:2000]
                    })
            except Exception as e:
                print(f"    ⚠️  Could not extract {result['link']}: {str(e)[:50]}")
                continue
    
    if not trusted_articles:
        return {
            "claim": claim,
            "verdict": "NO TRUSTED SOURCES",
            "confidence": 0.3,
            "summary": "Search results only from low-trust domains",
            "reasoning": "Search results only from low-trust domains",
            "key_quotes": "",
            "sources_used": 0,
            "sources": []
        }
    
    print(f"  Extracted {len(trusted_articles)} trusted articles, querying LLM...")
    
    # Build context from articles
    article_context = "\n\n---SOURCE BREAK---\n\n".join([
        f"[{article['trust'].upper()} TRUST] {article['title']}\nURL: {article['url']}\n\n{article['text']}"
        for article in trusted_articles
    ])
    
    # Ask LLM to synthesize verdict
    prompt = f"""You are a fact-checker. Analyze these articles from trusted sources and determine if the claim is accurate.

CLAIM TO VERIFY: "{claim}"

ARTICLES FROM TRUSTED SOURCES:
{article_context}

Analyze ALL the sources above and provide a final verdict. Consider:
1. Do the sources support, contradict, or are neutral about the claim?
2. Is there consensus among sources?
3. Are there important caveats or nuances?

Respond ONLY with valid JSON (no markdown, no extra text, no explanation before or after):
{{
    "verdict": "TRUE" or "FALSE" or "MIXED" or "UNVERIFIABLE",
    "confidence": 0.95,
    "summary": "One sentence summary of finding",
    "reasoning": "2-3 sentences explaining the consensus from sources",
    "key_quotes": "Most relevant quote(s) from the sources"
}}

Guidelines:
- verdict: TRUE if sources clearly support, FALSE if clearly contradict, MIXED if conflicting, UNVERIFIABLE if insufficient
- confidence: 0.9-1.0 for clear verdicts, 0.7-0.8 for most aligned with nuance, 0.5-0.6 for mixed/conflicting, below 0.5 for insufficient
- Return ONLY the JSON object, nothing else"""

    try:
        response = llama(prompt)
        
        if not response:
            return {
                "claim": claim,
                "verdict": "ERROR",
                "confidence": 0,
                "summary": "LLM did not respond",
                "reasoning": "Local LLM server returned empty response",
                "key_quotes": "",
                "sources_used": len(trusted_articles),
                "sources": [{"title": a["title"], "url": a["url"], "trust": a["trust"]} for a in trusted_articles]
            }
        
        # Parse JSON response
        result = parse_json_response(response)
        
    except Exception as e:
        result = {
            "verdict": "ERROR",
            "confidence": 0,
            "summary": "LLM processing failed",
            "reasoning": f"Error: {str(e)[:100]}",
            "key_quotes": ""
        }
    
    # Add metadata
    result["claim"] = claim
    result["sources_used"] = len(trusted_articles)
    result["sources"] = [{"title": a["title"], "url": a["url"], "trust": a["trust"]} for a in trusted_articles]
    
    return result


def parse_json_response(response: str) -> dict:
    """
    Safely parse JSON from LLM response.
    Handles cases where LLM returns JSON with extra text.
    """
    try:
        # Try direct parsing first
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    try:
        # Try extracting JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start != -1 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # Fallback response
    return {
        "verdict": "PARSE ERROR",
        "confidence": 0,
        "summary": "Could not parse LLM response",
        "reasoning": f"Raw response: {response[:150]}",
        "key_quotes": ""
    }


def display_result(result):
    """Pretty print the result."""
    print(f"\n{'='*70}")
    print(f"CLAIM: {result['claim']}")
    print(f"{'='*70}")
    print(f"VERDICT: {result['verdict']} (Confidence: {result['confidence']:.0%})")
    print(f"\nSUMMARY: {result.get('summary', 'N/A')}")
    print(f"\nREASONING:\n{result.get('reasoning', 'N/A')}")
    
    if result.get('key_quotes'):
        print(f"\nKEY EVIDENCE:\n{result['key_quotes']}")
    
    print(f"\nSOURCES USED: {result['sources_used']}")
    for i, source in enumerate(result.get('sources', []), 1):
        print(f"  {i}. [{source['trust'].upper()}] {source['title']}")
        print(f"     {source['url']}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    test_claims = [
        "The Earth revolves around the Sun once every 365.25 days",
        "Vaccines cause autism",
        "Climate change is caused by human activity",
        "The Great Wall of China is visible from space",
    ]
    
    for claim in test_claims:
        print(f"\n🔍 Fact-checking: '{claim}'")
        result = fact_check_with_consensus(claim)
        display_result(result)