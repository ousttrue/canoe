from typing import Any, NamedTuple, Dict, TypeAlias, Callable, Type, Generic, List, TypeVar, Awaitable
import logging
import asyncio


logger = logging.getLogger(__name__)


T = TypeVar('T')


class Event(Generic[T]):
    def __init__(self) -> None:
        self.callbacks: List[Callable[[T], None]] = []

    def bind(self, callback: Callable[[T], None]):
        self.callbacks.append(callback)

    def __call__(self, value: T):
        for callback in self.callbacks:
            callback(value)


class OpenCommand(NamedTuple):
    method: str
    url: str


AwaitableEventHandler: TypeAlias = Callable[[Any], Awaitable]


class EventDispatcher:
    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        self._handlers: Dict[Type, AwaitableEventHandler] = {}

    def start(self, loop: asyncio.events.AbstractEventLoop):
        loop.create_task(self._worker())

    def register(self, event_type: Type, handler: AwaitableEventHandler):
        assert(event_type not in self._handlers)
        self._handlers[event_type] = handler

    async def _worker(self):
        logger.info('start worker')
        while True:
            payload = await self._queue.get()
            logger.debug(f'dequeue: {payload}')

            handler = self._handlers.get(type(payload))
            if not handler:
                logger.error(f'handler not found: {payload}')
                continue

            try:
                await handler(payload)
            except Exception as e:
                logger.exception(e)
                # raise

    def enqueue(self, payload):
        self._queue.put_nowait(payload)


DISPATCHER = EventDispatcher()


def enqueue(payload):
    DISPATCHER.enqueue(payload)


def register(event_type: Type, handler):
    DISPATCHER.register(event_type, handler)


def pre_run(loop: asyncio.events.AbstractEventLoop):
    DISPATCHER.start(loop)
