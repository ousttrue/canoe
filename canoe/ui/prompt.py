from typing import Callable
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.layout.processors
import prompt_toolkit.buffer
import prompt_toolkit.completion
import prompt_toolkit.lexers
import prompt_toolkit.filters
import prompt_toolkit.key_binding


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

        def dummy(text: str):
            pass
        self.on_accept = dummy

    def _accept(self, buffer: prompt_toolkit.buffer.Buffer) -> bool:
        assert(self.on_accept)
        self.on_accept(buffer.text)
        self.on_accept = None
        return False

    def focus(self, event: prompt_toolkit.key_binding.KeyPressEvent, callback: Callable[[str], None]):
        def on_accept(text: str):
            callback(text)
        self.on_accept = on_accept
        event.app.layout.focus(self.buffer)
