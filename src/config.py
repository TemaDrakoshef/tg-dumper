import pathlib

import click
import toml

APP_VERSION = "0.1.0"
CURRENT_LANG: str = "ru"
APP_ID: int = 8257218
APP_HASH: str = "0558e86760a5e3cc2769d9831e7483fa"
SYSTEM_VERSION = "4.16.30-vxXSGWY"


def setup_config():
    sessions = pathlib.Path("sessions")
    if not sessions.exists():
        sessions.mkdir()

    feed_sessions = pathlib.Path("feed_sessions")
    if not feed_sessions.exists():
        feed_sessions.mkdir()

    feed_tdata = pathlib.Path("feed_tdata")
    if not feed_tdata.exists():
        feed_tdata.mkdir()

    ftemp = pathlib.Path(".tdtemp")
    if not ftemp.exists():
        ftemp.mkdir()

    config_file = pathlib.Path("config.toml")
    if not config_file.exists():
        config_file.touch()
        
    accounts_file = pathlib.Path("accounts.txt")
    if not accounts_file.exists():
        accounts_file.touch()


    config = toml.load(config_file)
    click.clear()

    # if "lang" not in config:
    #     config["lang"] = click.prompt(
    #         pretty_prompt(
    #             "Выберите язык интерфейса/Choose interface language"
    #         ),
    #         type=click.Choice(["ru", "en"], case_sensitive=False),
    #         prompt_suffix="> ",
    #     )

    with open(config_file, "w", encoding="utf-8") as file:
        toml.dump(config, file)

    return config
