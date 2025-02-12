import logging
import os
import signal
from contextlib import AbstractAsyncContextManager
from enum import Enum
from threading import Event
from typing import AsyncGenerator

import pytest

import zendriver as zd

logger = logging.getLogger(__name__)


class BrowserMode(Enum):
    HEADLESS = "headless"
    HEADFUL = "headful"
    ALL = "all"

    @property
    def fixture_params(self):
        if self == BrowserMode.HEADLESS:
            return [{"headless": True}]
        elif self == BrowserMode.HEADFUL:
            return [{"headless": False}]
        elif self == BrowserMode.ALL:
            return [{"headless": True}, {"headless": False}]


NEXT_TEST_EVENT = Event()


class TestConfig:
    BROWSER_MODE = BrowserMode(os.getenv("ZENDRIVER_TEST_BROWSERS", "all"))
    PAUSE_AFTER_TEST = os.getenv("ZENDRIVER_PAUSE_AFTER_TEST", "false") == "true"
    SANDBOX = os.getenv("ZENDRIVER_TEST_SANDBOX", "false") == "true"
    USE_WAYLAND = os.getenv("WAYLAND_DISPLAY") is not None


class CreateBrowser(AbstractAsyncContextManager):
    def __init__(
        self,
        *,
        headless: bool = True,
        sandbox: bool = TestConfig.SANDBOX,
        browser_args: list[str] | None = None,
    ):
        self.headless = headless
        self.sandbox = sandbox
        self.browser_args = browser_args
        self.browser: zd.Browser | None = None
        self.browser_pid: int | None = None

    def _browser_args(self) -> list[str]:
        args = []
        if not self.headless and TestConfig.USE_WAYLAND:
            # use wayland backend instead of x11
            args.extend(
                ["--disable-features=UseOzonePlatform", "--ozone-platform=wayland"]
            )
        if self.browser_args is not None:
            args.extend(self.browser_args)

        return args

    def config(self) -> zd.Config:
        return zd.Config(
            headless=self.headless,
            sandbox=self.sandbox,
            browser_args=self._browser_args(),
            browser_connection_max_tries=10,
            browser_connection_timeout=1,
        )

    async def __aenter__(self) -> zd.Browser:
        self.browser = await zd.start(self.config())
        browser_pid = self.browser._process_pid
        assert browser_pid is not None and browser_pid > 0
        await self.browser.wait(0)
        return self.browser

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser is not None:
            await self.browser.stop()
            assert self.browser_pid is None


@pytest.fixture
def create_browser() -> type[CreateBrowser]:
    return CreateBrowser


@pytest.fixture(params=TestConfig.BROWSER_MODE.fixture_params)
def headless(request: pytest.FixtureRequest) -> bool:
    return request.param["headless"]


@pytest.fixture
async def browser(
    headless: bool, create_browser: type[CreateBrowser]
) -> AsyncGenerator[zd.Browser, None]:
    NEXT_TEST_EVENT.clear()

    async with create_browser(headless=headless) as browser:
        yield browser

    if TestConfig.PAUSE_AFTER_TEST:
        logger.info(
            "Pausing after test. Send next test hotkey (default Mod+Return) to continue to next test"
        )
        NEXT_TEST_EVENT.wait()
    await browser.stop()
    assert browser._process_pid is None


# signal handler for starting next test
def handle_next_test(signum, frame):
    if not TestConfig.PAUSE_AFTER_TEST:
        logger.warning(
            "Next test signal received, but ZENDRIVER_PAUSE_AFTER_TEST is not set."
        )
        logger.warning(
            "To enable pausing after each test, set ZENDRIVER_PAUSE_AFTER_TEST=true"
        )
        return

    NEXT_TEST_EVENT.set()


signal.signal(signal.SIGUSR1, handle_next_test)
