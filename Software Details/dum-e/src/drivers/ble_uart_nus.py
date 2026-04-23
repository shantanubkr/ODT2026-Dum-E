"""Nordic UART Service (NUS) peripheral — laptop writes text lines to RX characteristic.

Same UUIDs as Nordic / bleak examples (Luxo-style). Lines are UTF-8 bytes ending in
\\n or \\r; ``pull_lines()`` returns complete commands for ``main.handle_command``.
"""

from micropython import const

import bluetooth

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_WRITE = const(0x0008)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

def _adv_payload(name: str) -> bytes:
    """Flags + short name + NUS 128-bit UUID (for bleak service_uuids scan). Max 31 bytes."""
    nb = name.encode("utf-8")
    if len(nb) > 8:
        nb = nb[:8]
    u = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    ub = bytes(u)
    payload = bytearray()
    payload += b"\x02\x01\x06"
    payload.append(len(nb) + 1)
    payload.append(0x09)
    payload.extend(nb)
    payload.append(17)
    payload.append(0x07)
    payload.extend(ub)
    return bytes(payload)


class BleUartNus:
    def __init__(self, ble, name="DUM-E", rxbuf=256):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services(
            (_UART_SERVICE,)
        )
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()
        self._rx_buffer = bytearray()
        self._name = name
        self._payload = _adv_payload(name)
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle in self._connections and value_handle == self._rx_handle:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)

    def pull_lines(self):
        """Return complete lines (strip \\n/\\r). Leaves partial line in buffer."""
        import machine

        out = []
        irq_state = machine.disable_irq()
        try:
            b = self._rx_buffer
            while True:
                nl = -1
                for idx in range(len(b)):
                    if b[idx] in (0x0A, 0x0D):
                        nl = idx
                        break
                if nl < 0:
                    break
                if nl > 0:
                    try:
                        line = bytes(b[:nl]).decode("utf-8").strip()
                        if line:
                            out.append(line)
                    except Exception:
                        pass
                # MicroPython bytearray does not support ``del b[:nl+1]`` — reassign slice.
                self._rx_buffer = b[nl + 1 :]
                b = self._rx_buffer
        finally:
            machine.enable_irq(irq_state)
        return out

    def notify(self, text: str):
        """Optional: send a line to connected centrals on TX notify (debug)."""
        data = (text if text.endswith("\n") else text + "\n").encode("utf-8")
        for conn_handle in self._connections:
            try:
                self._ble.gatts_notify(conn_handle, self._tx_handle, data)
            except Exception:
                pass

    def close(self):
        for conn_handle in list(self._connections):
            try:
                self._ble.gap_disconnect(conn_handle)
            except Exception:
                pass
        self._connections.clear()

    def _advertise(self, interval_us=500_000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)
