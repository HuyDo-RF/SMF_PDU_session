import asyncio
from src.common.pfcp import PFCPProtocol


class UPFServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.pfcp_protocol = PFCPProtocol()
        self.sessions = {}

    async def start(self):
        await self.pfcp_protocol.start_server(
            self.host, self.port, self.handle_pfcp_message
        )

    async def handle_pfcp_message(self, request, addr):
        print(f"Received PFCP message from {addr}: {request}")

        if request['message_type'] == PFCPProtocol.SESSION_ESTABLISHMENT_REQUEST:
            # Tạo phiên
            seid = request.get('seid', 0)
            if seid == 0:
                seid = int.from_bytes(asyncio.get_event_loop().time().to_bytes(8, 'big'), 'big')

            session = {
                'seid': seid,
                'ipAddress': '10.11.22.123',
                'status': 'ESTABLISHED'
            }

            self.sessions[seid] = session

            print(f"PFCP Session established with ID: {seid}")

            return session

        return None
