import aiohttp
import logging
from . import event

logger = logging.getLogger(__name__)


class Client:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
        self.on_request = event.Event[str]()
        self.on_response = event.Event[aiohttp.ClientResponse]()
        self.title = ''
        self.status = ''

        event.register(event.OpenCommand, self.open_command_async)

    async def open_command_async(self, command: event.OpenCommand):
        self.on_request(command.url)
        async with self.session.get(command.url) as response:
            self.on_response(response)
            body = await response.text()
            event.enqueue(event.UpdateHtml(body))
