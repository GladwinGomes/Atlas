from urllib.parse import urlparse

def get_domain(url):
    return urlparse(url).netloc.lower()

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