from src.impl.home import home_page
from src.config import setup_config
from src.utils import setup_logging


def main():
    setup_config()
    setup_logging()
    
    home_page()


if __name__ == "__main__":
    main()
