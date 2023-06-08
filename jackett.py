import httpx
import json
import sys
import time
from dataclasses import dataclass
from typing import Optional
from config import JACKETT_API_KEY


BASE_URL = "http://192.168.0.37:9117/api/v2.0/indexers"


@dataclass
class Jackett:
    title: str
    magnet_uri: Optional[str] = None


def query_api(imdb_id, search_string):
    with httpx.Client() as client:
        r = client.get(
            f"{BASE_URL}/all/results?apikey={JACKETT_API_KEY}&Query={imdb_id}%20{search_string}&_={time.time()}",
            timeout=60,
        )
        if r.status_code != 200:
            print("Something went wrong")
            sys.exit(1)

        return json.loads(r.text)["Results"]


def search_jackett(show_title, imdb_id, search_string):
    print(f"Looking for {imdb_id} {search_string}")
    imdb_results = query_api(imdb_id, search_string)
    print(f"Looking for {show_title} {search_string}")
    name_results = query_api(show_title, search_string)

    results = imdb_results + name_results
    unique_results = [i for n, i in enumerate(results) if i not in results[n + 1 :]]
    sorted_unique_results = sorted(
        unique_results, key=lambda k: k["Seeders"], reverse=True
    )

    uhd = []
    hd = []
    sd = []

    for i in sorted_unique_results:
        r_imdb = str(i["Imdb"])
        r_title = i["Title"]
        magnet_uri = i["MagnetUri"] if i["MagnetUri"] else i["Details"]
        if search_string in r_title:
            if r_imdb in imdb_id or f"{show_title} {search_string}" in r_title.replace(
                ".", " "
            ):
                if "2160p" in r_title:
                    uhd.append(Jackett(r_title, magnet_uri))
                elif "1080p" in r_title:
                    hd.append(Jackett(r_title, magnet_uri))
                else:
                    sd.append(Jackett(r_title, magnet_uri))

    return uhd, hd, sd
