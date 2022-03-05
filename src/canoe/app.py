import prompt_toolkit.application


class App:
    def __init__(self) -> None:
        self.application = prompt_toolkit.application.Application(
            full_screen=True)
