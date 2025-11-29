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

def mark_verified(claim_id):
    # Update MongoDB to set verified: true
    collection.update_one(
        {"_id": claim_id},
        {"$set": {"verified": True}}
    )