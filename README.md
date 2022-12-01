# symbiot-modbus
Modbus provider for [symbiot](https://github.com/SeanDS/symbiot).

## Example
Assume you have a Modbus master at `mymodbusserver.example.org` with 32-bit channels at addresses
`229` and `231`. This would require a `bridge.toml` file with the following content:

```toml
[mqtt]
broker_host = "mymqtthost.example.org"

[modbus]
query_interval = 30

[modbus.connection]
host = "mymodbusserver.example.org"
port = 502
slave_id = 1
[modbus.channels.chan1]
address = 229
quantity = 2
combine = true
combine_reversed = false
topic = "mydevice/chan1"

[modbus.channels.chan2]
address = 231
quantity = 2
combine = true
combine_reversed = false
topic = "mydevice/chan2"
```

Start the bridge with `python -m symbiot /path/to/bridge.toml`. The values from the Modbus master
then appear as MQTT topics at `mydevice/chan1` and `mydevice/chan2`.

## Credits
Sean Leavey <sean.leavey@stfc.ac.uk>
