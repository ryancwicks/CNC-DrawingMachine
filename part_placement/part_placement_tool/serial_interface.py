import serial
import asyncio

class SerialInterface:

    def __init__(self, port_name, from_serial_queue, to_serial_queue):
        self._serial = serial.Serial(port_name, 115200, timeout=0.25)
        self._from_serial_q = from_serial_queue
        self._to_serial_q = to_serial_queue

        self._running = True

    def stop(self):
        self._running = False

    async def reader(self):
        while self._running:
            await asyncio.sleep(0.1)
            data = self._serial.read(1024)

            if len(data) != 0:
                await self._from_serial_q.put(data)

    async def writer(self):
        while self._running:
            item = await self._to_serial_q.get()
            if item == "q":
                self._running = False
                break
            self._serial.write(item)
            self._to_serial_q.task_done()