"""DUM-E entrypoint — keep orchestration here; delegate logic to modules."""

import time

from config import LOOP_DELAY_MS
from utils.logger import log


def boot():
    log("DUM-E boot")


def loop():
    time.sleep_ms(LOOP_DELAY_MS)


if __name__ == "__main__":
    boot()
    while True:
        loop()
