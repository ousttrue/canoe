import asyncio
import argparse
import prompt_toolkit.key_binding.bindings.named_commands
import prompt_toolkit.key_binding
import logging
logger = logging.getLogger(__name__)


def quit(event: prompt_toolkit.key_binding.KeyPressEvent):
    event.app.exit()


def up(event: prompt_toolkit.key_binding.KeyPressEvent) -> None:
    event.current_buffer.auto_up(count=event.arg)


def down(event: prompt_toolkit.key_binding.KeyPressEvent) -> None:
    event.current_buffer.auto_down(count=event.arg)


async def main():
    #
    # command line
    #
    parser = argparse.ArgumentParser(description='canoe 🛶 text browser.')

    parser.add_argument('url', help='open url')
    args = parser.parse_args()

    #
    # worker
    #
    from .async_processor import AsyncProcessor
    processor = AsyncProcessor()

    #
    # UI
    #
    from .ui.root import Root
    root = Root(processor.queue)

    #
    # key bindings
    #
    root._keybind(quit, 'Q', filter=root.view.has_focus)
    root._keybind(root.quit_prompt, 'q', eager=True,
                  filter=root.view.has_focus)
    root.key_bindings.add('h', filter=root.view.has_focus)(
        prompt_toolkit.key_binding.bindings.named_commands.get_by_name("backward-char"))
    root._keybind(down, 'j', filter=root.view.has_focus)
    root._keybind(up, 'k', filter=root.view.has_focus)
    root.key_bindings.add('l', filter=root.view.has_focus)(
        prompt_toolkit.key_binding.bindings.named_commands.get_by_name("forward-char"))
    # 0
    # $
    # space
    # b
    root._keybind(root.enter, 'enter', filter=root.view.has_focus)
    root._keybind(root.view.focus_next, 'tab', filter=root.view.has_focus)
    root._keybind(root.view.focus_prev, 's-tab', filter=root.view.has_focus)
    # shift-tab
    root._keybind(root.address_bar.focus, 'U', filter=root.view.has_focus)
    root._keybind(root.view.focus, 'escape',
                  filter=root.address_bar.has_focus)
    root._keybind(root.address_bar.enter, 'enter',
                  filter=root.address_bar.has_focus)

    #
    # start up
    #
    root.client.push_url(args.url)

    await root.application.run_async()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.debug('start')
    asyncio.get_event_loop().run_until_complete(main())
