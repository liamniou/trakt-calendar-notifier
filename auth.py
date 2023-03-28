import config
import httpx
import os
import json
import time
from dataclasses import dataclass, asdict, fields
from typing import Optional


@dataclass
class AuthConfig:
    device_code: Optional[str] = None
    verification_url: Optional[str] = None
    user_code: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    created_at: Optional[int] = None


def class_from_dict(className, dict):
    field_set = {f.name for f in fields(className) if f.init}
    filtered_arg_dict = {k: v for k, v in dict.items() if k in field_set}
    return className(**filtered_arg_dict)


def call_api(method, url, data={}, headers={}):
    r = httpx.request(method, url, data=json.dumps(data), headers=headers)
    print(f"{r} {r.text}")

    if r.status_code == 200:
        return json.loads(r.text)
    else:
        raise f"Exception: {r}"


def get_device_code():
    print("Issuing new device code...")

    values = {"client_id": config.CLIENT_ID}
    headers = {"Content-Type": "application/json"}

    r = class_from_dict(
        AuthConfig,
        call_api(
            "post",
            "https://api.trakt.tv/oauth/device/code",
            values,
            headers,
        ),
    )
    print(f"Go to {r.verification_url} and enter {r.user_code}")
    input("Press any key to continue...")
    with open(".auth", "w") as file:
        file.write(json.dumps(asdict(r), indent=2))
    return r.device_code


def do_token_refresh():
    with open(os.path.join(os.path.dirname(__file__), ".auth"), "r") as j:
        auth = class_from_dict(AuthConfig, json.load(j))

    print("Refreshing token...")

    values = {
        "refresh_token": auth.refresh_token,
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "refresh_token",
    }
    headers = {"Content-Type": "application/json"}

    r = class_from_dict(
        AuthConfig,
        call_api(
            "post",
            "https://api.trakt.tv/oauth/token",
            values,
            headers,
        ),
    )

    r.device_code = auth.device_code

    with open(".auth", "w") as file:
        file.write(json.dumps(asdict(r), indent=2))

    return r.access_token


def poll_access_token():
    with open(os.path.join(os.path.dirname(__file__), ".auth"), "r") as j:
        auth = class_from_dict(AuthConfig, json.load(j))

    print("Polling new access token with device_code...")

    values = {
        "code": auth.device_code,
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/json"}

    r = class_from_dict(
        AuthConfig,
        call_api(
            "post",
            "https://api.trakt.tv/oauth/device/token",
            values,
            headers,
        ),
    )

    r.device_code = auth.device_code

    with open(".auth", "w") as file:
        file.write(json.dumps(asdict(r), indent=2))

    return r.access_token


def get_new_token():
    print("Issuing new token...")
    get_device_code()
    return poll_access_token()


def get_access_token():
    try:
        with open(os.path.join(os.path.dirname(__file__), ".auth"), "r") as j:
            auth_json = json.load(j)
    except (FileNotFoundError, ValueError) as e:
        print(
            f"{e}\nauth file not found or invalid. Starting auth process from scratch..."
        )
        return get_new_token()

    auth = class_from_dict(AuthConfig, auth_json)

    if (time.time() - auth.created_at) <= auth.expires_in and auth.access_token:
        print("Valid token found in .auth")
        return auth.access_token

    if (time.time() - auth.created_at) >= auth.expires_in:
        print("Token expired")
        if auth.refresh_token:
            print("Refresh token found, executing the refresh...")
            return do_token_refresh()

    print("No valid access_token and refresh_token found in .auth")
    return get_new_token()
