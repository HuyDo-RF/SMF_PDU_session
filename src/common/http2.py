import ssl
import asyncio
from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.events import (
    RequestReceived, DataReceived, StreamEnded
)


class HTTP2Server:
    def __init__(self, host, port, cert_file, key_file, request_handler):
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.request_handler = request_handler

    async def start(self):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(self.cert_file, self.key_file)
        ssl_context.set_alpn_protocols(['h2'])

        server = await asyncio.start_server(
            self.handle_client, self.host, self.port, ssl=ssl_context
        )

        print(f"HTTP/2 Server running on {self.host}:{self.port}")

        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        config = H2Configuration(client_side=False)
        conn = H2Connection(config=config)
        conn.initiate_connection()
        writer.write(conn.data_to_send())

        request_data = {}

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break

                events = conn.receive_data(data)

                for event in events:
                    if isinstance(event, RequestReceived):
                        request_data[event.stream_id] = {
                            'headers': dict(event.headers),
                            'data': bytearray(),
                            'stream_id': event.stream_id
                        }
                    elif isinstance(event, DataReceived):
                        if event.stream_id in request_data:
                            request_data[event.stream_id]['data'].extend(event.data)
                    elif isinstance(event, StreamEnded):
                        if event.stream_id in request_data:
                            req = request_data[event.stream_id]
                            response = await self.request_handler(req)

                            # Send response headers
                            conn.send_headers(
                                stream_id=event.stream_id,
                                headers=[
                                    (':status', '200'),
                                    ('content-type', 'application/json'),
                                ],
                            )

                            # Send response data
                            conn.send_data(
                                stream_id=event.stream_id,
                                data=response,
                                end_stream=True
                            )

                            writer.write(conn.data_to_send())

                writer.write(conn.data_to_send())
                await writer.drain()

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
