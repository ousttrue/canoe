from typing import Optional, Callable, List, Tuple
import bs4
import prompt_toolkit.layout
import prompt_toolkit.buffer
import prompt_toolkit.filters
import prompt_toolkit.key_binding
import prompt_toolkit.key_binding.bindings.named_commands
import urllib.parse
from .. import event


def create_form_url(form: bs4.Tag, base_url) -> Tuple[str, str]:
    method = form.get('method', 'GET')
    assert(isinstance(method, str))
    action = form.get('action', '')
    assert(isinstance(action, str))
    if action.startswith('http:') or action.startswith('https:'):
        pass
    else:
        action = urllib.parse.urljoin(base_url, action)

    # query
    inputs = form.find_all('input')
    values = {}
    for input in inputs:
        name = input.get('name')
        if name in ['iflsig', 'btnG', 'btnI']:
            continue
        value = input.get('value')
        if name:
            if value:
                values[name] = value
            else:
                values[name] = ''
    query = '&'.join(f'{k}={v}' if v else k for k, v in values.items())

    return (method, action + '?' + query)


class ViewWindow:
    def __init__(self, kb: prompt_toolkit.key_binding.KeyBindings) -> None:
        self.kb = kb
        self.url = None
        self.soup = bs4.BeautifulSoup
        self.read_only = True
        self.on_buffer_callbacks: List[Callable[[
            prompt_toolkit.buffer.Buffer], None]] = []

        def on_buffer_changed(buffer: prompt_toolkit.buffer.Buffer):
            for callback in self.on_buffer_callbacks:
                callback(buffer)

        self.buffer = prompt_toolkit.buffer.Buffer(
            read_only=prompt_toolkit.filters.Condition(lambda: self.read_only),
            on_cursor_position_changed=on_buffer_changed)
        self.has_focus = prompt_toolkit.filters.has_focus(self.buffer)

        from .hover_processor import AnchorProcessor, HoverProcessor
        self.anchor = AnchorProcessor()
        self.hover = HoverProcessor()
        input_processors = [
            self.anchor,
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

        #
        # key bindings
        #
        self._keybind(self.quit, 'Q')
        self._keybind(self.down, 'j')
        self._keybind(self.up, 'k')
        self.kb.add('h', filter=self.has_focus)(
            prompt_toolkit.key_binding.bindings.named_commands.get_by_name("backward-char"))
        self.kb.add('l', filter=self.has_focus)(
            prompt_toolkit.key_binding.bindings.named_commands.get_by_name("forward-char"))
        # 0
        # $
        # space
        # b
        self._keybind(self.enter, 'enter')
        self._keybind(self.focus_next, 'tab')
        self._keybind(self.focus_prev, 's-tab')

    @property
    def base_urL(self) -> str:
        assert(self.url)
        u = urllib.parse.urlsplit(self.url)
        path = u.path
        return urllib.parse.urlunsplit(u._replace(path=path.rsplit('/', 1)[0], query=''))

    def _keybind(self, callback, *args):
        self.kb.add(*args, filter=self.has_focus, eager=True)(callback)

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container

    def set_html_soup(self, url: str, soup: bs4.BeautifulSoup) -> str:
        self.url = url
        self.soup = soup
        text, title = self.lexer.lex_html(soup)
        self.read_only = False
        self.buffer.text = text
        self.read_only = True
        return title

    def get_url_under_cursor(self) -> Optional[Tuple[str, str]]:
        assert(self.url)
        from .beautifulsoup_lexer import Anchor, Input
        match self.hover.anchor_index:
            case int() as anchor_index:
                match self.lexer.focus[anchor_index]:
                    case Anchor(tag):
                        href = tag['href']
                        return ('GET', href)  # type: ignore

                    case Input(tag, form):
                        if form:
                            match tag.get('type', 'text'):
                                case 'submit':
                                    return create_form_url(form, self.base_urL)
                                case 'text':
                                    event.enqueue(
                                        event.FocusInputCommand(self.url, tag))

            case _:
                return None

    def focus(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        e.app.layout.focus(self.buffer)

    def focus_next(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        focus = self.anchor.get_focus_next(self.buffer.document)
        if focus:
            self.buffer.cursor_position = self.buffer.document.translate_row_col_to_index(
                focus.row, focus.col_start)

    def focus_prev(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        focus = self.anchor.get_focus_prev(self.buffer.document)
        if focus:
            self.buffer.cursor_position = self.buffer.document.translate_row_col_to_index(
                focus.row, focus.col_start)

    def up(self, event: prompt_toolkit.key_binding.KeyPressEvent) -> None:
        event.current_buffer.auto_up(count=event.arg)

    def down(self, event: prompt_toolkit.key_binding.KeyPressEvent) -> None:
        event.current_buffer.auto_down(count=event.arg)

    def quit(self, event: prompt_toolkit.key_binding.KeyPressEvent):
        event.app.exit()

    def enter(self, e: prompt_toolkit.key_binding.KeyPressEvent):
        match self.get_url_under_cursor():
            case method, url:
                from .. import event
                event.enqueue(event.OpenCommand(method, url))
