import asyncio
from description import fact_check_with_consensus, display_result
from database import get_unverified_claims

async def main():
    res = get_unverified_claims()
    claims = [item['resolvedClaim'] for item in res]
    
    print(f"\n📋 Found {len(claims)} claims to fact-check.\n")
    
    # Run all claims concurrently
    results = await asyncio.gather(*[
        fact_check_with_consensus(claim) for claim in claims
    ])
    
    for result in results:
        display_result(result)


if __name__ == "__main__":
    asyncio.run(main())