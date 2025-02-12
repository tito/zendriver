import logging
import os

logger = logging.getLogger(__name__)

NO_SANDBOX = os.getenv("ZENDRIVER_TEST_NO_SANDBOX", "false") == "true"


def get_browser_args(*, headless: bool) -> list[str]:
    args = []

    if not headless:
        args.extend(["--disable-features=UseOzonePlatform", "--ozone-platform=x11"])

    if NO_SANDBOX:
        logger.warning("Detected ZENDRIVER_TEST_NO_SANDBOX=true! Disabling sandbox")
        args.append("--no-sandbox")

    return args
