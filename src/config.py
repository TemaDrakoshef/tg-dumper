import pathlib

import click
import toml

CURRENT_LANG: str = "ru"


def setup_config():
    sessions = pathlib.Path("sessions")
    if not sessions.exists():
        sessions.mkdir()

    feed_tdata = pathlib.Path("feed_tdata")
    if not feed_tdata.exists():
        feed_tdata.mkdir()

    ftemp = pathlib.Path(".tdtemp")
    if not ftemp.exists():
        ftemp.mkdir()

    config_file = pathlib.Path("config.toml")
    if not config_file.exists():
        config_file.touch()

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
