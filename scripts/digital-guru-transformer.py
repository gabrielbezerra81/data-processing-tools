from pathlib import Path
import json
from typing import TypedDict, Literal
from datetime import datetime, timezone
import argparse
from scripts.processa_arquivos_peron import process_files_peron


class Infrastructure(TypedDict):
    city_lat_long: str
    country: str
    region: str
    ip: str
    city: str
    user_agent: str


class GuruEvent(TypedDict):
    causer_email: str
    causer_name: str
    infrastructure: Infrastructure
    type: Literal[
        "tracking_updated",
        "user_login_google2fa",
        "checkout_settings_updated",
        "offer_updated",
        "offer_created",
        "user_login",
    ]
    updated_at: int


CSV_HEADER = "Timestamp (UTC),Latitude,Longitude,Country Codes,Display Radius (Meters),Source,Device Tag,Platform"


def create_user_data(path: str):
    file_path = Path(path)

    save_folder = file_path.parent.joinpath("arquivos guru")

    save_folder.mkdir(exist_ok=True)

    with open(file_path, "r+") as file:
        content: list[GuruEvent] = json.load(file)

        users_accesslogs: dict[str, str] = {}
        users_geoloc: dict[str, str] = {}

        for event in content:
            create_acesslog_entry(event, users_accesslogs)

            create_geolocation_entry(event, users_geoloc)

        for user in users_accesslogs:
            log = users_accesslogs[user]
            geoloc = users_geoloc[user]

            log_new_path = save_folder.joinpath(f"access-log-{user}.txt")
            geoloc_new_path = save_folder.joinpath(f"geolocation-{user}.csv")

            with open(log_new_path, "wt+") as log_file:
                log_file.write(log)

            with open(geoloc_new_path, "wt+") as geoloc_file:
                geoloc_file.write(geoloc)

    process_files_peron(str(save_folder.resolve()))


def create_acesslog_entry(event: GuruEvent, users_accesslogs: dict[str, str]):
    if not users_accesslogs.get(event["causer_name"]):
        users_accesslogs[event["causer_name"]] = f"IP List: {event['causer_name']}"

    users_accesslogs[event["causer_name"]] += f"\n{event['infrastructure']['ip']}"


def create_geolocation_entry(event: GuruEvent, users_geoloc: dict[str, str]):
    if not users_geoloc.get(event["causer_name"]):
        users_geoloc[event["causer_name"]] = CSV_HEADER

    timestamp = datetime.fromtimestamp(event["updated_at"], timezone.utc).isoformat()

    [lat, long] = event["infrastructure"]["city_lat_long"].split(",")

    country = event["infrastructure"]["country"]

    display_radius = 0

    source = ""

    device_tag = event["infrastructure"]["user_agent"]

    platform = ""

    users_geoloc[
        event["causer_name"]
    ] += f"\n{timestamp},{lat},{long},{country},{display_radius},{source},{device_tag},{platform}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Manipulador de dados json da Digital Manager Guru"
    )

    parser.add_argument(
        "--arquivo",
        type=str,
        required=True,
        help="Arquivo auditoria-usuarios.json da Digital Manager Guru",
    )

    args = parser.parse_args()

    create_user_data(args.arquivo)
