import prompt_toolkit.buffer
import prompt_toolkit.layout
import prompt_toolkit.filters
import prompt_toolkit.key_binding
D = prompt_toolkit.layout.Dimension


class AddressBar:
    def __init__(self, kb: prompt_toolkit.key_binding.KeyBindings, style="") -> None:
        self.kb = kb
        self.buffer = prompt_toolkit.buffer.Buffer(multiline=False)
        self.has_focus = prompt_toolkit.filters.has_focus(self.buffer)
        self.control = prompt_toolkit.layout.controls.BufferControl(
            self.buffer)
        self.container = prompt_toolkit.layout.containers.Window(
            content=self.control,
            height=D.exact(1),
            style=style,
        )

        self._keybind(self.unfocus, 'escape')
        self._keybind(self.enter, 'enter')

    def set_text(self, text: str):
        self.buffer.text = text

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def _keybind(self, callback, *args):
        self.kb.add(*args, filter=self.has_focus)(callback)

    def focus(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        e.app.layout.focus(self.buffer)

    def unfocus(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        e.app.layout.focus_last()

    def enter(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        from .. import event
        event.enqueue(event.OpenCommand('GET', self.buffer.text))
        e.app.layout.focus_previous()
