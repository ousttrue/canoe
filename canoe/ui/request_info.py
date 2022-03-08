import io
import prompt_toolkit.layout
import prompt_toolkit.buffer
import aiohttp


class RequestInfo:
    def __init__(self) -> None:
        self.text = ''
        self.control = prompt_toolkit.layout.controls.FormattedTextControl(
            lambda: self.text)
        self.container = prompt_toolkit.layout.containers.Window(self.control)

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def set_url(self, url: str):
        self.text = url


class ResponseInfo:
    def __init__(self) -> None:
        self.text = ''
        self.control = prompt_toolkit.layout.controls.FormattedTextControl(
            lambda: self.text)
        self.container = prompt_toolkit.layout.containers.Window(self.control)

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def set_response(self, response: aiohttp.ClientResponse):
        sio = io.StringIO()
        sio.write(f'{response.status}\n')
        for key in response.headers.keys():
            v = response.headers[key]
            sio.write(f'{key}: {v}\n')
        self.text = sio.getvalue()


class Logger:
    def __init__(self) -> None:
        self.text = ''
        self.control = prompt_toolkit.layout.controls.FormattedTextControl(
            lambda: self.text)
        self.container = prompt_toolkit.layout.containers.Window(self.control)

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container
