from google_search import search_text
from search_filter import search_results_score
from config import Config
from description import fact_check_with_consensus, display_result

claim = Config.query

def main():   
    print(f"\n🔍 Fact-checking: '{claim}'")
    print("Searching trusted sources and synthesizing verdict...\n")
    
    result = fact_check_with_consensus(claim)
    display_result(result)

if __name__ == "__main__":
    main()











    

# results = search_text(claim)
# rating = search_results_score(results, claim)

# for r in rating:
#     print(f"sf score: {round(r['credibility'], 2)}, deep score: {round(r['article_sentence_score'], 2)} - {r['title']}")

# if rating:
#     avg_sf_score = sum([i["credibility"] for i in rating]) / len(rating)
#     print("Average sf credibility score:", round(avg_sf_score * 100, 2), "%")

#     avg_deep_score = sum([i["article_sentence_score"] for i in rating]) / len(rating)
#     print("Average deep credibility score:", round(avg_deep_score * 100, 2), "%")

#     combined_score = (avg_sf_score * 0.4) + (avg_deep_score * 0.6)
#     print("Combined average credibility score:", round(combined_score * 100, 2), "%")
    
# else:
#     print("No results found.")