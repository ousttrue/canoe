import asyncio


class AsyncProcessor:
    def __init__(self) -> None:
        self.queue = asyncio.Queue()
        asyncio.create_task(self._worker())

    async def _worker(self):
        while True:

            command = await self.queue.get()
            await command()
