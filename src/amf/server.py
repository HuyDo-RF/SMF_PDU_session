import orjson as json
import asyncio
from src.common.http2 import HTTP2Server
from src.common.models import N1N2MessageTransfer, CreateSessionRequest


class AMFClient:
    def __init__(self, smf_host, smf_port):
        # Chỉ lưu cấu hình, chưa kết nối
        self.smf_host = smf_host
        self.smf_port = smf_port
        self._conn = None
        self._socket = None
    async def connect(self):
        import ssl, socket
        from h2.config import H2Configuration
        from h2.connection import H2Connection
      # Tạo SSLContext và bật ALPN 'h2'
        ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        ssl_ctx.check_hostname = False
        ssl_ctx.set_alpn_protocols(['h2'])
      # Kết nối TCP + TLS
        raw_sock = socket.create_connection((self.smf_host, self.smf_port))
        ssl_sock = ssl_ctx.wrap_socket(raw_sock, server_hostname=self.smf_host)

      # HTTP/2 handshake
        self._conn = H2Connection(config=H2Configuration(client_side=True))
        self._conn.initiate_connection()
        ssl_sock.send(self._conn.data_to_send())
        self._socket = ssl_sock


    async def create_session(self, request: CreateSessionRequest):
        # Client sử dụng giao thức HTTP/2 để gửi request đến SMF
        print(f"Sending Create Session Request to SMF: {request.dict()}")
        return True
        headers = [
            (':method', 'POST'),
            (':path', '/nsmf-pdusession/v1/sm-contexts'),
            ('content-type', 'application/json'),
        ]
        data = json.dumps(request.dict())
        self._conn.send_headers(stream_id=1, headers=headers)
        self._conn.send_data(stream_id=1, data=data, end_stream=True)
        self._socket.send(self._conn.data_to_send())
        # Đọc response nếu cần...
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

            return json.dumps({"status": "received"})

        return json.dumps({"error": "Not found"})

    async def send_create_session_request(self, request: CreateSessionRequest):
        return await self.smf_client.create_session(request)
