"""Downloads the free, real-world source assets the arrival scenes are built from.

    python blender/fetch_assets.py

Everything lands in blender/assets/ (git-ignored) with a manifest of where each file came from.
  - Poly Haven (polyhaven.com): photo-scanned models, textures and HDRI skies, all CC0.
  - NASA Visible Earth: the Blue Marble Next Generation Earth and its cloud layer (public domain,
    credit "NASA Earth Observatory").
Files already on disk are skipped, so the script is safe to re-run. --hires also fetches the
final-render set beside them: 4K surface textures and the models with 2K textures (models/<id>/2k/).
"""

import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent / 'assets'
UA = {'User-Agent': 'the-archive-portfolio-build/1.0'}

HDRIS = {
    'kloofendal_overcast_puresky': '4k',
    'kloofendal_misty_morning_puresky': '4k',
}

MODELS = [
    # The street.
    'covered_car', 'concrete_road_barrier', 'street_lamp_01', 'modular_electricity_poles',
    'modular_urban_apartments_facade', 'modular_factory_facade', 'modular_fire_escape',
    'utility_box_01', 'old_tyre',
    # What grew back.
    'island_tree_01', 'shrub_01', 'shrub_02', 'fern_02', 'moss_01', 'grass_medium_01',
    'weed_plant_02', 'nettle_plant', 'dead_tree_trunk', 'root_cluster_01', 'rock_moss_set_01',
    # The lab's hardware corner (blender/hardware.py): real scanned bench gear and tools.
    'circuit_board', 'retro_multimeter', 'vintage_radio_transceiver', 'vintage_spacecraft_instrument',
    'industrial_microscope', 'desk_lamp_arm_01', 'metal_tool_chest', 'tool_cart', 'steel_frame_shelves_02',
    'pliers', 'screwdrivers_02', 'measuring_tape_01', 'modular_electric_cables', 'power_box_01',
    'plastic_crate_02', 'metal_stool_02', 'magnifying_glass_01',
]

TEXTURES = [
    'road_damaged', 'concrete_moss', 'mossy_brick', 'forest_leaves_02', 'dirty_concrete',
    'rusty_metal_02', 'worn_mossy_plasterwall', 'concrete_wall_008', 'brown_mud_leaves_01',
    'metal_plate', 'painted_metal_shutter',
]
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough', 'Displacement': 'disp'}

NASA = {
    'earth/blue_marble_21600.jpg': 'https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x21600x10800.jpg',
    'earth/clouds_8192.tif': 'https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud_combined_8192.tif',
}

manifest = []


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def fetch(url, dest, source, licence):
    dest = ROOT / dest
    manifest.append({'file': str(dest.relative_to(ROOT)).replace('\\', '/'), 'url': url,
                     'source': source, 'licence': licence})
    if dest.exists() and dest.stat().st_size > 0:
        return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + '.part')
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, \
            open(tmp, 'wb') as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.replace(dest)
    return dest.stat().st_size


def main():
    hires = '--hires' in sys.argv
    total = 0
    for hid, res in HDRIS.items():
        d = get_json(f'https://api.polyhaven.com/files/{hid}')
        total += fetch(d['hdri'][res]['hdr']['url'], f'hdri/{hid}_{res}.hdr', 'Poly Haven', 'CC0')
    for mid in MODELS:
        files = get_json(f'https://api.polyhaven.com/files/{mid}')['gltf']
        for res, sub in (('1k', ''), ('2k', '2k/')) if hires else (('1k', ''),):
            g = files[res]['gltf']
            total += fetch(g['url'], f'models/{mid}/{sub}{mid}.gltf', 'Poly Haven', 'CC0')
            for rel, inc in g.get('include', {}).items():
                total += fetch(inc['url'], f'models/{mid}/{sub}{rel}', 'Poly Haven', 'CC0')
        print('model', mid, flush=True)
    for tid in TEXTURES:
        d = get_json(f'https://api.polyhaven.com/files/{tid}')
        for key, short in MAPS.items():
            for res in ('2k', '4k') if hires else ('2k',):
                if key in d:
                    total += fetch(d[key][res]['jpg']['url'], f'textures/{tid}/{tid}_{short}_{res}.jpg',
                                   'Poly Haven', 'CC0')
        print('texture', tid, flush=True)
    for rel, url in NASA.items():
        total += fetch(url, rel, 'NASA Earth Observatory (Visible Earth)', 'Public domain')
        print('nasa', rel, flush=True)
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    print(f'downloaded {total / 1e6:.1f} MB')


if __name__ == '__main__':
    sys.exit(main())
