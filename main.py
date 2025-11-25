from description import fact_check_with_consensus, display_result
from database import res

for i in res:
        claims = i

def main():  
    for claim in claims: 
        print(f"\n🔍 Fact-checking: '{claim}'")
        print("Searching trusted sources and synthesizing verdict...\n")
    
        result = fact_check_with_consensus(claim)
        display_result(result)

if __name__ == "__main__":
    main()