import json
import asyncio
from pymongo import MongoClient
from src.common.http2 import HTTP2Server


class UDMServer:
    def __init__(self, host, port, cert_file, key_file, db_uri):
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.db_client = MongoClient(db_uri)
        self.db = self.db_client.udmdb
        self.http2_server = HTTP2Server(
            host, port, cert_file, key_file, self.handle_request
        )

    async def start(self):
        await self.http2_server.start()

    async def handle_request(self, request):
        path = request['headers'].get(b':path', b'').decode('utf-8')
        method = request['headers'].get(b':method', b'').decode('utf-8')

        if path.startswith('/nudm-sdm/v2/') and method == 'GET':
            # trích xuất IMSI from path
            parts = path.split('/')
            if len(parts) >= 4:
                imsi = parts[3]

                # Xác minh IMSI trong database
                subscriber = await self.verify_imsi(imsi)

                if subscriber:
                    response = {
                        "imsi": imsi,
                        "status": "verified",
                        "subscriptionData": {
                            "dnn": "v-internet"
                        }
                    }
                    return json.dumps(response).encode('utf-8')
                else:
                    return json.dumps({"error": "IMSI not found"}).encode('utf-8')

        return json.dumps({"error": "Not found"}).encode('utf-8')

    async def verify_imsi(self, imsi):
        # Kiểm tra nếu IMSI tồn tại trong database
        subscriber = self.db.subscribers.find_one({"imsi": imsi})
        return subscriber is not None
