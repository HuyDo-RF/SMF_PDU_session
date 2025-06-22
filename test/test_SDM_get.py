import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(http2=True, verify=False) as client:
        resp = await client.get("https://localhost:8083/nudm-sdm/v2/imsi-452040000000001/sm-data")
        print(resp.status_code)
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(main())


