import aiohttp
import logging

import bs4
from . import event

logger = logging.getLogger(__name__)


class Client:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
        self.on_request = event.Event[str]()
        self.on_response = event.Event[aiohttp.ClientResponse]()
        self.title = ''
        self.status = ''
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        }

        event.register(event.OpenCommand, self.open_command_async)

    async def open_command_async(self, command: event.OpenCommand):
        self.on_request(command.url)
        async with self.session.get(command.url, headers=self.headers) as response:
            self.on_response(response)
            body = await response.text()

        soup = bs4.BeautifulSoup(body, 'html.parser')
        event.enqueue(event.UpdateSoup(command.url, soup))
