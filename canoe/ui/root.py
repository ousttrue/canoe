from typing import Callable, Union, Coroutine, Any, Optional
import prompt_toolkit.application
import prompt_toolkit.styles
import prompt_toolkit.layout
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.buffer
import prompt_toolkit.widgets
import prompt_toolkit.enums
import prompt_toolkit.key_binding
import prompt_toolkit.filters
import prompt_toolkit.keys
from prompt_toolkit.layout.dimension import LayoutDimension as D


class Root:
    def __init__(self, queue) -> None:
        self.queue = queue

        from ..client import Client
        self.client = Client(queue)

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

        self.key_bindings = prompt_toolkit.key_binding.KeyBindings()

        from .style import CLIENT_STYLE
        self.application = prompt_toolkit.application.Application(
            layout=prompt_toolkit.layout.Layout(
                self.root, focused_element=self.view.container),
            full_screen=True,
            style=CLIENT_STYLE,
            key_bindings=self.key_bindings,
            # editing_mode=prompt_toolkit.enums.EditingMode.VI,
            enable_page_navigation_bindings=False,
        )

    def _browser_layout(self) -> prompt_toolkit.layout.containers.Container:
        '''
        [title]
        [address] # reverse
        [content]
        [status] # reverse
        [command]
        '''
        from .address_bar import AddressBar
        self.address_bar = AddressBar(
            self.client.push_url, style="class:status")
        self.client.on_request.bind(self.address_bar.set_text)

        from .view_window import ViewWindow
        self.view = ViewWindow()

        from .bar import Bar
        self.title_bar = Bar()

        def on_body(body: str):
            title = self.view.set_html_get_title(body)
            self.title_bar.text = title

        self.client.on_body.bind(on_body)

        from .status_bar import StatusBar

        self.status_bar = StatusBar()

        def on_buffer_changed(buffer: prompt_toolkit.buffer.Buffer):
            doc = buffer.document
            self.status_bar.row = doc.cursor_position_row + 1
            self.status_bar.col = doc.cursor_position_col + 1
            self.status_bar.lines = len(doc.lines)
        self.view.on_buffer_callbacks.append(on_buffer_changed)

        from .prompt import YesNoPrompt
        self._quit_prompt = YesNoPrompt()

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
            ]
        )

        return splitter

    def _keybind(self, func: Callable[[prompt_toolkit.key_binding.KeyPressEvent], None], *keys: Union[prompt_toolkit.keys.Keys, str],
                 filter: prompt_toolkit.filters.FilterOrBool = True,
                 eager: prompt_toolkit.filters.FilterOrBool = False,
                 is_global: prompt_toolkit.filters.FilterOrBool = False,
                 save_before: Callable[[prompt_toolkit.key_binding.KeyPressEvent], bool] = (
            lambda e: True),
            record_in_macro: prompt_toolkit.filters.FilterOrBool = True):
        keys = tuple(prompt_toolkit.key_binding.key_bindings._parse_key(k)
                     for k in keys)
        self.key_bindings.bindings.append(
            prompt_toolkit.key_binding.key_bindings.Binding(
                keys,
                func,
                filter=filter,
                eager=eager,
                is_global=is_global,
                save_before=save_before,
                record_in_macro=record_in_macro,
            )
        )
        self.key_bindings._clear_cache()

    def _keybind_async(self, func: Callable[[prompt_toolkit.key_binding.KeyPressEvent], Coroutine[Any, Any, None]], *keys: Union[prompt_toolkit.keys.Keys, str], **kw):
        assert keys

        def callback(e: prompt_toolkit.key_binding.KeyPressEvent):
            async def task():
                await func(e)
            self.queue.put_nowait(task)

        self._keybind(callback, *keys, **kw)

    def quit_prompt(self, event: prompt_toolkit.key_binding.KeyPressEvent):
        " Quit. "
        def on_accept(value: str):
            if value == 'y':
                event.app.exit()
            else:
                event.app.layout.focus(self.view.control)
        self._quit_prompt.focus(event, on_accept)

    def enter(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        url = self.view.get_url_under_cursor()
        if url:
            self.client.push_url(url)
