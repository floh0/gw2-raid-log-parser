import pymongo
import conf

client = pymongo.MongoClient(conf.mongo["url"], conf.mongo["port"])
db = client["gw2"]
collection = db["logs"]

def insert(object):
	collection.update_one({"account": object.account, "start": object.start}, {"$set": object.__dict__}, upsert=True)

if __name__=="__main__":
	# collection.delete_many({})
	# for a in collection.aggregate([{"$match":{"success":True}}, {"$group" : {"_id":"$account", "count":{"$sum":1}}}, {"$sort":{"count":-1}}]):
	# 	print(a)
	
	i = -1
	for a in collection.aggregate([
		{
			"$project": {
				"account": "$account",
				"boss": "$boss",
				"day": {
					"$dayOfMonth": "$start"
				},
				"month": {
					"$month": "$start"
				}, 
				"year": {
					"$year": "$start"
				}
			}
		}, {
			"$group": {
				"_id": {
					"account": "$account",
					"boss": "$boss",
					"day": "$day",
					"month": "$month",
					"year": "$year"
				},
				"count": {
					"$sum": 1
				}
			}
		}, {
			"$group": {
				"_id":"$_id.account",
				"count": {
					"$sum": 1
				}
			}
		}, {
			"$sort": {
				"count": -1
			}
		}
	]):
		i+=1
		print(i, a)
	

