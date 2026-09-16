"""Regenerate apps.json from this repo's Releases.

Naming convention (no trailing tag of any kind):
    <AppName>_<Version>.ipa                     (decrypted only)
    <AppName>_<Version>_<Tweak>_<TweakVer>.ipa  (injected)

Bundle IDs are resolved from bundleId.csv first; only unknown apps are
downloaded once to extract CFBundleIdentifier (plus icon when available).
"""
from github import Github
import json
import argparse
import pandas as pd
from get_bundle_id import get_single_bundle_id
import os
import shutil


REPO_NAME = "thedavidweng/tvOS-ipa"


def parse_asset_name(filename):
    """Return (app_name, version, tweaks_text)."""
    name = filename[:-4] if filename.endswith(".ipa") else filename
    try:
        app_name, version = name.rsplit("_", 1)
        tweaks_text = "Decrypted"
    except ValueError:
        app_name, version, tweaks_text = name, "Unknown", None
    return app_name, version, tweaks_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", help="Github token")
    args = parser.parse_args()
    token = args.token

    out_file = "apps.json"
    clone_file = "index.html"

    with open(out_file, "r") as f:
        data = json.load(f)

    if os.path.exists("bundleId.csv"):
        df = pd.read_csv("bundleId.csv")
    else:
        df = pd.DataFrame(columns=["name", "bundleId"])

    # clear apps
    data["apps"] = []

    g = Github(token)
    repo = g.get_repo(REPO_NAME)
    releases = repo.get_releases()

    for release in releases:
        print(release.title)

        for asset in release.get_assets():
            if not asset.name.endswith(".ipa"):
                continue
            date = asset.created_at.strftime("%Y-%m-%d")
            full_date = asset.created_at.strftime("%Y%m%d%H%M%S")
            app_name, version, tweaks = parse_asset_name(asset.name)

            if app_name in df.name.values:
                bundle_id = str(df[df.name == app_name].bundleId.values[0])
            else:
                bundle_id = get_single_bundle_id(asset.browser_download_url)
                df = pd.concat([df, pd.DataFrame(
                    {"name": [app_name], "bundleId": [bundle_id]})], ignore_index=True)

            icon_url = (f"https://raw.githubusercontent.com/{REPO_NAME}"
                        f"/main/icons/{bundle_id}.png")
            data["apps"].append(
                {
                    "name": app_name,
                    "realBundleID": bundle_id,
                    "bundleID": bundle_id,
                    "bundleIdentifier": bundle_id,
                    "version": version,
                    "versionDate": date,
                    "fullDate": full_date,
                    "size": asset.size,
                    "down": asset.browser_download_url,
                    "downloadURL": asset.browser_download_url,
                    "developerName": "",
                    "localizedDescription": tweaks,
                    "icon": icon_url,
                    "iconURL": icon_url,
                }
            )
            data["apps"].sort(key=lambda x: x["fullDate"], reverse=True)

    df.to_csv("bundleId.csv", index=False)

    with open(out_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    shutil.copyfile(out_file, clone_file)
