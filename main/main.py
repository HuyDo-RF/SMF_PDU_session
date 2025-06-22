import asyncio
import argparse
import os
import ssl
from src.amf.server import AMFServer
from src.smf.server import SMFServer
from src.udm.server import UDMServer
from src.upf.server import UPFServer


async def main(args):
    # Tạo SSL certificate nếu chưa có
    if not os.path.exists(args.cert_file) or not os.path.exists(args.key_file):
        print("Generating SSL certificate...")
        os.system(
            f"openssl req -new -x509 -keyout {args.key_file} -out {args.cert_file} -days 365 -nodes -subj '/CN=localhost'")

    # Khởi động UPF server
    upf_server = UPFServer(args.upf_host, args.upf_port)
    upf_task = asyncio.create_task(upf_server.start())

    # Khởi động UDM server
    udm_server = UDMServer(
        args.udm_host, args.udm_port,
        args.cert_file, args.key_file,
        args.db_uri
    )
    udm_task = asyncio.create_task(udm_server.start())

    # Khởi động SMF server
    smf_server = SMFServer(
        args.smf_host, args.smf_port,
        args.cert_file, args.key_file,
        args.db_uri
    )
    smf_task = asyncio.create_task(smf_server.start())

    # Khởi động AMF server
    amf_server = AMFServer(
        args.amf_host, args.amf_port,
        args.cert_file, args.key_file
    )
    amf_task = asyncio.create_task(amf_server.start())

    await asyncio.gather(upf_task, udm_task, smf_task, amf_task)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="5G Core Network Functions")
    parser.add_argument("--amf-host", default="localhost", help="AMF host")
    parser.add_argument("--amf-port", type=int, default=8081, help="AMF port")
    parser.add_argument("--smf-host", default="localhost", help="SMF host")
    parser.add_argument("--smf-port", type=int, default=8082, help="SMF port")
    parser.add_argument("--udm-host", default="localhost", help="UDM host")
    parser.add_argument("--udm-port", type=int, default=8083, help="UDM port")
    parser.add_argument("--upf-host", default="localhost", help="UPF host")
    parser.add_argument("--upf-port", type=int, default=8084, help="UPF port")
    parser.add_argument("--cert-file", default="server.crt", help="SSL certificate file")
    parser.add_argument("--key-file", default="server.key", help="SSL key file")
    parser.add_argument("--db-uri", default="mongodb://localhost:27017/", help="MongoDB URI")

    args = parser.parse_args()
    args.cert_file = r"D:\5G VDT\5G_SMF\server.crt"
    args.key_file = r"D:\5G VDT\5G_SMF\server.key"

    asyncio.run(main(args))
