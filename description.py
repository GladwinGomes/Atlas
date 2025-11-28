import json
import asyncio
from google_search import search_text
from extract_article import extract_article_text
from search_filter import get_domain, HIGH_TRUST, MEDIUM_TRUST
from llama import llama  # Now async from previous conversion
from update import mark_verified, send_verified_claim_to_backend
from database import get_unverified_claims


def clean_claim(claim: str) -> str:
    """Clean up claim text by removing YouTube metadata and excessive noise."""
    if "YouTube" in claim or "youtube.com" in claim:
        segments = [s.strip() for s in claim.split('·') if s.strip() and len(s.strip()) > 20]
        if segments:
            for seg in segments:
                if not any(char.isdigit() for char in seg[:5]):
                    return seg
            return segments[-1]
    return claim[:200].strip()


def get_trust_level(url):
    domain = get_domain(url)
    if any(k in domain for k in HIGH_TRUST):
        return "high"
    elif any(k in domain for k in MEDIUM_TRUST):
        return "medium"
    return "low"


def verdict_map(v):
    """Map LLM verdicts to standard format."""
    mapping = {
        "TRUE": "Likely True",
        "FALSE": "Likely False",
        "MIXED": "Uncertain",
        "UNVERIFIABLE": "Unverified",
        "NO TRUSTED SOURCES": "Unverified",
        "INSUFFICIENT DATA": "Unverified",
        "ERROR": "Unverified",
        "PARSE ERROR": "Unverified",
    }
    return mapping.get(v, "Unverified")


def parse_json_response(response: str) -> dict:
    """Safely parse JSON from LLM response."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"    Direct JSON parse failed: {str(e)[:50]}")
    
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start != -1 and end > start:
            json_str = response[start:end]
            print(f"    Extracted JSON substring, trying to parse...")
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"    Extracted JSON parse failed: {str(e)[:50]}")
    
    print(f"    ❌ Could not parse any JSON")
    return {
        "verdict": "PARSE ERROR",
        "confidence": 0,
        "summary": "Could not parse LLM response",
        "reasoning": f"Raw response: {response[:150]}",
        "key_quotes": ""
    }


async def fact_check_with_consensus(claim: str) -> dict:
    """
    Search for claim, extract articles from trusted sources,
    and ask LLM to synthesize consensus verdict.
    """
    claim_cleaned = clean_claim(claim)
    
    print(f"  🔍 Searching for sources...")
    results = search_text(claim_cleaned)
    print(f"  Found {len(results)} results")
    
    if not results or len(results) == 0:
        print("  ❌ No search results found")
        return {
            "claim": claim,
            "verdict": "Unverified",
            "score": 20,
            "explanation_snippet": "No search results found",
            "urls": [],
            "explanation": "No search results found",
            "sources": []
        }
    
    print(f"  📰 Extracting trusted sources from {len(results)} results...")
    trusted_articles = []
    
    for result in results:
        try:
            trust_level = get_trust_level(result["link"])
            
            if trust_level in ["high", "medium"]:
                print(f"    ✅ Extracting {result['title'][:50]}... ({trust_level} trust)")
                article_text = extract_article_text(result["link"])
                
                if article_text and len(article_text) > 100:
                    trusted_articles.append({
                        "title": result["title"],
                        "url": result["link"],
                        "trust": trust_level,
                        "text": article_text[:5000]
                    })
                    print(f"      ↳ Successfully extracted ({len(article_text)} chars)")
                else:
                    print(f"      ↳ Text too short or empty")
        except Exception as e:
            print(f"    ⚠️  Could not extract {result.get('link', 'unknown')}: {str(e)[:50]}")
            continue
    
    if not trusted_articles:
        print("  ❌ No trusted sources found")
        return {
            "claim": claim,
            "verdict": "Unverified",
            "score": 30,
            "explanation_snippet": "Search results only from low-trust domains",
            "urls": [],
            "explanation": "Search results only from low-trust domains",
            "sources": []
        }
    
    print(f"  🤖 Extracted {len(trusted_articles)} trusted articles, querying LLM...")
    
    article_context = "\n\n---SOURCE BREAK---\n\n".join([
        f"[{article['trust'].upper()} TRUST] {article['title']}\nURL: {article['url']}\n\n{article['text']}"
        for article in trusted_articles
    ])
    
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
        response = await llama(prompt)  # Now properly awaited
        
        if not response or response.strip() == "":
            print("  ❌ LLM did not respond")
            return {
                "claim": claim,
                "verdict": "Unverified",
                "score": 0,
                "explanation_snippet": "LLM did not respond",
                "urls": [a["url"] for a in trusted_articles],
                "explanation": "Local LLM server returned empty response",
                "sources": [
                    {
                        "title": a["title"],
                        "link": a["url"],
                        "snippet": a["text"][:150] if a["text"] else ""
                    }
                    for a in trusted_articles
                ]
            }
        
        print("  ✅ LLM responded, parsing JSON...")
        result = parse_json_response(response)
        
    except Exception as e:
        print(f"  ❌ LLM error: {str(e)}")
        result = {
            "verdict": "ERROR",
            "confidence": 0,
            "summary": "LLM processing failed",
            "reasoning": f"Error: {str(e)[:100]}",
            "key_quotes": ""
        }
    
    mapped_verdict = verdict_map(result.get("verdict", "UNVERIFIABLE"))
    confidence = result.get("confidence", 0)
    
    final_result = {
        "claim": claim,
        "verdict": mapped_verdict,
        "score": int(confidence * 100),
        "explanation_snippet": result.get("summary", "No summary available"),
        "urls": [a["url"] for a in trusted_articles],
        "explanation": result.get("reasoning", "No reasoning available"),
        "sources": [
            {
                "title": a["title"],
                "link": a["url"],
                "snippet": a["text"][:150] if a["text"] else ""
            }
            for a in trusted_articles
        ]
    }
    
    return final_result


def display_result(result):
    """Pretty print the result."""
    print(f"\n{'='*70}")
    print(f"CLAIM: {result['claim']}")
    print(f"{'='*70}")
    print(f"VERDICT: {result['verdict']}")
    print(f"CONFIDENCE SCORE: {result.get('score', 'N/A')}%")
    print(f"\nSUMMARY: {result.get('explanation_snippet', 'N/A')}")
    print(f"\nREASONING:\n{result.get('explanation', 'N/A')}")
    
    print(f"\nSOURCES USED: {len(result.get('sources', []))}")
    for i, source in enumerate(result.get('sources', []), 1):
        print(f"  {i}. {source['title']}")
        print(f"     {source['link']}")
        if source.get('snippet'):
            print(f"     Snippet: {source['snippet'][:100]}...")
    print(f"{'='*70}\n")


async def main():
    """Main async entry point."""
    claims = get_unverified_claims()
    print(f"\n📋 Found {len(claims)} unverified claims.\n")

    for doc in claims:
        claim_id = doc["_id"]
        claim_text = doc["resolvedClaim"]

        print(f"\n📝 Fact-checking: '{claim_text}'")

        # Run fact checker
        result = await fact_check_with_consensus(claim_text)
        display_result(result)

        # Mark as verified in MongoDB
        mark_verified(claim_id)
        print(f"✅ Marked claim {claim_id} as verified in DB")

        try:
            send_verified_claim_to_backend(
                claim=result["claim"],
                verdict=result["verdict"],
                score=result["score"],
                explanation_snippet=result["explanation_snippet"],
                urls=result["urls"],
                explanation=result["explanation"],
                sources=result["sources"],
            )
            print("✅ Sent verified claim to Node backend\n")
        except Exception as e:
            print(f"⚠️  Failed to send to backend: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())