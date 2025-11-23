import re
from extract_article import extract_article_text
from config import Config

claim = Config.query

POSITIVE_KEYWORDS = [
    "effective", "safe", "shown to", "evidence", "proven", "clinical trial",
    "study shows", "study found", "research shows", "findings", "data shows"
]

NEGATIVE_KEYWORDS = [
    "dangerous", "cause harm", "cause cancer", "hoax", "myth",
    "serious side effect", "unproven", "no evidence", "debunked", "false",
    "not effective", "does not", "cannot"
]

STOPWORDS = {
    "the","a","an","of","to","in","on","and","or","is","are","was",
    "were","be","being","been","for","with","as","at","by","it",
    "that","this","those","these","from","but","if","then","so","not"
}


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_keywords(claim):
    words = re.findall(r"[a-zA-Z]+", claim.lower())
    # Filter: length > 4 AND not stopword
    return [w for w in words if w not in STOPWORDS and len(w) > 3]


def match_density_multiplier(fraction):
    if fraction > 0.7:
        return 1.5
    if fraction > 0.5:
        return 1.3
    if fraction > 0.3:
        return 1.1
    return 1.0

def sentence_matches_claim(sentence, claim_keywords, min_fraction=0.15):
    sentence_lower = sentence.lower()
    matches = sum(1 for word in claim_keywords if word in sentence_lower)
    min_required = max(2, int(len(claim_keywords) * min_fraction))
    if matches < min_required:
        return 0
    
    base_fraction = matches / len(claim_keywords)
    boosted_score = base_fraction * match_density_multiplier(base_fraction)
    boosted_score = min(1.0, boosted_score)
    return boosted_score

def context_score(sentence):
    """Score based on language strength and evidence markers."""
    sentence_lower = sentence.lower()
    score = 0.5  # neutral baseline
    
    # Check for negation context (look back 10 words)
    words = sentence_lower.split()
    for i, word in enumerate(words):
        if any(k in word for k in POSITIVE_KEYWORDS):
            # Check if negated in last 5 words
            context = " ".join(words[max(0, i-5):i])
            if any(neg in context for neg in ["not", "no ", "cannot", "does not"]):
                score -= 0.3
            else:
                score += 0.4
        
        if any(k in word for k in NEGATIVE_KEYWORDS):
            score -= 0.2
    
    return max(-0.5, min(0.5, score))

def score_sentence(sentence, claim_keywords):
    match_score = sentence_matches_claim(sentence, claim_keywords)
    if match_score == 0:
        return 0

    context = context_score(sentence)
    final_score = match_score * (1 + context)
    return max(0, min(1, final_score))

def article_sentence_score(url, sf_score, claim):
    article_text = extract_article_text(url)
    if not article_text:
        return sf_score

    sentences = split_into_sentences(article_text)
    claim_keywords = extract_keywords(claim)
    
    if not claim_keywords:
        return sf_score

    scores = []
    for s in sentences:
        sc = score_sentence(s, claim_keywords)
        if sc > 0:
            scores.append(sc)

    if scores:
        # Weight by sentence length (longer = more substantial)
        weighted_scores = []
        for s, score in zip(sentences, [score_sentence(s, claim_keywords) for s in sentences]):
            if score > 0:
                length_weight = min(1.2, 1 + len(s.split()) / 50)
                weighted_scores.append(score * length_weight)
        
        article_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else sf_score
        return max(0, min(1, article_score))
    
    return sf_score