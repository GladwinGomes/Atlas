import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

    query = "In October, Aishat was found dead in a rented flat in neighbouring Armenia. Police say Aishat was murdered."