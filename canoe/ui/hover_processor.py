from typing import Optional
import re
import prompt_toolkit.layout.processors
import prompt_toolkit.layout.utils

ANCHORE_PATTERN = re.compile(r'\bclass:anchor class:_(\d+)\b')


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
