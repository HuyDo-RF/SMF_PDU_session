import json
import asyncio
import uuid
from pymongo import MongoClient
from src.common.http2 import HTTP2Server
from src.common.worker_pool import WorkerPool
from src.common.models import CreateSessionRequest, PDUSession, N1N2MessageTransfer


class UDMClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def verify_imsi(self, supi):
        # Triển khai HTTP/2 client để gửi yêu cầu tới UDM
        print(f"Verifying IMSI with UDM: {supi}")
        return True


class UPFClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def establish_pfcp_session(self, request):
        # Triển khai PFCP client để gửi yêu cầu tơi UPF
        print(f"Establishing PFCP Session with UPF: {request}")
        return {
            "seid": 12345,
            "ipAddress": "10.11.22.123",
            "status": "ESTABLISHED"
        }


class AMFClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def send_n1n2_message_transfer(self, supi, msg):
        # Triển khai HTTP/2 client để gửi yêu cầu tới AMF
        print(f"Sending N1N2 Message Transfer to AMF for {supi}: {msg.dict()}")
        return True


class SMFServer:
    def __init__(self, host, port, cert_file, key_file, db_uri):
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.db_client = MongoClient(db_uri)
        self.db = self.db_client.smfdb
        self.worker_pool = WorkerPool(num_workers=10)
        self.udm_client = UDMClient("localhost", 8083)
        self.upf_client = UPFClient("localhost", 8084)
        self.amf_client = AMFClient("localhost", 8081)
        self.http2_server = HTTP2Server(
            host, port, cert_file, key_file, self.handle_request
        )

    async def start(self):
        await self.worker_pool.start()
        await self.http2_server.start()

    async def handle_request(self, request):
        path = request['headers'].get(b':path', b'').decode('utf-8')
        method = request['headers'].get(b':method', b'').decode('utf-8')

        if path == '/nsmf-pdusession/v1/sm-contexts' and method == 'POST':
            # Xử lý Create Session Request
            data = json.loads(request['data'].decode('utf-8'))
            req = CreateSessionRequest(**data)

            # Gửi vào worker pool để xử lý bất đồng bộ
            await self.worker_pool.submit(self.process_create_session, req)

            return json.dumps({"status": "processing"}).encode('utf-8')

        return json.dumps({"error": "Not found"}).encode('utf-8')

    async def process_create_session(self, req: CreateSessionRequest):
        # Step 1: Xác thực IMSI với UDM
        if not await self.udm_client.verify_imsi(req.supi):
            print(f"IMSI verification failed for {req.supi}")
            return

        # Step 2: Thiết lập PFCP session với UPF
        pfcp_resp = await self.upf_client.establish_pfcp_session(req.dict())

        # Step 3: Lưu phiên trong database
        session = PDUSession(
            id=str(uuid.uuid4()),
            supi=req.supi,
            pduSessionId=req.pduSessionId,
            dnn=req.dnn,
            ipAddress=pfcp_resp["ipAddress"],
            status="ACTIVE"
        )

        await self.store_session(session)

        # Step 4: Gửi N1N2 Message Transfer tới AMF
        n1n2_msg = N1N2MessageTransfer(
            pduSessionId=req.pduSessionId,
            sNssai=req.sNssai,
            dnn=req.dnn
        )

        await self.amf_client.send_n1n2_message_transfer(req.supi, n1n2_msg)

    async def store_session(self, session: PDUSession):
        # Lưu phiên trong MongoDB
        self.db.pdu_sessions.insert_one(session.dict())
        print(f"Session stored in database: {session.dict()}")
