from database import db
import requests
import json
from config import Config

def mark_verified(claim_id):
    claims = db['claims']
    claims.update_one(
        {"_id": claim_id},
        {"$set": {"verified": True}}
    )


def send_verified_claim_to_backend(claim, verdict, score, explanation_snippet, urls, explanation, sources):
    # Fix verdict: ensure it's valid for the schema
    VALID_VERDICTS = {
        "Likely True",
        "Likely False",
        "Uncertain",
        "Unverified",
        "Partially True",
        "Partially False",
        "Very Likely False"
    }

    if verdict not in VALID_VERDICTS:
        verdict = "Unverified"   # Default fallback

    # Fix each source to match Mongo schema exactly
    formatted_sources = []
    for s in sources:
        formatted_sources.append({
            "title": s.get("title", "Unknown"),
            "link": s.get("url") or s.get("link") or "",
            "snippet": s.get("snippet", "")
        })

    # Check if backend already has this claim
    try:
        check_response = requests.get(
            f"{Config.NODE_BACKEND_URL}/api/verifiedClaims/check",
            params={"claim": claim, "verdict": verdict}
        )

        if check_response.status_code == 200 and check_response.json().get("exists"):
            print("Claim already exists. Skipping.")
            return

    except Exception as e:
        print("Error checking duplicate claim:", str(e))
        return

    # Payload matching EXACT Mongo schema
    payload = {
        "claim": claim,
        "verdict": verdict,
        "score": score,
        "explanation_snippet": explanation_snippet,
        "urls": urls,
        "explanation": explanation,
        "sources": formatted_sources
    }

    try:
        response = requests.post(
            f"{Config.NODE_BACKEND_URL}/api/verifiedClaims/create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in (200, 201):
            print("Verified claim saved to Node backend.")
        else:
            print("Failed to save verified claim:", response.text)

    except Exception as e:
        print("Error sending verified claim:", str(e))
