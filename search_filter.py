from urllib.parse import urlparse

HIGH_TRUST = [
    # Government & International Agencies
    ".gov", "nih.gov", "cdc.gov", "noaa.gov", "usgs.gov", "fda.gov",
    "who.int", "un.org", "esa.int", "ecdc.europa.eu",

    # Top universities (trusted research)
    "harvard.edu", "mit.edu", "stanford.edu", "ox.ac.uk", "cam.ac.uk",
    "yale.edu", "princeton.edu", "berkeley.edu", "columbia.edu",
    "uchicago.edu", "johnshopkins.edu", "ucl.ac.uk",

    # Peer-reviewed science journals
    "nature.com", "science.org", "thelancet.com", "nejm.org", "jama.com",

    # Medical institutions & hospitals
    "mayoclinic.org", "clevelandclinic.org", "mskcc.org", "mdanderson.org",
]

MEDIUM_TRUST = [
    # Major news outlets
    "bbc.com", "reuters.com", "apnews.com", "nytimes.com", "theguardian.com",

    # Popular science publishers
    "scientificamerican.com", "nationalgeographic.com", "livescience.com",
    "space.com", "sciencedaily.com",

    # Educational platforms
    "khanacademy.org", "britannica.com", "howstuffworks.com", "smithsonianmag.com",
]

LOW_TRUST = [
    "blogspot", "wordpress", "substack", "medium.com",
    "quora.com", "reddit.com", "answers.com", "ask.com",
    "facebook.com", "instagram.com", "tiktok.com", "x.com",
    "naturalnews", "mercola", "activistpost", "beforeitsnews"
]

MISINFO_KEYWORDS = [
    "miracle cure", "secret remedy", "hidden cure", "flat earth",
    "detox cleanse", "no side effects", "ancient secret", "cancer cure",
    "suppressed cure", "government hiding", "earth is flat", "miracle solution",
]

FACT_CHECK_KEYWORDS = [
    "evidence", "study", "research", "data shows", "verified",
    "peer-reviewed", "clinical trial", "scientific consensus",
    "fact check", "meta-analysis",
]



def get_domain(url):
    return urlparse(url).netloc.lower()

def domain_trust(url):
    domain = get_domain(url)
    score = 0.5

    if any(k in domain for k in HIGH_TRUST):
        score += 0.6
    elif any(k in domain for k in MEDIUM_TRUST):
        score += 0.3
    elif any(k in domain for k in LOW_TRUST):
        score -= 0.3

    return max(0, min(1, score))