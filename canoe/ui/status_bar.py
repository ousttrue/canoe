import prompt_toolkit.layout
D = prompt_toolkit.layout.Dimension


class StatusBar:
    def __init__(self, get_text) -> None:
        self.text = ''
        self.container = prompt_toolkit.layout.containers.Window(
            content=prompt_toolkit.layout.controls.FormattedTextControl(
                get_text),
            height=D.exact(1),
            style='class:status',
        )

    def __pt_container__(self) -> prompt_toolkit.layout.containers.Container:
        return self.container
