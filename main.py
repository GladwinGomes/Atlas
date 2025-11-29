import asyncio
import json
import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

from description import fact_check_with_consensus, display_result
from database import get_unverified_claims, mark_verified
from update import send_verified_claim_to_backend

# Backend configuration
BACKEND_URL = "http://localhost:5000/"  # Change to your backend URL
BACKEND_ENDPOINT = "/api/claims/claimsWithVerification"  # Change to your backend endpoint


app = FastAPI(title="Fact Checker API", version="1.0.0")


class ClaimRequest(BaseModel):
    claim: str


class FactCheckResponse(BaseModel):
    claim: str
    verdict: str
    score: int
    explanation_snippet: str
    urls: List[str]
    explanation: str
    sources: List[dict]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Fact Checker API is running",
        "endpoints": {
            "GET /": "Health check",
            "GET /claims/unverified": "Get all unverified claims",
            "POST /fact-check": "Fact-check a single claim",
            "POST /fact-check/batch": "Fact-check multiple claims",
            "POST /fact-check/all": "Fact-check all unverified claims from database"
        }
    }


@app.get("/claims/unverified")
async def get_unverified():
    """Fetch all unverified claims from database"""
    try:
        res = get_unverified_claims()
        claims = [item['resolvedClaim'] for item in res]
        return {
            "count": len(claims),
            "claims": claims
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/fact-check", response_model=FactCheckResponse)
async def fact_check_single(request: ClaimRequest):
    """Fact-check a single claim"""
    if not request.claim or len(request.claim.strip()) == 0:
        raise HTTPException(status_code=400, detail="Claim cannot be empty")
    
    try:
        result = await fact_check_with_consensus(request.claim)
        
        # Send result to backend
        await send_to_backend(result)
        
        return FactCheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fact-check error: {str(e)}")


@app.post("/fact-check/batch")
async def fact_check_batch(requests: List[ClaimRequest]):
    """Fact-check multiple claims concurrently"""
    if not requests:
        raise HTTPException(status_code=400, detail="No claims provided")
    
    if len(requests) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 claims per request")
    
    try:
        results = await asyncio.gather(*[
            fact_check_with_consensus(req.claim) for req in requests
        ])
        
        return {
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch fact-check error: {str(e)}")


@app.post("/fact-check/all")
async def fact_check_all():
    """Fact-check all unverified claims from database (sequentially)"""
    try:
        res = get_unverified_claims()
        claims = [item['resolvedClaim'] for item in res]
        
        if not claims:
            return {
                "count": 0,
                "message": "No unverified claims found",
                "results": []
            }
        
        print(f"\n📋 Fact-checking {len(claims)} claims...\n")
        
        results = []
        for i, claim in enumerate(claims, 1):
            print(f"\n[{i}/{len(claims)}] Processing claim...")
            result = await fact_check_with_consensus(claim)
            results.append(result)
        
        return {
            "count": len(results),
            "message": f"Successfully fact-checked {len(results)} claims",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database or fact-check error: {str(e)}")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Fact Checker API"
    }


background_task = None


async def send_to_backend(result: dict):
    """Send fact-check result to backend server"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}{BACKEND_ENDPOINT}",
                json=result,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200 or response.status == 201:
                    print(f"✅ Sent to backend: {result['claim'][:50]}...")
                    return True
                else:
                    print(f"⚠️  Backend returned {response.status}: {await response.text()}")
                    return False
    except Exception as e:
        print(f"❌ Failed to send to backend: {str(e)}")
        return False


async def continuous_fact_check():
    """Background task that continuously fact-checks all unverified claims"""
    global background_task
    while True:
        try:
            print("\n" + "="*70)
            print("🤖 AGENTIC FACT-CHECKER: Running background fact-check cycle")
            print("="*70)
            
            res = get_unverified_claims()
            
            if not res or len(res) == 0:
                print("✅ No unverified claims found. Waiting for next cycle...\n")
            else:
                print(f"\n📋 Fact-checking {len(res)} claims...\n")
                
                for i, doc in enumerate(res, 1):
                    claim = doc['resolvedClaim']
                    claim_id = doc['_id']
                    
                    print(f"\n[{i}/{len(res)}] Processing claim: {claim[:60]}...")
                    result = await fact_check_with_consensus(claim)
                    print(f"✅ Result: {result['verdict']} (Confidence: {result['score']}%)")
                    
                    # Send result to backend
                    backend_sent = await send_to_backend(result)
                    
                    # Mark as verified in database ONLY if backend accepted it
                    if backend_sent:
                        try:
                            mark_verified(claim_id)
                            print(f"✅ Marked as verified in database")
                        except Exception as e:
                            print(f"⚠️  Failed to mark as verified: {str(e)}")
                    else:
                        print(f"⚠️  Skipped marking as verified (backend failed)")
            
            # Wait 5 minutes before next cycle (adjust as needed)
            print(f"\n⏰ Next fact-check cycle in 5 minutes...\n")
            await asyncio.sleep(300)
            
        except Exception as e:
            print(f"\n❌ Error in background fact-check: {str(e)}")
            print(f"⏰ Retrying in 1 minute...\n")
            await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    """Start background fact-checking task on server startup"""
    global background_task
    print("\n🚀 Server starting up...")
    print("🤖 Starting agentic fact-checker background task...\n")
    background_task = asyncio.create_task(continuous_fact_check())


@app.on_event("shutdown")
async def shutdown_event():
    """Cancel background task on server shutdown"""
    global background_task
    if background_task:
        background_task.cancel()
        print("\n⛔ Background fact-checker stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)