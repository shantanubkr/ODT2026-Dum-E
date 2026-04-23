"""
Laptop-only: Nordic UART Service client (Bleak) — same NUS UUIDs as ``src/drivers/ble_uart_nus``.

Set ``DUM_E_BLE=1``. Optional: ``DUM_E_BLE_NAME`` (default ``DUM-E``), ``DUM_E_BLE_ADDRESS``
(macOS UUID or ``AA:BB:...``). Sends the same plain-text lines as USB serial (``hello\\n``, etc.).
"""

from __future__ import annotations

import asyncio
import os
import re
import threading

from utils.logger import log

try:
    from bleak import BleakClient, BleakScanner

    _BLEAK_OK = True
except ImportError:
    _BLEAK_OK = False

NUS_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

_SCAN_TIMEOUT = float(os.environ.get("DUM_E_BLE_SCAN_TIMEOUT", "20"))
_CONNECT_TIMEOUT = float(os.environ.get("DUM_E_BLE_CONNECT_TIMEOUT", "15"))
_BLE_INIT_FUT_TIMEOUT = _CONNECT_TIMEOUT + 2 * _SCAN_TIMEOUT + 25


def _normalize_ble_address(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    if re.fullmatch(
        r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}",
        s,
    ):
        return s.upper()
    return s.upper().replace("-", ":")


class BleNusClient:
    def __init__(self) -> None:
        if not _BLEAK_OK:
            raise RuntimeError("bleak not installed — pip install bleak")
        self._name = (os.environ.get("DUM_E_BLE_NAME") or "DUM-E").strip()
        self._address = _normalize_ble_address(os.environ.get("DUM_E_BLE_ADDRESS", ""))
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._client: BleakClient | None = None
        self._ready = threading.Event()
        self._start_loop()
        log(
            "[BleNus] scan/connect starting (timeout ≈ %.0fs) — app stays responsive in background"
            % (_BLE_INIT_FUT_TIMEOUT,)
        )
        fut = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        fut.result(timeout=_BLE_INIT_FUT_TIMEOUT)

    def _start_loop(self) -> None:
        self._ready.clear()
        self._loop = asyncio.new_event_loop()

        def _runner() -> None:
            asyncio.set_event_loop(self._loop)
            self._ready.set()
            assert self._loop is not None
            self._loop.run_forever()

        self._loop_thread = threading.Thread(target=_runner, name="dum-e-ble", daemon=True)
        self._loop_thread.start()
        self._ready.wait(timeout=5.0)

    def _run_coro(self, coro, timeout: float = 25.0):
        assert self._loop is not None
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=timeout)

    async def _async_connect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None

        if self._address:
            log("[BleNus] connect to DUM_E_BLE_ADDRESS=" + self._address)
            self._client = BleakClient(self._address)
            await self._client.connect()
            return

        dev = await BleakScanner.find_device_by_name(self._name, timeout=_SCAN_TIMEOUT)
        if dev is None:
            found = list(await BleakScanner.discover(timeout=min(10.0, _SCAN_TIMEOUT)))
            want = self._name.lower()
            for d in found:
                n = (d.name or "").strip()
                if n and (n == self._name or want in n.lower() or n.lower() in want):
                    dev = d
                    break
        if dev is None:
            try:
                by_svc = list(
                    await BleakScanner.discover(
                        timeout=min(12.0, _SCAN_TIMEOUT),
                        service_uuids=[NUS_SERVICE_UUID],
                    )
                )
            except (TypeError, ValueError, RuntimeError):
                by_svc = []
            if len(by_svc) >= 1:
                dev = by_svc[0]
        if dev is None:
            raise RuntimeError(
                "No DUM-E BLE peripheral — name=%r; set DUM_E_BLE_ADDRESS or "
                "advertise USE_BLE_NUS on the ESP32." % (self._name,)
            )

        self._client = BleakClient(dev)
        await self._client.connect()
        log("[BleNus] connected to %r @ %s" % (dev.name, dev.address))

    def is_connected_safe(self) -> bool:
        """Best-effort link state for status/logs (may be queried from any thread)."""
        if self._client is None:
            return False
        try:
            return bool(self._client.is_connected)
        except Exception:
            return False

    async def _async_write(self, payload: bytes) -> None:
        if self._client is None or not self._client.is_connected:
            await self._async_connect()
        assert self._client is not None
        await self._client.write_gatt_char(NUS_RX_UUID, payload, response=False)

    def write_line(self, text: str) -> None:
        line = text if text.endswith("\n") else text + "\n"
        data = line.encode("utf-8")
        with self._lock:
            try:
                self._run_coro(self._async_write(data), timeout=25.0)
            except Exception as exc:  # noqa: BLE001
                log("[BleNus] send error: " + str(exc) + " — reconnect")
                self._run_coro(self._async_connect(), timeout=_CONNECT_TIMEOUT + 5)
                self._run_coro(self._async_write(data), timeout=25.0)

    def close(self) -> None:
        if self._loop is not None and self._client is not None:

            async def _disc() -> None:
                try:
                    if self._client.is_connected:
                        await self._client.disconnect()
                except Exception:
                    pass

            try:
                fut = asyncio.run_coroutine_threadsafe(_disc(), self._loop)
                fut.result(timeout=5)
            except Exception:
                pass
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread is not None:
            self._loop_thread.join(timeout=3.0)
