from typing import Optional, NamedTuple, Dict, List
import dataclasses
import re
import prompt_toolkit.layout.processors
import prompt_toolkit.layout.utils
import prompt_toolkit.document

FOCUS_PATTERN = re.compile(r'\bclass:_(\d+)\b')


@dataclasses.dataclass
class Focus:
    focus_index: int
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
        self.document: Optional[prompt_toolkit.document.Document] = None
        self.focus_map: Dict[int, Focus] = {}
        self.focus_line_map: Dict[int, List[Focus]] = {}

    def apply_transformation(
        self, transformation_input: prompt_toolkit.layout.processors.
        TransformationInput
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
            self.focus_map.clear()
            self.focus_line_map.clear()

        # In case of selection, highlight all matches.
        # Get cursor column.
        fragments = prompt_toolkit.layout.utils.explode_text_fragments(
            fragments)

        if lineno not in self.focus_line_map:
            line_list: List[Focus] = []
            self.focus_line_map[lineno] = line_list
            for i, fragment in enumerate(fragments):
                style, text, *_ = fragment
                m = FOCUS_PATTERN.search(style)
                if m:
                    focus_index = int(m.group(1))
                    focus = self.focus_map.get(focus_index)
                    if focus:
                        focus.push(i, text)
                    else:
                        focus = Focus(focus_index, lineno, i, i, text)
                        self.focus_map[focus_index] = focus
                        line_list.append(focus)

        return prompt_toolkit.layout.processors.Transformation(fragments)

    def _cursor_focus(
            self, doc: prompt_toolkit.document.Document) -> Optional[Focus]:
        line_list = self.focus_line_map.get(doc.cursor_position_row)
        if line_list:
            for focus in line_list:
                if focus.is_hover(doc.cursor_position_row,
                                  doc.cursor_position_col):
                    return focus
        return None

    def _get_next(self, focus: Focus):
        for k, v in self.focus_map.items():
            if v == focus:
                for kk in sorted(self.focus_map.keys()):
                    if kk > k:
                        return self.focus_map[kk]

    def _get_prev(self, focus: Focus):
        for k, v in self.focus_map.items():
            if v == focus:
                for kk in reversed(sorted(self.focus_map.keys())):
                    if kk < k:
                        return self.focus_map[kk]

    def get_focus_next(
            self, doc: prompt_toolkit.document.Document) -> Optional[Focus]:
        focus = self._cursor_focus(doc)
        if focus:
            return self._get_next(focus)
        else:
            target = doc.cursor_position_col
            for row in range(doc.cursor_position_row, len(doc.lines)):
                line_list = self.focus_line_map.get(row)
                if line_list:
                    return line_list[0]
        return None

    def get_focus_prev(
            self, doc: prompt_toolkit.document.Document) -> Optional[Focus]:
        focus = self._cursor_focus(doc)
        if focus:
            return self._get_prev(focus)
        else:
            target = doc.cursor_position_col
            for row in range(doc.cursor_position_row, len(doc.lines)):
                line_list = self.focus_line_map.get(row)
                if line_list:
                    return line_list[-1]
        return None


class HoverProcessor(prompt_toolkit.layout.processors.Processor):

    def __init__(self) -> None:
        super().__init__()
        self.anchor_index: Optional[int] = None

    def apply_transformation(
        self, transformation_input: prompt_toolkit.layout.processors.
        TransformationInput
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

                m = FOCUS_PATTERN.search(style)
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
