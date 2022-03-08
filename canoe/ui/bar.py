import prompt_toolkit.layout
D = prompt_toolkit.layout.Dimension


class Bar:
    def __init__(self, get_text, style="") -> None:
        self.container = prompt_toolkit.layout.containers.Window(
            content=prompt_toolkit.layout.controls.FormattedTextControl(
                get_text),
            height=D.exact(1),
            style=style,
        )

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container
