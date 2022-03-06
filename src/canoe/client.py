from typing import Callable
import aiohttp
import bs4
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters
import prompt_toolkit.buffer
import prompt_toolkit.lexers
import prompt_toolkit.document
import prompt_toolkit.formatted_text
import prompt_toolkit.widgets


class Client:
    def __init__(self) -> None:
        self.title = ''
        self.address = ''
        self.status = ''
        self._wrap_lines = False
        self.text = ''

        self.buffer = prompt_toolkit.buffer.Buffer()

        self.control = prompt_toolkit.layout.controls.BufferControl(
            buffer=self.buffer,
            # lexer=BeautifulSoupLexer(),
            # input_processors=input_processors,
            include_default_input_processors=False,
            # preview_search=True,
            # search_buffer_control=search_buffer_control
        )

        @prompt_toolkit.filters.Condition
        def wrap_lines() -> bool:
            return self._wrap_lines

        self.container = prompt_toolkit.layout.containers.Window(
            wrap_lines=wrap_lines,
            content=self.control,
        )

    def get_title(self):
        return self.title

    def get_address(self):
        return self.address

    def get_status(self):
        return self.status

    async def get_async(self, url: str):
        self.title = url
        self.address = url
        self.text = f'get {url} ...'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.status = f"{response.status}: {response.headers['content-type']}"
                html = await response.text()
                self.on_get(html)

    def on_get(self, html: str):
        # text = []
        soup = bs4.BeautifulSoup(html, 'html.parser')
        for e in soup.descendants:
            match e:
                case bs4.Tag() as tag:
                    pass
                case bs4.element.Doctype():
                    pass
                case bs4.element.NavigableString():
                    # text.append(('', e.text))
                    pass
                case _:
                    t = type(e)
                    raise RuntimeError(f'unknwon: {t}')
            if soup.title:
                self.title = soup.title.get_text()
            self.buffer.text = soup.get_text()

        # self.text = text

    def get_text(self):
        return self.text
