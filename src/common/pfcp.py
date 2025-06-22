import socket
import struct
import asyncio
from typing import Dict, Any, Tuple


class PFCPProtocol:
    # PFCP Message Types
    SESSION_ESTABLISHMENT_REQUEST = 50
    SESSION_ESTABLISHMENT_RESPONSE = 51

    def __init__(self):
        self.socket = None

    async def start_server(self, host: str, port: int, handler):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, port))
        self.socket.setblocking(False)

        print(f"PFCP Server running on {host}:{port}")

        loop = asyncio.get_event_loop()

        while True:
            data, addr = await loop.sock_recvfrom(self.socket, 1024)
            asyncio.create_task(self._handle_message(data, addr, handler))

    async def _handle_message(self, data: bytes, addr: Tuple[str, int], handler):
        if len(data) < 8:
            print("Invalid PFCP message length")
            return

        # Parse PFCP header
        version = (data[0] >> 5) & 0x7
        message_type = data[1]
        message_length = struct.unpack("!H", data[2:4])[0]

        if message_type == self.SESSION_ESTABLISHMENT_REQUEST:
            # Extract SEID (if present)
            s_flag = (data[0] >> 3) & 0x1
            seid = None
            if s_flag:
                seid = struct.unpack("!Q", data[4:12])[0]
                ie_offset = 12
            else:
                ie_offset = 4

            # Process IEs (simplified)
            request_data = {
                'message_type': message_type,
                'seid': seid
            }

            # Call handler
            response_data = await handler(request_data, addr)

            # Send response
            await self.send_response(addr, response_data)

    async def send_response(self, addr: Tuple[str, int], response_data: Dict[str, Any]):
        # Create PFCP Session Establishment Response
        seid = response_data.get('seid', 0)
        ip_address = response_data.get('ipAddress', '0.0.0.0')

        # Build response packet (simplified)
        response = bytearray()

        # Version (3 bits) | S flag (1 bit) | Others (4 bits)
        response.append(0x20 | 0x08)  # Version 1, S flag set

        # Message type
        response.append(self.SESSION_ESTABLISHMENT_RESPONSE)

        # Message length placeholder (will be filled later)
        response.extend(b'\x00\x00')

        # SEID
        response.extend(struct.pack("!Q", seid))

        # Sequence number, spare
        response.extend(b'\x00\x00\x00')

        # Add IP address IE (simplified)
        ip_bytes = socket.inet_aton(ip_address)
        response.extend(ip_bytes)

        # Update message length
        struct.pack_into("!H", response, 2, len(response) - 4)

        # Send response
        loop = asyncio.get_event_loop()
        await loop.sock_sendto(self.socket, response, addr)
