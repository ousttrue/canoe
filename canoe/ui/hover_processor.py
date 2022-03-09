from typing import Optional, NamedTuple, Dict, List
import dataclasses
import re
import prompt_toolkit.layout.processors
import prompt_toolkit.layout.utils
import prompt_toolkit.document

ANCHORE_PATTERN = re.compile(r'\bclass:anchor class:_(\d+)\b')


@dataclasses.dataclass
class Anchor:
    anchor_index: int
    row: int
    col_start: int
    col_end: int
    text: str

    def push(self, col: int, char: str):
        self.end = col
        self.text += char

    def is_hover(self, row: int, col: int) -> bool:
        if row != self.row:
            return False
        if col < self.col_start:
            return False
        if col > self.col_end:
            return False
        return True


class AnchorProcessor(prompt_toolkit.layout.processors.Processor):
    def __init__(self) -> None:
        super().__init__()
        self.document = None
        self.anchor_map: Dict[int, Anchor] = {}
        self.anchor_line_map: Dict[int, List[Anchor]] = {}

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

        if self.document != document:
            self.document = document
            self.anchor_map.clear()
            self.anchor_line_map.clear()

        # In case of selection, highlight all matches.
        # Get cursor column.
        fragments = prompt_toolkit.layout.utils.explode_text_fragments(
            fragments)

        if lineno not in self.anchor_line_map:
            line_list: List[Anchor] = []
            self.anchor_line_map[lineno] = line_list
            for i, fragment in enumerate(fragments):
                style, text, *_ = fragment
                m = ANCHORE_PATTERN.search(style)
                if m:
                    anchor_index = int(m.group(1))
                    anchor = self.anchor_map.get(anchor_index)
                    if anchor:
                        anchor.push(i, text)
                    else:
                        anchor = Anchor(anchor_index, lineno, i, i, text)
                        self.anchor_map[anchor_index] = anchor
                        line_list.append(anchor)

        return prompt_toolkit.layout.processors.Transformation(fragments)

    def _cursor_anchor(self, doc: prompt_toolkit.document.Document) -> Optional[Anchor]:
        line_list = self.anchor_line_map.get(doc.cursor_position_row)
        if line_list:
            for anchor in line_list:
                if anchor.is_hover(doc.cursor_position_row, doc.cursor_position_col):
                    return anchor

    def get_anchor_next(self, doc: prompt_toolkit.document.Document) -> Optional[Anchor]:
        anchor = self._cursor_anchor(doc)
        if anchor:
            return self.anchor_map.get(anchor.anchor_index+1)
        else:
            target = doc.cursor_position_col
            for row in range(doc.cursor_position_row, len(doc.lines)):
                line_list = self.anchor_line_map.get(row)
                if line_list:
                    for anchor in line_list:
                        if not isinstance(target, int) or anchor.col_start > target:
                            return anchor
                target = None

    def get_anchor_prev(self, doc: prompt_toolkit.document.Document) -> Optional[Anchor]:
        anchor = self._cursor_anchor(doc)
        if anchor:
            return self.anchor_map.get(anchor.anchor_index-1)
        else:
            target = doc.cursor_position_col
            for row in range(doc.cursor_position_row, len(doc.lines)):
                line_list = self.anchor_line_map.get(row)
                if line_list:
                    for anchor in line_list:
                        if not isinstance(target, int) or anchor.col_end < target:
                            return anchor
                target = None


class HoverProcessor(prompt_toolkit.layout.processors.Processor):
    def __init__(self) -> None:
        super().__init__()
        self.anchor_index: Optional[int] = None

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
        if isinstance(cursor_column, int):
            if cursor_column < len(fragments):
                style, text = fragments[cursor_column]  # type: ignore

                m = ANCHORE_PATTERN.search(style)
                if m:
                    self.anchor_index = int(m.group(1))
                    for i, fragment in enumerate(fragments):
                        style, text, *_ = fragment
                        matched = m.group(0)
                        if matched in style:
                            fragments[i] = (style + ' reverse ', text)
                else:
                    self.anchor_index = None

        return prompt_toolkit.layout.processors.Transformation(fragments)
