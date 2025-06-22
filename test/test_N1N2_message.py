import asyncio
import ssl
import h2.connection
import h2.config
from h2.events import ResponseReceived, DataReceived, StreamEnded, ConnectionTerminated
import json

async def send_n1n2_message_transfer():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    ssl_context.set_alpn_protocols(['h2'])

    reader, writer = await asyncio.open_connection('localhost', 8081, ssl=ssl_context)
    config = h2.config.H2Configuration(client_side=True)
    conn = h2.connection.H2Connection(config=config)
    conn.initiate_connection()
    writer.write(conn.data_to_send())

    msg_data = {
        "pduSessionId": 5,
        "sNssai": {"sst": 1, "sd": "000001"},
        "dnn": "v-internet"
    }
    json_data = json.dumps(msg_data).encode('utf-8')
    stream_id = conn.get_next_available_stream_id()
    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (':method', 'POST'),
            (':path', '/namf-comm/v1/ue-context/imsi-452040000000001/n1-n2-messages'),
            (':scheme', 'https'),
            (':authority', 'localhost:8081'),
            ('content-type', 'application/json'),
            ('content-length', str(len(json_data))),
        ],
    )
    conn.send_data(stream_id=stream_id, data=json_data, end_stream=True)
    writer.write(conn.data_to_send())

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
    conn.close_connection()
    writer.write(conn.data_to_send())
    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(send_n1n2_message_transfer())
