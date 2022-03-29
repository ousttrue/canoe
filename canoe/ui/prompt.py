import asyncio
from typing import Callable
from prompt_toolkit.application.current import get_app
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.layout.processors
import prompt_toolkit.buffer
import prompt_toolkit.completion
import prompt_toolkit.lexers
import prompt_toolkit.filters
import prompt_toolkit.key_binding
from .. import event


class YesNoPrompt(prompt_toolkit.layout.containers.ConditionalContainer):
    def __init__(self) -> None:
        # Buffer for the 'Examine:' input.

        self.buffer = prompt_toolkit.buffer.Buffer(name="YesNo",
                                                   accept_handler=self._accept,
                                                   multiline=False,
                                                   )

        self.control = prompt_toolkit.layout.controls.BufferControl(
            buffer=self.buffer,
            lexer=prompt_toolkit.lexers.SimpleLexer(
                style="class:system-toolbar.text"),
            input_processors=[
                prompt_toolkit.layout.processors.BeforeInput(
                    lambda: "(y/n)? ", style="class:system-toolbar")
            ],
        )

        super().__init__(
            content=prompt_toolkit.layout.containers.Window(
                self.control, height=1,
            ),
            filter=prompt_toolkit.filters.has_focus(self.buffer),
        )

        from ..event import Event
        self.on_accept = Event[str]()

    def _accept(self, buffer: prompt_toolkit.buffer.Buffer) -> bool:
        assert(self.on_accept)
        self.on_accept(buffer.text)
        return False

    def focus(self, event: prompt_toolkit.key_binding.KeyPressEvent, callback: Callable[[str], None]):
        self.on_accept.once(callback)
        event.app.layout.focus(self.buffer)


class InputPrompt(prompt_toolkit.layout.containers.ConditionalContainer):
    def __init__(self) -> None:
        # Buffer for the 'Examine:' input.
        self.name = ''

        self.buffer = prompt_toolkit.buffer.Buffer(name="Input",
                                                   accept_handler=self._accept,
                                                   multiline=False,
                                                   )

        self.control = prompt_toolkit.layout.controls.BufferControl(
            buffer=self.buffer,
            lexer=prompt_toolkit.lexers.SimpleLexer(
                style="class:system-toolbar.text"),
            input_processors=[
                prompt_toolkit.layout.processors.BeforeInput(
                    lambda: f"{self.name}=>", style="class:system-toolbar")
            ],
        )

        super().__init__(
            content=prompt_toolkit.layout.containers.Window(
                self.control, height=1,
            ),
            filter=prompt_toolkit.filters.has_focus(self.buffer),
        )

        self.on_accept = event.Event[str]()
        event.register(event.FocusInputCommand, self.input_async)

    def _accept(self, buffer: prompt_toolkit.buffer.Buffer) -> bool:
        assert(self.on_accept)
        self.on_accept(buffer.text)
        return False

    async def input_async(self, command: event.FocusInputCommand):
        self.name = command.tag.get('name', '')
        self.buffer.text = command.tag.get('value', '')  # type: ignore
        self.buffer.cursor_position = len(self.buffer.text)  # type: ignore

        get_app().layout.focus(self.buffer)
        text = await self.on_accept.wait_async()
        assert(isinstance(text, str))
        command.tag['value'] = text
        get_app().layout.focus_last()

        parents = [p for p in command.tag.parents]
        event.enqueue(event.UpdateSoup(parents[-1]))  # type: ignore
