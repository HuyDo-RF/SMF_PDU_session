from pymongo import MongoClient

def setup_database():
    client = MongoClient("mongodb://localhost:27017/")

    # SMF database
    smfdb = client["smfdb"]
    if "pdu_sessions" not in smfdb.list_collection_names():
        smfdb.create_collection("pdu_sessions")
    smfdb.pdu_sessions.create_index("supi")
    smfdb.pdu_sessions.create_index("pduSessionId")

    # UDM database
    udmdb = client["udmdb"]
    if "subscribers" not in udmdb.list_collection_names():
        udmdb.create_collection("subscribers")
    udmdb.subscribers.create_index("imsi", unique=True)
    if udmdb.subscribers.count_documents({}) == 0:
        udmdb.subscribers.insert_one({
            "imsi": "imsi-452040000000001",
            "msisdn": "msisdn-84900000001",
            "status": "ACTIVE"
        })

    print("Database setup completed successfully!")

if __name__ == "__main__":
    setup_database()
