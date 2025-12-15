import httpx

timeout = httpx.Timeout(
        connect=5,
        read=10,
        write=10,
        pool=5,
    )
client = httpx.AsyncClient(
    timeout=httpx.Timeout(timeout=timeout)
)
