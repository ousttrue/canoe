from typing import Callable, List, Tuple, Optional
import aiohttp
import re
import bs4
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.layout.processors
import prompt_toolkit.filters
import prompt_toolkit.buffer
import prompt_toolkit.lexers
import prompt_toolkit.document
import prompt_toolkit.formatted_text
import prompt_toolkit.widgets
import prompt_toolkit.layout.utils
import prompt_toolkit.styles

CLIENT_STYLE = prompt_toolkit.styles.Style.from_dict({
    "status": "reverse",
    "status.position": "#aaaa00",
    "status.key": "#ffaa00",
    "not-searching": "#888888",
    #
    'anchor': '#0044ff underline',
    'form': '#44ff00 underline',
    'input': '#44ff00 underline',
})

ANCHORE_PATTERN = re.compile(r'\bclass:anchor class:_\d+\b')


class BeautifulSoupLexer(prompt_toolkit.lexers.Lexer):

    def __init__(self) -> None:
        super().__init__()
        self.lines: List[prompt_toolkit.formatted_text.StyleAndTextTuples] = [
            [('', '')]]
        self.title = ''
        self.anchors = []

    def lex_document(self, document: prompt_toolkit.document.Document) -> Callable[[int], prompt_toolkit.formatted_text.StyleAndTextTuples]:
        return self.get_line

    def get_line(self, index: int) -> prompt_toolkit.formatted_text.StyleAndTextTuples:
        return self.lines[index]

    def push(self, text: str, style: str):
        self.lines[-1].append((style, text))

    def new_line(self):
        self.lines.append([])

    def push_anchor(self, tag: bs4.element.Tag) -> str:
        n = len(self.anchors)
        self.anchors.append(tag)
        return f'class:anchor class:_{n}'

    def traverse(self, e: bs4.PageElement, style: str):
        match e:
            case bs4.Tag() as tag:
                match tag.name:
                    case 'title':
                        self.title = tag.text
                    case 'a':
                        style = self.push_anchor(tag)
                    case 'form':
                        self.push('form', 'class:form')
                    case 'input':
                        self.push('input', '#44ff00 underline')
                    case 'p' | 'div':
                        self.new_line()
                for child in tag.children:
                    self.traverse(child, style)
            case bs4.element.NavigableString():
                self.push(e.text, style)
            case bs4.element.Doctype():
                pass
            case _:
                t = type(e)
                raise RuntimeError(f'unknwon: {t}')

    def tex_html(self, html: str) -> Tuple[str, str]:
        soup = bs4.BeautifulSoup(html, 'html.parser')
        self.lines = [[]]
        self.title = ''
        for e in soup.children:
            self.traverse(e, '')

        def merge_line(line):
            return ''.join(text for style, text in line)
        lines = [merge_line(line) for line in self.lines]
        return ('\n'.join(lines), self.title)


class HoverProcessor(prompt_toolkit.layout.processors.Processor):
    def apply_transformation(
        self, transformation_input: prompt_toolkit.layout.processors.TransformationInput
    ) -> prompt_toolkit.layout.processors.Transformation:
        (
            buffer_control,
            document,
            lineno,
            source_to_display,
            fragments,
            _,
            _,
        ) = transformation_input.unpack()

        # In case of selection, highlight all matches.
        # Get cursor column.
        cursor_column: Optional[int]
        if document.cursor_position_row == lineno:
            cursor_column = source_to_display(document.cursor_position_col)
        else:
            cursor_column = None

        fragments = prompt_toolkit.layout.utils.explode_text_fragments(
            fragments)
        if isinstance(cursor_column, int) and cursor_column < len(fragments):
            style, text = fragments[cursor_column]  # type: ignore

            m = ANCHORE_PATTERN.search(style)
            if m:
                for i, fragment in enumerate(fragments):
                    style, text, *_ = fragment
                    matched = m.group(0)
                    if matched in style:
                        fragments[i] = (style + ' reverse ', text)

        return prompt_toolkit.layout.processors.Transformation(fragments)


class Client:
    def __init__(self) -> None:
        self.lexer = BeautifulSoupLexer()
        self.title = ''
        self.address = ''
        self.status = ''
        self._wrap_lines = False

        self.read_only = True
        self.buffer = prompt_toolkit.buffer.Buffer(
            read_only=prompt_toolkit.filters.Condition(lambda: self.read_only))
        self.has_focus = prompt_toolkit.filters.has_focus(self.buffer)

        input_processors = [
            HoverProcessor(),
        ]

        self.control = prompt_toolkit.layout.controls.BufferControl(
            buffer=self.buffer,
            lexer=self.lexer,
            input_processors=input_processors,  # type: ignore
            include_default_input_processors=False,
            # preview_search=True,
            # search_buffer_control=search_buffer_control
        )

        @ prompt_toolkit.filters.Condition
        def wrap_lines() -> bool:
            return self._wrap_lines

        self.container = prompt_toolkit.layout.containers.Window(
            wrap_lines=wrap_lines,
            content=self.control,
        )

    def get_title(self):
        return self.title

    def get_address(self):
        return self.address

    def get_status(self):
        return self.status

    async def get_async(self, url: str):
        self.title = url
        self.address = url
        self.text = f'get {url} ...'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.status = f"{response.status}: {response.headers['content-type']}"
                html = await response.text()
        text, title = self.lexer.tex_html(html)
        self.title = title
        self.read_only = False
        self.buffer.text = text
        self.read_only = True

    def get_url_under_cursor(self) -> Optional[str]:
        return 'http://www.github.com/'
