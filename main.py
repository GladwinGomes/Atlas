from description import fact_check_with_consensus, display_result
from database import get_unverified_claims

res = get_unverified_claims()
claims = [item['resolvedClaim'] for item in res]

def main():  
    for claim in claims: 
        result = fact_check_with_consensus(claim)
        display_result(result)

if __name__ == "__main__":
    main()