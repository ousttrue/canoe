import asyncio
import argparse
from . import browser
import prompt_toolkit.key_binding.bindings.named_commands


async def main():
    # command line
    parser = argparse.ArgumentParser(description='canoe 🛶 text browser.')

    parser.add_argument('url', help='open url')
    args = parser.parse_args()

    app = browser.Browser()

    #
    # key bindings
    #
    app._keybind(browser.quit, 'Q', filter=app.client.has_focus)
    app._keybind(app.quit_prompt, 'q', eager=True, filter=app.client.has_focus)
    app.key_bindings.add('h', filter=app.client.has_focus)(
        prompt_toolkit.key_binding.bindings.named_commands.get_by_name("backward-char"))
    app._keybind(browser.down, 'j', filter=app.client.has_focus)
    app._keybind(browser.up, 'k', filter=app.client.has_focus)
    app.key_bindings.add('l', filter=app.client.has_focus)(
        prompt_toolkit.key_binding.bindings.named_commands.get_by_name("forward-char"))
    # 0
    # $
    # space
    # b
    # enter
    app._keybind(app.client.enter, 'enter', filter=app.client.has_focus)
    # tab
    # shift-tab
    app._keybind(app.address_bar.focus, 'U', filter=app.client.has_focus)
    app._keybind(app.client.focus, 'escape', filter=app.address_bar.has_focus)
    app._keybind(app.address_bar.enter, 'enter', filter=app.address_bar.has_focus)

    #
    # start up
    #
    app.client.push_url(args.url)

    await app.application.run_async()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
