from typing import Callable
import aiohttp
from bs4 import BeautifulSoup


class Client:
    def __init__(self) -> None:
        self.title = ''
        self.address = ''
        self.set_content: Callable[[str], None] = lambda x: None
        self.status = ''

    def get_title(self):
        return self.title

    def get_address(self):
        return self.address

    def get_status(self):
        return self.status

    async def get_async(self, url: str):
        self.title = url
        self.address = url
        self.set_content(f'get {url} ...')
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.status = f"{response.status}: {response.headers['content-type']}"
                html = await response.text()

                if self.set_content:
                    soup = BeautifulSoup(html, 'html.parser')
                    if soup.title:
                        self.title = soup.title.get_text()
                    self.set_content(soup.get_text())
