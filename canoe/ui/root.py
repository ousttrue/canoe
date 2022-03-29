from typing import Callable, Union, Coroutine, Any, Optional
import bs4
import prompt_toolkit.application
import prompt_toolkit.styles
import prompt_toolkit.layout
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.buffer
import prompt_toolkit.widgets
import prompt_toolkit.enums
import prompt_toolkit.key_binding
import prompt_toolkit.key_binding.bindings.named_commands
import prompt_toolkit.filters
import prompt_toolkit.keys
import prompt_toolkit.cursor_shapes
from prompt_toolkit.layout.dimension import LayoutDimension as D
from .. import event


class Root:
    def __init__(self) -> None:

        from ..client import Client
        self.client = Client()

        self.key_bindings = prompt_toolkit.key_binding.KeyBindings()
        browser_layout = self._browser_layout()

        self.root = prompt_toolkit.layout.containers.FloatContainer(
            # background
            content=prompt_toolkit.layout.containers.Window(
                char=' ',
                ignore_content_width=True,
                ignore_content_height=True,
            ),
            floats=[
                prompt_toolkit.layout.containers.Float(
                    browser_layout,
                    transparent=True,
                    left=0,
                    right=0,
                    top=0,
                    bottom=0
                ),
            ],
        )

        from .style import CLIENT_STYLE
        self.application = prompt_toolkit.application.Application(
            layout=prompt_toolkit.layout.Layout(
                self.root, focused_element=self.view.container),
            full_screen=True,
            style=CLIENT_STYLE,
            key_bindings=self.key_bindings,
            # editing_mode=prompt_toolkit.enums.EditingMode.VI,
            enable_page_navigation_bindings=False,
            cursor=prompt_toolkit.cursor_shapes.CursorShape.BLOCK,
        )

        self.view._keybind(self.quit_prompt, 'q')
        # shift-tab
        self.view._keybind(self.address_bar.focus, 'U')

    def quit_prompt(self, event: prompt_toolkit.key_binding.KeyPressEvent):
        " Quit. "
        def on_accept(value: str):
            if value == 'y':
                event.app.exit()
            else:
                event.app.layout.focus(self.view.control)
        self._quit_prompt.focus(event, on_accept)

    def _browser_layout(self) -> prompt_toolkit.layout.containers.Container:
        '''
        [title]
        [address] # reverse
        [content]
        [status] # reverse
        [command]
        '''
        from .address_bar import AddressBar
        self.address_bar = AddressBar(self.key_bindings, style="class:status")
        self.client.on_request.bind(self.address_bar.set_text)

        from .view_window import ViewWindow
        self.view = ViewWindow(self.key_bindings)

        from .bar import Bar
        self.title_bar = Bar()

        def on_soup(payload: event.UpdateSoup):
            title = self.view.set_html_soup(payload.url, payload.soup)
            self.title_bar.text = title
        event.register(event.UpdateSoup, on_soup)

        from .status_bar import StatusBar

        self.status_bar = StatusBar()

        def on_buffer_changed(buffer: prompt_toolkit.buffer.Buffer):
            doc = buffer.document
            self.status_bar.row = doc.cursor_position_row + 1
            self.status_bar.col = doc.cursor_position_col + 1
            self.status_bar.lines = len(doc.lines)
        self.view.on_buffer_callbacks.append(on_buffer_changed)

        from .prompt import YesNoPrompt, InputPrompt
        self._quit_prompt = YesNoPrompt()
        self._input_prompt = InputPrompt()

        from .request_info import RequestInfo, ResponseInfo, Logger

        self.request = RequestInfo()
        self.client.on_request.bind(self.request.set_url)

        self.response = ResponseInfo()
        self.client.on_response.bind(self.response.set_response)

        self.logger = Logger()

        splitter = prompt_toolkit.layout.containers.HSplit(
            [
                self.title_bar,
                self.address_bar,
                self.request,
                self.response,
                self.view,
                self.status_bar,
                self.logger,
                self._quit_prompt,
                self._input_prompt,
            ]
        )

        return splitter
