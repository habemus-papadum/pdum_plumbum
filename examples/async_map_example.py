import asyncio

from pdum.plumbum import apb
from pdum.plumbum.aiterops import map as aiter_map


@apb
async def fetch(value: int) -> int:
    await asyncio.sleep(0.1)
    return value * 2


async def value_stream(values):
    for item in values:
        await asyncio.sleep(0)
        yield item


async def main() -> None:
    values = [1, 2, 3, 4]
    pipeline = aiter_map(fetch)

    iterator = await (value_stream(values) >> pipeline)
    results = [item async for item in iterator]
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
