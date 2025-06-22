import json
import asyncio
from src.common.http2 import HTTP2Server
from src.common.models import N1N2MessageTransfer, CreateSessionRequest


class AMFClient:
    def __init__(self, smf_host, smf_port):
        self.smf_host = smf_host
        self.smf_port = smf_port

    async def create_session(self, request: CreateSessionRequest):
        # Client sử dụng giao thức HTTP/2 để gửi request đến SMF
        print(f"Sending Create Session Request to SMF: {request.dict()}")
        return True


class AMFServer:
    def __init__(self, host, port, cert_file, key_file):
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.smf_client = AMFClient("localhost", 8082)
        self.http2_server = HTTP2Server(
            host, port, cert_file, key_file, self.handle_request
        )

    async def start(self):
        await self.http2_server.start()

    async def handle_request(self, request):
        path = request['headers'].get(b':path', b'').decode('utf-8')
        method = request['headers'].get(b':method', b'').decode('utf-8')

        if path.startswith('/namf-comm/v1/ue-context/') and method == 'POST':
            # Xử lý N1N2 Message Transfer
            data = json.loads(request['data'].decode('utf-8'))
            msg = N1N2MessageTransfer(**data)
            print(f"Received N1N2 Message Transfer: {msg.dict()}")

            return json.dumps({"status": "received"}).encode('utf-8')

        return json.dumps({"error": "Not found"}).encode('utf-8')

    async def send_create_session_request(self, request: CreateSessionRequest):
        return await self.smf_client.create_session(request)
