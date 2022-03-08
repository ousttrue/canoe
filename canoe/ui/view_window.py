from typing import Optional
import prompt_toolkit.layout
import prompt_toolkit.buffer
import prompt_toolkit.filters
import prompt_toolkit.key_binding


class ViewWindow:
    def __init__(self) -> None:
        self.read_only = True
        self.buffer = prompt_toolkit.buffer.Buffer(
            read_only=prompt_toolkit.filters.Condition(lambda: self.read_only))
        self.has_focus = prompt_toolkit.filters.has_focus(self.buffer)

        from .hover_processor import HoverProcessor
        self.hover = HoverProcessor()
        input_processors = [
            self.hover,
        ]

        from .beautifulsoup_lexer import BeautifulSoupLexer
        self.lexer = BeautifulSoupLexer()

        self.control = prompt_toolkit.layout.controls.BufferControl(
            buffer=self.buffer,
            lexer=self.lexer,
            input_processors=input_processors,  # type: ignore
            include_default_input_processors=False,
            # preview_search=True,
            # search_buffer_control=search_buffer_control
        )

        self._wrap_lines = False

        @ prompt_toolkit.filters.Condition
        def wrap_lines() -> bool:
            return self._wrap_lines

        self.container = prompt_toolkit.layout.containers.Window(
            wrap_lines=wrap_lines,
            content=self.control,
        )

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def set_html_get_title(self, html: str) -> str:
        text, title = self.lexer.lex_html(html)
        self.read_only = False
        self.buffer.text = text
        self.read_only = True
        return title

    def get_url_under_cursor(self) -> Optional[str]:

        match self.hover.anchor_index:
            case int() as anchor_index:
                anchor = self.lexer.anchors[anchor_index]
                href = anchor['href']
                return href

    def focus(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        e.app.layout.focus(self.buffer)
