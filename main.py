from src.impl.home import home_page
from src.config import setup_config


def main():
    setup_config()
    home_page()


if __name__ == "__main__":
    main()
