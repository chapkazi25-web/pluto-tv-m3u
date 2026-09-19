import base64
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid

BOOT_URL = "https://boot.pluto.tv/v4/start"
CHANNELS_URL = "https://api.pluto.tv/v2/channels.json"
OUT_FILE = "pluto.m3u"

APP_VERSION = "8.0.0-111b2b9dc00bd0bea9030b30662159ed9e7c8bc6"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def token_expiry(token):
    try:
        p = token.split(".")[1]
        p += "=" * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p)).get("exp", 0)
    except Exception:
        return 0


def boot():
    params = {
        "appName": "web",
        "appVersion": APP_VERSION,
        "deviceVersion": "122.0.0",
        "deviceModel": "web",
        "deviceMake": "chrome",
        "deviceType": "web",
        "clientID": str(uuid.uuid4()),
        "clientModelNumber": "1.0.0",
        "serverSideAds": "false",
        "drmCapabilities": "widevine:L3",
        "blockingMode": "",
    }
    headers = {
        "authority": "boot.pluto.tv",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://pluto.tv",
        "referer": "https://pluto.tv/",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": UA,
    }
    req = urllib.request.Request(BOOT_URL + "?" + urllib.parse.urlencode(params), headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_channels():
    req = urllib.request.Request(CHANNELS_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def build_stream_url(channel_id, token, stitcher, stitcher_params):
    url = (
        f"{stitcher}/v2/stitch/hls/channel/{channel_id}/master.m3u8"
        f"?jwt={token}&masterJWTPassthrough=true"
    )
    if stitcher_params:
        url += "&" + stitcher_params
    return url


def main():
    cfg = boot()
    token = cfg["sessionToken"]
    stitcher = cfg.get("servers", {}).get("stitcher",
                                           "https://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv")
    stitcher_params = cfg.get("stitcherParams", "")
    exp = token_expiry(token)
    if exp:
        deadline = datetime.datetime.fromtimestamp(exp)
        print(f"Session token valid until {deadline.isoformat(sep=' ')} "
              f"({(exp - time.time()) / 3600:.1f} h) - refresh before then")

    channels = fetch_channels()
    lines = ["#EXTM3U"]
    count = 0
    for c in channels:
        if not c.get("isStitched"):
            continue
        name = c.get("name") or c.get("slug")
        number = c.get("number")
        category = c.get("category") or "Misc"
        url = build_stream_url(c["_id"], token, stitcher, stitcher_params)
        lines.append(f'#EXTINF:-1 tvg-id="{c.get("slug")}" tvg-name="{name}" '
                     f'group-title="{category}" channel-number="{number}",{name}')
        lines.append(url)
        count += 1
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {count} channels to {OUT_FILE}")


if __name__ == "__main__":
    main()