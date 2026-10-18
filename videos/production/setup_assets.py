"""One-time asset setup for the brain-freeze shots. Run it inside Blender 4.2+ (Scripting
tab > Open > Run Script, or `blender -b -P setup_assets.py`).

1. Installs and enables the MPFB 2 character extension (GPL add-on, CC0 assets) if missing.
2. Downloads the CC0 MakeHuman asset packs the protagonist needs and installs them in MPFB.
3. Downloads the NIH 3D brain model (CC BY - credit it in the video description).
Poly Haven HDRIs and textures (CC0) download automatically the first time a shot is built.
"""
import os
import sys
import tempfile
import urllib.request

import bpy  # noqa: I001  (bpy first: it puts addon_utils on the path)
import addon_utils

MPFB = "bl_ext.user_default.mpfb"
MPFB_ZIP = ("https://extensions.blender.org/download/sha256:c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad/"
            "add-on-mpfb-v2.0.18.zip")
PACKS = [  # all CC0, from static.makehumancommunity.org/assets/assetpacks.html
    "asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip",
    "asset_packs/shirts01/shirts01_cc0.zip",
    "asset_packs/pants01/pants01_cc0.zip",
    "asset_packs/shoes01/shoes01_cc0.zip",
    "asset_packs/poses01/poses01_cc0.zip",
    "functional/faceunits01.zip",
]
PACK_HOST = "https://files.makehumancommunity.org/"


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    print("downloading", url)
    req = urllib.request.Request(url, headers={"User-Agent": "brain-freeze-setup/1.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest + ".part", "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(dest + ".part", dest)
    return dest


def ensure_mpfb(cache):
    if MPFB not in {m.__name__ for m in addon_utils.modules()}:
        zip_path = download(MPFB_ZIP, os.path.join(cache, "add-on-mpfb-v2.0.18.zip"))
        bpy.ops.extensions.package_install_files(filepath=zip_path, repo="user_default", enable_on_install=True)
    addon_utils.enable(MPFB, default_set=True)
    bpy.ops.wm.save_userpref()


def install_packs(cache):
    from bl_ext.user_default.mpfb.services.assetservice import AssetService
    from bl_ext.user_default.mpfb.services.locationservice import LocationService
    data = LocationService.get_user_data()
    marker = os.path.join(data, ".brain_freeze_packs")
    done = set(open(marker).read().split()) if os.path.exists(marker) else set()
    for rel in PACKS:
        name = os.path.basename(rel)
        if name in done:
            continue
        z = download(PACK_HOST + rel, os.path.join(cache, name))
        err = AssetService.check_asset_pack_zip(z)
        if err not in (None, "STRUCTURE", "MACOS"):
            raise RuntimeError(f"{name}: {err}")
        err = AssetService.fix_and_extract_asset_pack_zip(z, data)
        if err:
            raise RuntimeError(f"{name}: {err}")
        done.add(name)
        with open(marker, "w") as f:
            f.write("\n".join(sorted(done)))
        print("installed", name)


def brain():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:0] = [here, os.path.join(here, "..", "..", "blender-expert"),
                    os.path.join(here, "..", "brain-freeze", "scenes")]
    import head_set
    print("brain model:", head_set.brain_file())


def main():
    cache = os.path.join(tempfile.gettempdir(), "brain_freeze_downloads")
    os.makedirs(cache, exist_ok=True)
    ensure_mpfb(cache)
    install_packs(cache)
    brain()
    print("Setup complete.")


if __name__ in ("__main__", "<run_path>"):
    main()
