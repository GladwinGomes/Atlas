from config import Config
import pymongo

client = pymongo.MongoClient(Config.MONGODB_URI)   
db = client[Config.MONGODB_DB_NAME]                
collection = db['claims']                         

data = collection.find()

res = []
for document in data:
    res.append(document.get('resolvedClaim'))
