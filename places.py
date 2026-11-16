import json
import math
import re

import byml
from game import ROOT

CACHE = ROOT / "data" / "places.json"
LANDMARKS = ROOT / "data" / "landmarks.json"
NEAR = 45.0

AREA_NAMES = {
    "LostWood": "Lost Woods", "InsideTheDekuTree": "Inside the Deku Tree", "DodongoCavern": "Dodongo's Cavern",
    "InsideJabuJabuBelly": "Inside Jabu-Jabu's Belly", "BottomOfTheWell": "Bottom of the Well",
    "InsideGanonCastle": "Inside Ganon's Castle", "GerudoTrainingGround": "Gerudo Training Ground",
    "HyruleCastle": "Hyrule Castle", "LonLonRanch": "Lon Lon Ranch", "ZoraDomain": "Zora's Domain",
    "ZoraFountain": "Zora's Fountain", "ZoraRiver": "Zora's River", "GerudoFortress": "Gerudo's Fortress",
    "Market": "Castle Town Market", "SacredForestMeadow": "Sacred Forest Meadow",
}

FACILITIES = {
    1: "the Happy Mask Shop", 3: "the Gerudo Training Ground entrance", 4: "the Bombchu Shop",
    5: "Dampé's grave", 6: "the singing frogs", 7: "the Horseback Archery range", 8: "the Cucco pen",
    9: "the horse race track", 11: "a Great Fairy Fountain", 13: "the Kokiri Shop", 14: "the Goron Shop",
    15: "the Zora Shop", 16: "the Potion Shop", 17: "the Potion Shop", 18: "the Bazaar", 19: "the Bazaar",
    20: "the Shooting Gallery", 21: "the Shooting Gallery", 22: "Bombchu Bowling", 23: "the Treasure Chest Game",
    24: "the House of Skulltula", 26: "Dampé's digging game", 27: "the Diving Game", 28: "the Fishing Pond",
    29: "Granny's Potion Shop", 30: "the Bottle shop", 31: "the Skull Kid stump", 32: "the running man",
    33: "the Deku Scrub stage", 34: "the bean seller", 35: "a captured carpenter", 36: "a captured carpenter",
    37: "a captured carpenter", 38: "the Gerudo guard post",
}

PEOPLE = {
    "Mido": "Mido", "Saria": "Saria", "Kaepora": "Kaepora Gaebora", "Darunia": "Darunia", "Talon": "Talon",
    "Malon": "Malon", "Ingo": "Ingo", "Dampe": "Dampé", "SkullKid": "Skull Kid", "Ruto": "Ruto",
    "KingZora": "King Zora", "Zelda": "Zelda", "Impa": "Impa", "Biggoron": "Biggoron", "SkullDad": "the Skulltula family",
    "Fishman": "the fishing pond owner", "DekuTreeChild": "the Deku Sprout", "GreatFairy": "a Great Fairy",
    "Carpenter": "the carpenters", "Scarecrow": "the scarecrows", "Windmill": "the windmill man",
    "Anju": "the Cucco lady", "Beggar": "the beggar", "Nabooru": "Nabooru", "Medigoron": "Medigoron",
    "Business": "a Deku Scrub salesman",
}


def area_name(area):
    if area in AREA_NAMES:
        return AREA_NAMES[area]
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", area)


ITEM_NAMES = {
    "Item_Sword_Kokiri": "Kokiri Sword", "TBox_Shield_Deku": "Deku Shield", "Shop_Weapon_Shield_Deku": "Deku Shield",
    "Item_Range_SlingShot": "Fairy Slingshot", "Item_BombBag_Small": "Bomb Bag", "Item_Boomerang": "Boomerang",
    "Item_GlassTruth": "Lens of Truth", "Item_Hammer": "Megaton Hammer", "Item_Range_Bow": "Fairy Bow",
    "Item_Hookshot": "Hookshot", "Item_Longshot": "Longshot", "Item_HeavyBoot": "Iron Boots",
    "Item_HoverBoot": "Hover Boots", "Item_Gauntlet_Silver": "Silver Gauntlets",
    "Item_Gauntlet_Gold": "Golden Gauntlets", "Item_Shield_Mirror": "Mirror Shield", "Shop_Armor_Goron": "Goron Tunic",
    "Shop_Armor_Zora": "Zora Tunic", "Item_Gauntlet_Goron": "Goron's Bracelet", "Item_DinFire": "Din's Fire",
    "Item_FaroreWind": "Farore's Wind", "Item_NayruLove": "Nayru's Love", "Obj_Heart_Piece": "Piece of Heart",
    "Obj_Heart_Container": "Heart Container", "Item_Arrow_Ice": "Ice Arrows", "Item_Arrow_Fire": "Fire Arrows",
    "Item_Arrow_Light": "Light Arrows", "Item_Dungeon_Map": "Dungeon Map", "Item_Dungeon_Compass": "Compass",
    "Item_Dungeon_SmallKey": "Small Key", "Item_Dungeon_BossKey": "Boss Key", "Obj_Token_Gold": "Gold Skulltula Token",
    "Obj_Rando_Rupoor": "Rupoor (trap)", "Enemy_Keese_Ice": "Ice Keese (trap)", "Enemy_Keese_Fire": "Fire Keese (trap)",
    "Enemy_Keese": "Keese (trap)",
    "Item_FairyBless_MP": "Magic Meter", "Item_FairyBless_MPDouble": "Double Magic",
    "Item_FairyBless_DefenseDouble": "Double Defense", "Item_ZeldaLetter": "Zelda's Letter",
    "Item_Sword_Biggoron": "Biggoron's Sword", "Item_Mask_Truth": "Mask of Truth", "Item_AgonyStone": "Stone of Agony",
    "Item_Bottle_Milk": "Bottle of Lon Lon Milk", "Item_Scale_Silver": "Silver Scale",
    "Item_Scale_Gold": "Golden Scale", "Item_Ocarina_Fairy": "Fairy Ocarina", "Item_Token_Gerudo": "Gerudo Card",
}


def item_name(item):
    if item is None or item == "None":
        return "Nothing"
    if item in ITEM_NAMES:
        return ITEM_NAMES[item]
    if item.startswith(("Rando_SmallKey_", "Rando_BossKey_")):
        import keys
        return keys.name(item)
    base = re.sub(r"^(Item_|Obj_|TBox_|Shop_|Enemy_|Pouch_)", "", item)
    base = re.sub(r"_(0\d|Small|Medium|Large)$", lambda m: "" if m.group(1).isdigit() else f" ({m.group(1)})", base)
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", base.replace("_", " ")).strip()


def _landmarks(root):
    out = []
    for a in root.get("Actors", []):
        g = a.get("Gyaml", "")
        dyn = a.get("Dynamic") or {}
        label = None
        if g == "MapIconEntranceAnchor" and dyn.get("Location"):
            label = f"the way to {area_name(dyn['Location'])}"
        elif g == "MapIconFacilityAnchor":
            label = FACILITIES.get(dyn.get("MapIconAnchorType", 0))
        elif g.startswith("Npc_"):
            label = next((v for k, v in PEOPLE.items() if k in g), None)
        if label:
            out.append((label, a["Translate"]))
    return out


def build(game, locations):
    by_area = {}
    for path in game.glob("Banc/*/*.bcett.byml.zs"):
        area = path.split("/")[1]
        root, _, _ = byml.loads(game.read(path))
        by_area.setdefault(area, []).extend(_landmarks(root))
    centers = {}
    for l in locations:
        if l.get("pos"):
            centers.setdefault(l["area"], []).append(l["pos"])
    places = {}
    for l in locations:
        pos = l.get("pos")
        if not pos:
            continue
        info = {}
        marks = by_area.get(l["area"], [])
        if marks:
            label, mpos = min(marks, key=lambda m: math.dist(m[1], pos))
            if math.dist(mpos, pos) <= NEAR:
                info["near"] = label
        pts = centers[l["area"]]
        cx = sum(p[0] for p in pts) / len(pts)
        cz = sum(p[2] for p in pts) / len(pts)
        dx, dz = pos[0] - cx, pos[2] - cz
        if math.hypot(dx, dz) > 25:
            ns = "north" if dz < -0.4 * abs(dx) else "south" if dz > 0.4 * abs(dx) else ""
            ew = "east" if dx > 0.4 * abs(dz) else "west" if dx < -0.4 * abs(dz) else ""
            info["side"] = ns + ew
        places[str(l["hash"])] = info
    CACHE.write_text(json.dumps(places))
    marks = {}
    for area, items in by_area.items():
        seen = {}
        for label, p in items:
            seen.setdefault((label, round(p[0] / 5), round(p[2] / 5)), [label, round(p[0], 1), round(p[2], 1)])
        marks[area] = list(seen.values())
    LANDMARKS.write_text(json.dumps(marks))
    return places


def landmarks(game, locations):
    if not LANDMARKS.exists():
        build(game, locations)
    return json.loads(LANDMARKS.read_text())


SPOT = {
    "chest": "in a chest", "floor": "lying on the ground", "rupee": "on the ground where a rupee was",
    "breakable": "inside a {thing}", "shop": "for sale in a shop", "skulltula": "on a Gold Skulltula",
    "scrub": "sold by a Business Scrub", "heart": "on the ground where a heart was", "rock": "under a gold {thing}",
}
THINGS = {"Obj_Pot": "pot", "Obj_BrokenBox": "crate", "Obj_LiftRock": "liftable rock", "Obj_BrokenRock": "cracked rock",
          "Beehive": "beehive", "Grass": "patch of grass"}


def describe(d, places, floor_item=False):
    if d["kind"] == "npc":
        return f"{area_name(d['area'])}: reward from {d['npc']['name']}"
    parts = [area_name(d["area"])]
    if d.get("room") is not None:
        parts[0] += f", room {d['room']}"
    info = places.get(str(d.get("hash")), {})
    where = SPOT[d["kind"]]
    if d["kind"] in ("breakable", "rock"):
        where = where.format(thing=next((v for k, v in THINGS.items() if k in d.get("actor", "")), "breakable object"))
    if floor_item:
        where = {"floor": "lying on the ground", "heart": "lying on the ground where a heart was"}.get(
            d["kind"], "lying on the ground where a rupee was")
    bits = [where]
    if info.get("near"):
        bits.append(f"near {info['near']}")
    if info.get("side"):
        bits.append(f"on the {info['side']} side")
    ages = sorted({v.split("_")[0] for v in d.get("variants", []) if v.split("_")[0] in ("Child", "Adult")})
    if len(ages) == 1:
        bits.append(f"as {ages[0].lower()}")
    return f"{parts[0]}: " + ", ".join(bits)
