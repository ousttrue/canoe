import asyncio


async def main():
    from .app import App
    app = App()
    await app.application.run_async()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
