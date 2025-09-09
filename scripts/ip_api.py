import time
import numpy
import json
import requests
from typing import TypedDict
from math import ceil

IP_URL = "http://ip-api.com/batch"

InfoIP_API = TypedDict(
    "InfoIP_API",
    {
        "asname": str,
        "as": str,
        "region": str,
        "city": str,
        "mobile": bool,
        "proxy": bool,
        "hosting": bool,
        "lat": float,
        "lon": float,
        "timezone": str,
        "countryCode": str,
        "status": str,
        "query": str,
    },
)


class AccessLog(TypedDict):
    ip: str
    port: str
    date: str


class UserAcessLogs(TypedDict):
    service: str
    identifier: str
    logs: list[AccessLog]


def get_ips_info(user_logs: UserAcessLogs):
    ips_list = list(set([log["ip"] for log in user_logs["logs"]]))

    ips_results: dict[str, InfoIP_API] = {}

    if not len(ips_list):
        return ips_results

    ips_list_by_100 = numpy.array_split(ips_list, ceil(len(ips_list) / 100))

    fields = "asname,as,region,city,mobile,proxy,hosting,lat,lon,timezone,countrycode,status,query"

    for ips in ips_list_by_100:
        try:
            body = json.dumps(ips.tolist())
            response = requests.post(
                IP_URL, data=body, params={"fields": fields, "lang": "pt-BR"}
            )

            # X-Rl => requests remaining in limit
            # X-Ttl => seconds left to reset limit
            requests_left = str(response.headers.get("X-Rl"))
            time_to_reset = str(response.headers.get("X-Ttl"))

            data: list[InfoIP_API] = response.json()

            for index, ip in enumerate(ips):
                ips_results[ip] = data[index]

            if requests_left == "1" or requests_left == "0":
                msg = f"Esperando {time_to_reset} segundos para o limite da API resetar..."
                time_to_reset = int(time_to_reset) + 2

                print(msg)
                time.sleep(time_to_reset)

            # with open("data.json", "w+") as fj:
            #     json.dump(ips_results, fj)

        except Exception as e:
            print("get ip error", e)

            with open(
                f"error-{user_logs['service']}-{user_logs['identifier']}.text",
                "wt+",
                encoding="utf-8",
            ) as erfile:
                erfile.write(f"error {e}\n")
                erfile.write(f"ips list:\n{json.dumps(ips.tolist())}\n")
                if response:
                    erfile.write(f"{json.dumps(response.request.body)}\n")
                    erfile.write(f"reason: {response.reason}\n")
                    erfile.write(f"status_code: {response.status_code}\n")

    return ips_results
