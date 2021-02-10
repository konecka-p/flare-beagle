from pymongo import MongoClient

client = MongoClient()

storeDB = client.storeDB
flare_beagleDB = client.flare_beagleDB

if __name__ == "__main__":
    pass