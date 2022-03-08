from typing import Callable, Union, Coroutine, Any
import prompt_toolkit.application
import prompt_toolkit.styles
import prompt_toolkit.layout
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.widgets
import prompt_toolkit.enums
import prompt_toolkit.key_binding
import prompt_toolkit.filters
import prompt_toolkit.keys
from prompt_toolkit.layout.dimension import LayoutDimension as D


def quit(event: prompt_toolkit.key_binding.KeyPressEvent):
    event.app.exit()


def up(event: prompt_toolkit.key_binding.KeyPressEvent) -> None:
    event.current_buffer.auto_up(count=event.arg)


def down(event: prompt_toolkit.key_binding.KeyPressEvent) -> None:
    event.current_buffer.auto_down(count=event.arg)


class Bar:
    def __init__(self, get_text, style="") -> None:
        self.container = prompt_toolkit.layout.containers.Window(
            content=prompt_toolkit.layout.controls.FormattedTextControl(
                get_text),
            height=D.exact(1),
            style=style,
        )

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container


class Browser:
    def __init__(self) -> None:
        from .client import Client, CLIENT_STYLE
        self.client = Client()
        container = self._layout()

        self.key_bindings = prompt_toolkit.key_binding.KeyBindings()

        self.application = prompt_toolkit.application.Application(
            layout=prompt_toolkit.layout.Layout(
                container, focused_element=self.client.container),
            full_screen=True,
            style=CLIENT_STYLE,
            key_bindings=self.key_bindings,
            # editing_mode=prompt_toolkit.enums.EditingMode.VI,
            enable_page_navigation_bindings=False,
        )

        from .commands import AsyncProcessor
        self.processor = AsyncProcessor()

    def _layout(self) -> prompt_toolkit.layout.containers.Container:
        '''
        [title]
        [address] # reverse
        [content]
        [status] # reverse
        [command]
        '''

        self.title_bar = Bar(self.client.get_title)
        self.address_bar = Bar(self.client.get_address, style="class:status")

        self.status_bar = Bar(self.client.get_status, style="class:status")
        from .prompt import YesNoPrompt
        self._quit_prompt = YesNoPrompt()

        splitter = prompt_toolkit.layout.containers.HSplit(
            [
                self.title_bar,
                self.address_bar,
                self.client.container,
                self.status_bar,
                self._quit_prompt,
            ]
        )
        self.root = prompt_toolkit.layout.containers.FloatContainer(
            # background
            content=prompt_toolkit.layout.containers.Window(
                char=' ',
                ignore_content_width=True,
                ignore_content_height=True,
            ),
            floats=[
                prompt_toolkit.layout.containers.Float(
                    splitter,
                    transparent=True,
                    left=0,
                    right=0,
                    top=0,
                    bottom=0
                ),
            ],
        )
        return self.root

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
            self.processor.queue.put_nowait(task)

        self._keybind(callback, *keys, **kw)

    def quit_prompt(self, event: prompt_toolkit.key_binding.KeyPressEvent):
        " Quit. "
        def on_accept(value: str):
            if value == 'y':
                event.app.exit()
            else:
                event.app.layout.focus(self.client.control)
        self._quit_prompt.focus(event, on_accept)

    def push_url(self, url: str):
        async def _async():
            await self.client.get_async(url)
        self.processor.queue.put_nowait(_async)

    def enter(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        url = self.client.get_url_under_cursor()
        if url:
            self.push_url(url)
