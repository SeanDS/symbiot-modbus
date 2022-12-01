"""Modbus provider for Symbiot."""

import asyncio
import logging
import warnings
from pymodbus.client import AsyncModbusTcpClient
from symbiot.receiver import Receiver

LOGGER = logging.getLogger("symbiot.receiver.modbus")


class Modbus(Receiver):
    def __init__(self, **options):
        self.query_interval = float(options.pop("query_interval"))
        self.channels = options.pop("channels")
        connection = options.pop("connection")
        self.host = connection.pop("host")
        self.port = int(connection.pop("port"))
        self.slave_id = int(connection.pop("slave_id"))

        super().__init__(**options)

    async def run(self):
        loop = asyncio.get_running_loop()
        next_receive = loop.time()

        try:
            while True:
                if loop.time() >= next_receive:
                    try:
                        await self._receive()
                    except Exception as exc:
                        LOGGER.exception(exc)  # Report exceptions but keep going.

                    next_receive += self.query_interval

                await asyncio.sleep(0)
        finally:
            # Write empty values to channels to signify going offline.
            LOGGER.debug("clearing MQTT topics")
            for channel in self.channels.values():
                await self.mqtt_client.publish(topic=channel["topic"], payload="")

    async def _receive(self):
        client = AsyncModbusTcpClient(host=self.host, port=self.port)
        await client.connect()

        for channel, channel_config in self.channels.items():
            LOGGER.debug(f"reading {channel}")
            response = await client.read_input_registers(
                address=int(channel_config["address"]),
                count=int(channel_config["quantity"]),
                slave=self.slave_id,
            )
            registers = list(response.registers)
            LOGGER.info(f"response registers: {registers}")

            if channel_config["combine"]:
                if channel_config["combine_reversed"]:
                    registers = reversed(registers)

                value = sum([value * 65536**i for i, value in enumerate(registers)])
            else:
                if len(registers) > 1:
                    # Config asked for >1 values but didn't specify combine = true.
                    warnings.warn(
                        f"Discarding {len(registers) - 1} extra registry entry(ies)"
                    )

                value = registers[0]

            topic = channel_config["topic"]
            LOGGER.info(f"publishing value {repr(value)} to topic {topic}")
            await self.mqtt_client.publish(topic=topic, payload=value)

        # Clean up.
        await client.close()
