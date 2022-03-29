import asyncio
import argparse
import logging
logger = logging.getLogger(__name__)


async def main():
    #
    # command line
    #
    parser = argparse.ArgumentParser(description='canoe 🛶 text browser.')

    parser.add_argument('url', help='open url')
    args = parser.parse_args()

    #
    # worker
    #
    from .async_processor import AsyncProcessor
    processor = AsyncProcessor()

    #
    # UI
    #
    from .ui.root import Root
    root = Root(processor.queue)

    #
    # start up
    #
    from . import event
    event.enqueue(event.OpenCommand('GET', args.url))

    def pre_run():
        assert(root.application.loop)
        event.pre_run(root.application.loop)

    await root.application.run_async(pre_run=pre_run)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.debug('start')
    asyncio.run(main())
