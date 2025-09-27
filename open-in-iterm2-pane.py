#!/usr/bin/env python3

import asyncio
import iterm2


async def main():
	connection = await iterm2.Connection.async_create()

	app = await iterm2.async_get_app(connection)

	window = app.current_terminal_window or await iterm2.Window.async_create(connection)

	session = window.current_tab.current_session
	new_pane = await session.async_split_pane(vertical=True, before=False)

	# new_pane_2 = await new_pane.async_split_pane(vertical=False, before=False)

	await new_pane.async_send_text("date +%s\n")


def run():
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)

	try:
		loop.run_until_complete(main())
	finally:
		loop.close()


if __name__ == "__main__":
	run()
