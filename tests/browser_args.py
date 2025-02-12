import logging
import os

logger = logging.getLogger(__name__)


def get_browser_args(*, headless: bool) -> list[str]:
    args = []

    if not headless:
        args.extend(["--disable-features=UseOzonePlatform", "--ozone-platform=x11"])

    if os.geteuid() == 0:
        logger.warning("Running tests as root! Disabling sandbox")
        args.append("--no-sandbox")

    return args
