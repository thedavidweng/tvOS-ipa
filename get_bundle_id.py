"""Extract CFBundleIdentifier (and app icon when available) from an IPA.

Reads a local file if one is passed, otherwise downloads from a URL
(used by generate_json.py for apps missing from bundleId.csv).
"""
import plistlib
import requests
import shutil
import os
import sys
import zipfile


def extract_from_ipa(path, icon_folder="icons/"):
    bundle_id = "com.example.app"
    with zipfile.ZipFile(path, mode="r") as archive:
        info_file = next(
            (n for n in archive.namelist() if n.endswith(".app/Info.plist")),
            None,
        )
        if info_file is None:
            return bundle_id
        folder_path = os.path.dirname(info_file)
        with archive.open(info_file) as fp:
            pl = plistlib.load(fp)
            bundle_id = pl.get("CFBundleIdentifier", bundle_id)

            icon_path = ""
            if "CFBundleIconFiles" in pl.keys():
                try:
                    icon_path = os.path.join(
                        folder_path, pl["CFBundleIconFiles"][0])
                except Exception:
                    pass
            if "CFBundleIcons" in pl.keys():
                try:
                    primary = pl["CFBundleIcons"]["CFBundlePrimaryIcon"]
                    try:
                        icon_prefix = primary["CFBundleIconFiles"][0]
                    except Exception:
                        icon_prefix = primary["CFBundleIconName"]
                    for file_name in archive.namelist():
                        if icon_prefix in file_name and file_name.endswith(".png"):
                            icon_path = file_name
                            break
                except Exception:
                    pass
            if icon_path:
                try:
                    os.makedirs(icon_folder, exist_ok=True)
                    with archive.open(icon_path) as origin, \
                            open(icon_folder + bundle_id + ".png", "wb") as dst:
                        shutil.copyfileobj(origin, dst)
                except Exception:
                    pass
    return bundle_id


def get_single_bundle_id(url, name="temp.ipa"):
    response = requests.get(url)
    with open(name, "wb") as f:
        f.write(response.content)
    try:
        return extract_from_ipa(name)
    finally:
        if os.path.exists(name):
            os.remove(name)


if __name__ == "__main__":
    # Local helper: python get_bundle_id.py <file.ipa> [more...]
    # prints "<bundleId>\t<file>" per file.
    for arg in sys.argv[1:]:
        print(f"{extract_from_ipa(arg)}\t{arg}")
