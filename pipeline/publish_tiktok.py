"""Krok 5: publikace na TikTok pres Content Posting API.

POZOR: vyzaduje schvalenou aplikaci v TikTok Developer Portal (review trva dny)
a scope 'video.publish'. Pred schvalenim funguje jen rezim soukromeho uploadu
(SELF_ONLY) v sandboxu aplikace.

Tok:
  1. refresh_token (z OAuth, ulozen v secrets) -> access_token
  2. inicializace uploadu (FILE_UPLOAD) -> publish_id + upload_url
  3. PUT video na upload_url
  4. (volitelne) polling stavu

Refresh token ziskas jednorazove pres OAuth flow - viz README.
"""
import requests
import config

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"


def _access_token() -> str:
    r = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": config.TIKTOK_CLIENT_KEY,
            "client_secret": config.TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": config.TIKTOK_REFRESH_TOKEN,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def upload(video_path: str, caption: str) -> dict:
    token = _access_token()
    size = __import__("os").path.getsize(video_path)
    chunk = size  # do 64 MB jednim chunkem

    init = requests.post(
        INIT_URL,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json; charset=UTF-8"},
        json={
            "post_info": {
                "title": caption[:2200],
                "privacy_level": "SELF_ONLY",  # zmen na PUBLIC_TO_EVERYONE az po schvaleni app
                "disable_comment": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": chunk,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    init.raise_for_status()
    data = init.json()["data"]
    upload_url = data["upload_url"]

    with open(video_path, "rb") as f:
        put = requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{size - 1}/{size}",
            },
            data=f.read(),
            timeout=120,
        )
    put.raise_for_status()
    return {"publish_id": data["publish_id"], "status": put.status_code}
