import asyncio

from loguru import logger

from src.impl.home import home_page
from src.config import setup_config
from src.utils import return_to_menu, setup_logging


def main():
    config = setup_config()
    setup_logging()

    while True:
        try:
            home_page(config)
        except BaseException as err:
            return_to_menu(err)


if __name__ == "__main__":
    asyncio.run(main())
