import asyncio
import json
import ssl
import h2.connection
import h2.config
from h2.events import (
    ResponseReceived, DataReceived, StreamEnded, StreamReset, ConnectionTerminated
)


async def send_create_session_request():
    # Tạo SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    ssl_context.set_alpn_protocols(['h2'])

    # Kết nối đến SMF
    reader, writer = await asyncio.open_connection(
        'localhost', 8082, ssl=ssl_context
    )

    # Thiết lập H2 connection
    config = h2.config.H2Configuration(client_side=True)
    conn = h2.connection.H2Connection(config=config)
    conn.initiate_connection()
    writer.write(conn.data_to_send())

    # Tạo request
    request_data = {
        "supi": "imsi-452040000000001",
        "gpsi": "msisdn-84900000001",
        "pduSessionId": 1,
        "dnn": "v-internet",
        "sNssai": {
            "sst": 1,
            "sd": "000001"
        },
        "servingNfId": "2ab2b5a9-68e8-4ee6-b939-024c109b520c",
        "anType": "3GPP_ACCESS"
    }

    # Chuyển đổi thành JSON
    json_data = json.dumps(request_data).encode('utf-8')

    # Gửi request
    stream_id = conn.get_next_available_stream_id()
    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (':method', 'POST'),
            (':path', '/nsmf-pdusession/v1/sm-contexts'),
            (':scheme', 'https'),
            (':authority', 'localhost:8082'),
            ('content-type', 'application/json'),
            ('content-length', str(len(json_data))),
        ],
    )
    conn.send_data(
        stream_id=stream_id,
        data=json_data,
        end_stream=True
    )
    writer.write(conn.data_to_send())

    # Xử lý response
    response_data = b''
    response_received = False

    while not response_received:
        data = await reader.read(1024)
        if not data:
            break

        events = conn.receive_data(data)

        for event in events:
            if isinstance(event, ResponseReceived):
                print(f"Response headers: {event.headers}")
            elif isinstance(event, DataReceived):
                response_data += event.data
            elif isinstance(event, StreamEnded):
                response_received = True
                print(f"Response data: {response_data.decode('utf-8')}")
            elif isinstance(event, ConnectionTerminated):
                print(f"Connection terminated: {event.error_code}")
                return

        writer.write(conn.data_to_send())

    # Đóng kết nối
    conn.close_connection()
    writer.write(conn.data_to_send())
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(send_create_session_request())
