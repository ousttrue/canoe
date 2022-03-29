import prompt_toolkit.styles

CLIENT_STYLE = prompt_toolkit.styles.Style.from_dict({
    "status": "reverse",
    "status.position": "#aaaa00",
    "status.key": "#ffaa00",
    "not-searching": "#888888",
    #
    'anchor': '#0044ff underline',

    'form': '#44ff00',
    'input.text': '#44ff00',
    'input.submit': '#44ff00 underline',
    'input.hidden': '#224400 underline',
    'input.unknown': '#442200 underline',
})
