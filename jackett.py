import httpx
import json
import sys
from dataclasses import dataclass
from typing import Optional
from config import JACKETT_API_KEY


BASE_URL = "http://192.168.0.37:9117/api/v2.0/indexers"


@dataclass
class Jackett:
    title: str
    magnet_uri: Optional[str] = None


def normalize_string(string):
    return (
        str(string)
        .replace(".", " ")
        .replace("-", " ")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def search_jackett(imdb_id, search_string):
    print(f"Looking for {imdb_id} {search_string}")
    with httpx.Client() as client:
        r = client.get(
            f"{BASE_URL}/all/results?apikey={JACKETT_API_KEY}&Query={imdb_id}%20{search_string}&Tracker%5B%5D=rarbg",
            timeout=60,
        )
        if r.status_code != 200:
            print("Something went wrong")
            sys.exit(1)

        results = json.loads(r.text)["Results"]

        uhd = []
        hd = []
        sd = []

        for i in results:
            r_imdb = str(i["Imdb"])
            r_title = normalize_string(i["Title"])
            magnet_uri = i["MagnetUri"]
            filters_4k = [search_string, "H265", "2160p"]
            if r_imdb in imdb_id and all([x in r_title for x in filters_4k]):
                uhd.append(Jackett(r_title, magnet_uri))
            filters_hd = [search_string, "H264", "1080p"]
            if r_imdb in imdb_id and all([x in r_title for x in filters_hd]):
                hd.append(Jackett(r_title, magnet_uri))
            filters_sd = [search_string]
            if r_imdb in imdb_id and all([x in r_title for x in filters_sd]):
                sd.append(Jackett(r_title, magnet_uri))

        return uhd, hd, sd
