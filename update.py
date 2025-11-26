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
    #Check if backend already has this claim
    try:
        check_response = requests.get(
            f"{Config.NODE_BACKEND_URL}/api/verified-claims/check",
            params={"claim": claim, "verdict": verdict}
        )

        if check_response.status_code == 200 and check_response.json().get("exists"):
            print("Claim already exists. Skipping.")
            return  # do NOT send duplicate

    except Exception as e:
        print("Error checking duplicate claim:", str(e))
        return

    #If it doesn't exist, send the new one
    payload = {
        "claim": claim,
        "verdict": verdict,
        "score": score,
        "explanation_snippet": explanation_snippet,
        "urls": urls,
        "explanation": explanation,
        "sources": sources
    }

    try:
        response = requests.post(
            f"{Config.NODE_BACKEND_URL}/api/verified-claims",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in (200, 201):
            print("Verified claim saved to Node backend.")
        else:
            print("Failed to save verified claim:", response.text)

    except Exception as e:
        print("Error sending verified claim:", str(e))
