#!/usr/bin/env python3

# https://iterm2.com/python-api/examples/theme.html

import asyncio, datetime
# pip install iterm2==2.7
import iterm2


async def update(connection, theme):
	now = datetime.datetime.now().replace(microsecond=0).isoformat()

	print(now, "iTerm2 Theme:", theme)

	# Themes have space-delimited attributes, one of which will be light or dark.
	parts = theme.split(" ")

	if "dark" in parts:
		color_preset_name = "Dark Background"
	else:
		color_preset_name = "Light Background"

	preset = await iterm2.ColorPreset.async_get(connection, color_preset_name)

	print(now, "Color Preset:", color_preset_name)

	# Update the list of all profiles and iterate over them.
	for partialProfile in await iterm2.PartialProfile.async_query(connection):
		# Fetch the full profile and then set the color preset in it.
		fullProfile = await partialProfile.async_get_full_profile()
		await fullProfile.async_set_color_preset(preset)


async def iterm2_main(connection):
	app = await iterm2.async_get_app(connection)
	await update(connection, await app.async_get_variable("effectiveTheme"))
	return
	async with iterm2.VariableMonitor(connection, iterm2.VariableScopes.APP, "effectiveTheme", None) as mon:
		while True:
			# Block until theme changes
			theme = await mon.async_get()
			await update(connection, theme)


def main():
	connection = iterm2.Connection()
	connection.run(forever=False, coro=iterm2_main, retry=False, debug=False)


try:
	main()
except KeyboardInterrupt:
	pass
