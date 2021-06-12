"""Simple example showing of pairing."""

import sys
import asyncio

from pyatv import scan, pair
from pyatv.const import Protocol


LOOP = asyncio.get_event_loop()


# Method that is dispatched by the asyncio event loop
async def pair_with_device(loop, MAC):
	"""Make it possible to pair with device."""
	atvs = await scan(loop, timeout=5, protocol=Protocol.MRP)

	if not atvs:
		sys.stdout("No device found\n")
		return

	for at in atvs:
		try:
			mac = at.device_info.mac
			ip = at.address 
			sys.stdout.write("ip: {} \n".format( ip ))
			sys.stdout.write("mac: {} \n".format( mac ))
			sys.stdout.write("all: {} \n".format( at ))
			if MAC != mac: continue
			pairing = await pair(at, Protocol.MRP, loop)
			await pairing.begin()

			sys.stdout.write("tv: {}\n".format(str(at)))
			sys.stdout.write("Enter PIN: \n")
			pin = int(sys.stdin.readline().strip("\n"))
			pairing.pin(pin)
			await pairing.finish()

			# Give some feedback about the process
			if pairing.has_paired:
				sys.stdout.write("Paired with device!\n")
				sys.stdout.write("Credentials:{}\n".format(pairing.service.credentials))
			else:
				sys.stdout.write("Did not pair with device!\n")

			await pairing.close()
		except Exception as e:
			sys.stdout.write(u"line:{}, error={}\n".format(sys.exc_info()[2].tb_lineno, e))


if __name__ == "__main__":
	# Setup event loop and connect
	MAC = sys.argv[1]
	LOOP.run_until_complete(pair_with_device(LOOP,MAC))
