import io
import prompt_toolkit.layout
import prompt_toolkit.buffer
import aiohttp
import logging


class RequestInfo:
    def __init__(self) -> None:
        self.text = ''
        self.control = prompt_toolkit.layout.controls.FormattedTextControl(
            lambda: self.text)
        self.container = prompt_toolkit.layout.containers.Window(
            self.control, height=1)

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def set_url(self, url: str):
        text = []
        text.append(('reverse', 'GET'))
        # text.append(('', url))
        self.text = text


class ResponseInfo:
    def __init__(self) -> None:
        self.text = ''
        self.control = prompt_toolkit.layout.controls.FormattedTextControl(
            lambda: self.text)
        self.container = prompt_toolkit.layout.containers.Window(self.control)

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def set_response(self, response: aiohttp.ClientResponse):
        text = []
        height = 1
        text.append(('reverse', f'{response.status}\n'))
        # for key in response.headers.keys():
        #     v = response.headers[key]
        #     text.append(('', f'{key}: {v}\n'))
        #     height += 1
        self.container.height = height
        self.text = text


class Logger(logging.Handler):
    def __init__(self, height=6) -> None:
        super().__init__()
        self.text = []
        self.control = prompt_toolkit.layout.controls.FormattedTextControl(
            lambda: self.text)
        self.container = prompt_toolkit.layout.containers.Window(
            self.control, height=height)
        self.register_root()

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        match record.levelno:
            case 0:
                style = '#888888'
            case _:
                style = ''
        self.text.append((style, msg+'\n'))

    def write(self, m):
        pass

    def register_root(self):
        logging.getLogger().handlers = [self]
