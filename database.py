from config import Config
import pymongo

client = pymongo.MongoClient(Config.MONGODB_URI)   
db = client[Config.MONGODB_DB_NAME]                
collection = db['claims']                         

def get_unverified_claims():

    return list(collection.find(
        {"verified": False},
        {"resolvedClaim": 1, "_id": 1}
    ))