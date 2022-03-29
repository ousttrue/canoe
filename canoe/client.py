from typing import Generic, TypeVar, List, Callable
import aiohttp
import logging
from . import event

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


class Client:
    def __init__(self, queue) -> None:
        self.session = aiohttp.ClientSession()
        self.queue = queue
        self.on_request = Event[str]()
        self.on_response = Event[aiohttp.ClientResponse]()
        self.on_body = Event[str]()
        self.title = ''
        self.status = ''

        event.register(event.OpenCommand, self.open_command)

    def open_command(self, command: event.OpenCommand):
        async def _async():
            self.on_request(command.url)
            async with self.session.get(command.url) as response:
                self.on_response(response)
                body = await response.text()
                self.on_body(body)

        self.queue.put_nowait(_async)
