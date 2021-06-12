"""Simple example that scans for devices and connects to first one found."""

import sys
import asyncio
import pyatv

LOOP = asyncio.get_event_loop()


# Method that is dispatched by the asyncio event loop
async def print_what_is_playing(loop):
	"""Find a device and print what is playing."""
	print("Discovering devices on network...")
	atvs = await pyatv.scan(loop, timeout=10)

	if not atvs:
		  print("No device found", file=sys.stderr)
		  return

	for tv in atvs:
		print("Connecting to {0}".format(tv.address))
		atv = await pyatv.connect(tv, loop)

		try:
			playing = await atv.metadata.playing()
			print("Currently playing:")
			print(playing)
		finally:
			# Do not forget to close
			atv.close()


if __name__ == "__main__":
	 # Setup event loop and connect
	 LOOP.run_until_complete(print_what_is_playing(LOOP))
