import prompt_toolkit.layout
D = prompt_toolkit.layout.Dimension


class Bar:
    def __init__(self, style="") -> None:
        self.text = ''
        self.container = prompt_toolkit.layout.containers.Window(
            content=prompt_toolkit.layout.controls.FormattedTextControl(
                lambda: self.text),
            height=D.exact(1),
            style=style,
        )

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container
