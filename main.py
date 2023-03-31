import config
import httpx
import json
from auth import get_access_token
from dataclasses import dataclass
from datetime import date
from jackett import search_jackett


@dataclass
class Show:
    title: str
    imdb: str
    s: int
    e: int
    tg_message: str = ""

    def __post_init__(self):
        self.s = f"S0{self.s}" if self.s < 10 else f"S{self.s}"
        self.e = f"E0{self.e}" if self.e < 10 else f"E{self.e}"
        self.tg_message = f"{self.title} {self.s}{self.e} \\({self.imdb}\\)"


def get_oncoming_items(subpath="my/shows"):
    today = date.today().strftime("%Y-%m-%d")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token()}",
        "trakt-api-version": "2",
        "trakt-api-key": config.CLIENT_ID,
    }

    with httpx.Client() as client:
        r = client.get(
            f"https://api.trakt.tv/calendars/{subpath}/{today}/1",
            headers=headers,
        )
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            return []


def send_tg_message(chat_id, message):
    with httpx.Client() as client:
        data_dict = {"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"}

        r = client.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data_dict,
        )

        return r.json()


def main():
    for show in get_oncoming_items():
        show = Show(
            show["show"]["title"],
            show["show"]["ids"]["imdb"],
            show["episode"]["season"],
            show["episode"]["number"],
        )

        uhd, hd, sd = search_jackett(show.imdb, f"{show.s}{show.e}")
        for item in uhd[:2]:
            show.tg_message += f"\n{item.title.replace(show.title, '').replace(show.s, '').replace(show.e, '').strip()} `{item.magnet_uri}`"
        for item in hd[:2]:
            show.tg_message += f"\n{item.title.replace(show.title, '').replace(show.s, '').replace(show.e, '').strip()} `{item.magnet_uri}`"
        if not uhd and not hd:
            for item in sd[:2]:
                show.tg_message += f"\n{item.title.replace(show.title, '').replace(show.s, '').replace(show.e, '').strip()} `{item.magnet_uri}`"
        print(show.tg_message)
        r = send_tg_message(config.CHAT_ID, show.tg_message)
        print(r)


if __name__ == "__main__":
    main()
