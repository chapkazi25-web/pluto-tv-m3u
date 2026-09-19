# Pluto TV M3U Playlist

Free IPTV playlist (`.m3u`) generator for Pluto TV live channels. Works with **VLC**, **Tivimate**, and any other player that supports HLS.

Since Pluto TV shut down its old v1 stitcher, every stream now requires a JWT session token fetched from `boot.pluto.tv/v4/start` (no account needed). This repo fetches a fresh token and embeds it in each channel URL.

## Usage

### Ad-hoc playlist

Download the latest generated playlist:

```sh
curl -O https://raw.githubusercontent.com/chapkazi25-web/pluto-tv-m3u/main/pluto.m3u
```

- **VLC:** `vlc pluto.m3u`
- **Tivimate:** add the playlist URL above as a new IPTV playlist source.

```sh
https://raw.githubusercontent.com/chapkazi25-web/pluto-tv-m3u/main/pluto.m3u
```

### Generate it yourself

```sh
python3 pluto_m3u.py
```

This contacts Pluto to get a session token and writes `pluto.m3u` with all 437 live channels grouped by category (`group-title` = genre).

## Token expiry

Session tokens are valid for **~24 hours**. The included GitHub Actions workflow runs every 12 hours and commits a refreshed `pluto.m3u`, so using the `raw.githubusercontent.com` URL above always points at a fresh file.

You can also trigger it manually from the Actions tab (`workflow_dispatch`) or run `python3 pluto_m3u.py` locally whenever playback stops.

## How it works

1. `pluto_m3u.py` calls `boot.pluto.tv/v4/start` with a random `clientID` to obtain a session token (JWT) plus the stitcher URL and stitcher params.
2. Channel metadata (names, numbers, categories) comes from `api.pluto.tv/v2/channels.json`.
3. Each stream URL is built as:

```
{stitcher}/v2/stitch/hls/channel/{channel_id}/master.m3u8?jwt={token}&masterJWTPassthrough=true&{stitcherParams}
```

4. URLs are written to an M3U playlist with the channel's genre as the `group-title`.
