from typing import List, Callable, Tuple, Optional
import prompt_toolkit.lexers
import prompt_toolkit.formatted_text
import prompt_toolkit.document
import bs4
import io

INPUT_KEYS = ['name', 'value']


class Focus:
    def __init__(self, tag: bs4.Tag, style_class: str, index: int):
        self.tag = tag
        self.index = index
        self.style_class = style_class

    def get_style(self) -> str:
        return f'class:{self.style_class} class:_{self.index}'


class Anchor(Focus):
    def __init__(slef, tag, index):
        super().__init__(tag, 'anchor', index)


class Input(Focus):
    def __init__(self, input: bs4.Tag, index: int, form: Optional[bs4.Tag]):
        super().__init__(input, 'input', index)
        self.form = form


class BeautifulSoupLexer(prompt_toolkit.lexers.Lexer):

    def __init__(self) -> None:
        super().__init__()
        self.lines: List[prompt_toolkit.formatted_text.StyleAndTextTuples] = [
            [('', '')]]
        self.title = ''
        self.stack: bs4.Tag = []
        self.focus: List[Focus] = []

    def lex_document(self, document: prompt_toolkit.document.Document) -> Callable[[int], prompt_toolkit.formatted_text.StyleAndTextTuples]:
        return self.get_line

    def get_line(self, index: int) -> prompt_toolkit.formatted_text.StyleAndTextTuples:
        return self.lines[index]

    def push(self, text: str, style: str):
        self.lines[-1].append((style, text))

    def new_line(self):
        self.lines.append([])

    def traverse(self, e: bs4.PageElement):
        match e:
            case bs4.Tag() as tag:
                self._process_tag(tag)
            case bs4.element.NavigableString():
                style = self._get_style()
                self.push(e.get_text(strip=True), style)
            case bs4.element.Doctype():
                pass
            case _:
                t = type(e)
                raise RuntimeError(f'unknwon: {t}')

    def _get_style(self) -> str:
        for tag in reversed(self.stack):
            for f in self.focus:
                if f.tag == tag:
                    return f.get_style()
        return ''

    def _process_tag(self, tag: bs4.Tag):
        self.stack.append(tag)
        match tag.name:
            case 'title':
                self.title = tag.text
            case 'a':
                self._push_anchor(tag)
            case 'form':
                # style = self._push_form(tag)
                pass
            case 'input':
                self._push_input(tag)
            case 'p' | 'div':
                self.new_line()
        for child in tag.children:
            self.traverse(child)
        self.stack.pop()

    def _push_anchor(self, tag: bs4.Tag):
        n = len(self.focus)
        self.focus.append(Anchor(tag, n))

    def _push_input(self, tag: bs4.Tag):
        n = len(self.focus)
        form = None
        for f in reversed(self.stack):
            if f.tag == 'form':
                form = f
                break
        self.focus.append(Input(tag, n, form))

        input_type = 'text'
        match tag.get('type'):
            case 'hidden':
                values = ','.join(f'{k}={v}' for k, v in tag.attrs.items() if k in INPUT_KEYS)
                self.push(f'({values})', 'class:input.hidden')

            case 'text' | None:
                name = tag.get('name')
                value = tag.get('value')
                self.push(f'{name}=[{value:20}]', 'class:input.text class:_{n}')

            case 'submit':
                values = ','.join(f'{k}={v}' for k, v in tag.attrs.items() if k in INPUT_KEYS)
                self.push(f'[{values}]', 'class:input.submit class:_{n}')

            case _:
                values = ','.join(f'{k}={v}' for k, v in tag.attrs.items())
                self.push(f'({values})', 'class:input.unknown')

    def lex_html(self, html: str) -> Tuple[str, str]:
        soup = bs4.BeautifulSoup(html, 'html.parser')
        self.lines = [[]]
        self.title = ''
        for e in soup.children:
            self.traverse(e)

        def merge_line(line):
            return ''.join(text for style, text in line)
        lines = [merge_line(line) for line in self.lines]
        return ('\n'.join(lines), self.title)
