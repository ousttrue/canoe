from typing import Any, NamedTuple, Dict, TypeAlias, Callable, Type, Generic, List, TypeVar, Awaitable
import logging
import asyncio
import inspect
import bs4


logger = logging.getLogger(__name__)


T = TypeVar('T')


class Event(Generic[T]):
    def __init__(self) -> None:
        self.callbacks: Dict[Callable[[T], None], bool] = {}

    def bind(self, callback: Callable[[T], None], once=False):
        self.callbacks[callback] = once

    def once(self, callback: Callable[[T], None]):
        self.bind(callback, True)

    def __iadd__(self, callback):
        self.bind(callback, False)

    def __call__(self, value: T):
        once_list = []
        for callback, once in self.callbacks.items():
            callback(value)
            if once:
                once_list.append(callback)
        for callback in once_list:
            del self.callbacks[callback]

    async def wait_async(self):
        future = asyncio.Future()

        def callback(value):
            future.set_result(value)
        self.once(callback)
        return await future


class OpenCommand(NamedTuple):
    method: str
    url: str


class FocusInputCommand(NamedTuple):
    url: str
    tag: bs4.Tag


# class UpdateHtml(NamedTuple):
#     html: str


class UpdateSoup(NamedTuple):
    url: str
    soup: bs4.BeautifulSoup


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

            result = handler(payload)
            if inspect.isawaitable(result):
                await result

    def enqueue(self, payload):
        self._queue.put_nowait(payload)


DISPATCHER = EventDispatcher()


def enqueue(payload):
    DISPATCHER.enqueue(payload)


def register(event_type: Type, handler):
    DISPATCHER.register(event_type, handler)


def pre_run(loop: asyncio.events.AbstractEventLoop):
    DISPATCHER.start(loop)
