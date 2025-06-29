import asyncio
import httpx
import time
import random
import string

def create_dummy_request():
    return {
        "supi": f"imsi-45204{random.randint(100000000, 999999999)}",
        "gpsi": f"msisdn-849{random.randint(100000000, 999999999)}",
        "pduSessionId": random.randint(1, 255),
        "dnn": "v-internet",
        "sNssai": {"sst": 1, "sd": "000001"},
        "servingNfId": ''.join(random.choices(string.ascii_lowercase + string.digits, k=12)),
        "anType": "3GPP_ACCESS"
    }


async def stress_test_http2(n_requests: int, concurrency: int = 100):
    url = "https://localhost:8082/nsmf-pdusession/v1/sm-contexts"
    # Tạo HTTP/2 client, bỏ kiểm chứng SSL nếu cần
    async with httpx.AsyncClient(http2=True, verify=False) as client:
        start = time.perf_counter()
        sem = asyncio.Semaphore(concurrency)

        async def send(i):
            async with sem:
                payload = create_dummy_request()
                try:
                    resp = await client.post(url, json=payload, timeout=30.0)
                    return resp.status_code
                except Exception:
                    return 0

        tasks = [asyncio.create_task(send(i)) for i in range(n_requests)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

    success = sum(1 for code in results if code in (200, 201, 202))
    print(f"--- Kết quả HTTP/2 stress-test ---")
    print(f"Sent          : {n_requests:,} requests")
    print(f"Successful    : {success:,}")
    print(f"Failed/Timeout: {n_requests - success:,}")
    print(f"Duration      : {elapsed:.2f} seconds")
    print(f"Throughput    : {success / elapsed:.2f} TPS")


if __name__ == "__main__":
    asyncio.run(stress_test_http2(n_requests=2000, concurrency=200))










