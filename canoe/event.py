from typing import Any, NamedTuple, Dict, TypeAlias, Callable, Type
import logging
import asyncio


logger = logging.getLogger(__name__)


class OpenCommand(NamedTuple):
    method: str
    url: str


EventHandler: TypeAlias = Callable[[Any], None]


class EventDispatcher:
    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        self._handlers: Dict[Type, EventHandler] = {}

    def start(self, loop: asyncio.events.AbstractEventLoop):
        loop.create_task(self._worker())

    def register(self, event_type: Type, handler: EventHandler):
        assert(event_type not in self._handlers)
        self._handlers[event_type] = handler

    def _handle(self, palyload: Any) -> bool:
        handler = self._handlers.get(type(palyload))
        if not handler:
            logger.error(f'handler not found: {palyload}')
            return False

        try:
            handler(palyload)
            return True
        except Exception as e:
            logger.exception(e)
            # raise
            return False

    async def _worker(self):
        logger.info('start worker')
        while True:
            event = await self._queue.get()
            logger.debug(f'dequeue: {event}')

            try:
                if not self._handle(event):
                    logger.error('unhandled event: %s', event)
            except Exception as e:
                logger.exception(e)

    def enqueue(self, payload):
        self._queue.put_nowait(payload)


DISPATCHER = EventDispatcher()


def enqueue(payload):
    DISPATCHER.enqueue(payload)


def register(event_type: Type, handler):
    DISPATCHER.register(event_type, handler)


def pre_run(loop: asyncio.events.AbstractEventLoop):
    DISPATCHER.start(loop)
