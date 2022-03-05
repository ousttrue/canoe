import asyncio
import argparse


async def main():
    # command line
    parser = argparse.ArgumentParser(description='canoe 🛶 text browser.')

    parser.add_argument('url', help='open url')
    args = parser.parse_args()

    from .app import App
    app = App()

    app.push_url(args.url)

    await app.application.run_async()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
