from typing import List, Callable, Tuple
import prompt_toolkit.lexers
import prompt_toolkit.formatted_text
import prompt_toolkit.document
import bs4


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
                self.push(e.get_text(strip=True), style)
            case bs4.element.Doctype():
                pass
            case _:
                t = type(e)
                raise RuntimeError(f'unknwon: {t}')

    def lex_html(self, html: str) -> Tuple[str, str]:
        soup = bs4.BeautifulSoup(html, 'html.parser')
        self.lines = [[]]
        self.title = ''
        for e in soup.children:
            self.traverse(e, '')

        def merge_line(line):
            return ''.join(text for style, text in line)
        lines = [merge_line(line) for line in self.lines]
        return ('\n'.join(lines), self.title)
