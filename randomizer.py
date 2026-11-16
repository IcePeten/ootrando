import argparse
import collections
import copy
import io
import json
import math
import random
import re
import types
from dataclasses import dataclass, field

import evfl
import hints
import mmh3

import byml
import cosmetics
import models
import keys
import logic
import logo
import maps
import pickups
import sarc
import places
import songs
import starting
from msbt import Msbt
from game import ROOT, Game
from mod import ModBuilder
from npcs import NPC_GIFTS

FAILURES = collections.Counter()
FLAGGED = set(json.loads((ROOT / "data" / "isget.json").read_text()))
NO_PICKUP = ("Item_Wallet_", "Item_StickBag_", "Item_NutBag_", "Item_BulletBag_", "Item_Quiver_")
REPEATABLE = ("Item_Bottle", "Item_Bomb", "Item_Deku", "Item_Arrow_Normal", "Item_Dungeon_", "Item_Token_")
TRACKED = {i for i in FLAGGED if i.startswith("Item_") and not i.startswith(REPEATABLE)} | \
          {i for i in FLAGGED if i.startswith("Item_BombBag_")}
ADULT_SHOP_ITEMS = ("Shop_Armor_",)
FLOOR_JUNK = [("Obj_Rupee_Green", 30), ("Obj_Rupee_Blue", 25), ("Obj_Rupee_Red", 14), ("Obj_Rupee_Purple", 6),
              ("Obj_Rupee_Gold", 2), ("Obj_Heart", 12), ("Obj_MagicJar_Small", 6), ("Obj_ArrowBundle_Small", 5)]
CHEST_JUNK = ["TBox_Rupee_Green", "TBox_Rupee_Blue", "TBox_Rupee_Red", "TBox_Rupee_Purple"]
JUNK_SMALL = {name for name, _ in FLOOR_JUNK}
POUCH_JUNK = ["Obj_Rupee_Blue", "Obj_Rupee_Red", "Obj_Rupee_Purple"]
TRAPS = ["Enemy_Keese_Ice", "Enemy_Keese_Fire", "Enemy_Keese", "Enemy_ReDead", "Enemy_LikeLike", "Enemy_Bubble_Blue",
         "Enemy_Bubble_Red", "Enemy_Freezard", "Enemy_Biri", "Enemy_Wallmaster", "Enemy_Tektite_Red", pickups.RUPOOR]
FLOOR_KINDS = ("rupee", "floor", "heart")
TRAP_RATES = {"off": 0.0, "some": 0.06, "lots": 0.18}
FAKE_RATE = 0.5
GOLD_POT = "Obj_Pot_A_02"
MAP_PARAM = "Banc/BancBasedResource/MapParam.byml.zs"
MAP_CHECK_ICON = 23
LOCATION_MSBT = "LocationMsg/Location.msbt"
BOOL_EXP_PUSH = 0
BOOL_EXP_OR = 4
BOOL_EXP_NOT = 5
MAP_SPOT_RADIUS = 5.0
MAP_SPOT_HEIGHT = 4.0
GAMEDATA = "GameData/GameDataList.Product.110.byml.zs"
MIDO_BLOCKER = "KokiriForest_Npc_Kokiri_Mido_Child_Blocker"
EXIT_BLOCKER = "KokiriForest_Npc_Kokiri_007_Child_Blocker_00"
DOOR_OF_TIME = "Market_Child_TimeTempleDoor_Opened"
BOSS_KEY = "Item_Dungeon_BossKey"
KAKARIKO_GATE = "Npc_Hylia_Soldier_009_Child_OpenTheGate"
KEY_DUNGEONS = ["ForestTemple", "FireTemple", "WaterTemple", "ShadowTemple", "SpiritTemple", "BottomOfTheWell",
                "IceCavern", "GerudoTrainingGround", "InsideGanonCastle", "InsideTheDekuTree", "DodongoCavern",
                "InsideJabuJabuBelly", "GerudoFortress"]
BOSS_DUNGEONS = ["ForestTemple", "FireTemple", "WaterTemple", "ShadowTemple", "SpiritTemple"]
KEYSY_COUNT = 30
CHEST_SIZES = {"small": "Obj_TBox_A_01", "big": "Obj_TBox_A_02"}
CARPENTERS = ["013", "014", "015", "016"]
MASKS = ["Keaton", "Skull", "Spooky", "Bunny", "Truth", "Goron", "Zora", "Gerudo"]
TRIALS = ["Forest", "Fire", "Water", "Shadow", "Spirit", "Light"]
STORY_ENUMS = {"water": 1539965606, "scarecrow": 2490511403, "door_of_time": 931730378}
FOREST_MODES = {
    "open": {"open": ("OpenDeku", "OpenExit"), "flags": (MIDO_BLOCKER, EXIT_BLOCKER)},
    "closed_deku": {"open": ("OpenExit",), "flags": (EXIT_BLOCKER,)},
    "closed": {"open": (), "flags": ()},
}
ITEM_GET_EVENT = re.compile(r"(^|_)Get_?[A-Z]")
INTRO_SETTINGS = ["Event/EventSetting/EventSettingComponentList/Dm_Kokiri_0000.engine__event__EventSettingComponentList.bgyml"]
PLAIN_POTS = {"Obj_Pot_A_02": "Obj_Pot_A_01", "Obj_Pot_A_02_Respawn": "Obj_Pot_A_05_Respawn"}
GOLD_TINT = (3.0, 2.3, 0.4)
DUNGEON_ITEMS = {"Item_Dungeon_Map", "Item_Dungeon_Compass"}
TEXT_ARCHIVES = ["Mals/USen.Product.110.sarc.zs", "Mals/EUen.Product.110.sarc.zs"]
TEXT_EDITS = {
    "LayoutMsg/Title_00.msbt": {
        "0000": "New Randomizer Game",
        "0001": "Continue Randomizer",
    },
    "ActorMsg/PouchContent.msbt": {
        "Item_Dungeon_Map_GetMessage": "You found the map for this dungeon!",
        "Item_Dungeon_Compass_GetMessage": "You found the compass for this dungeon!",
        "Item_Dungeon_SmallKey_GetMessage": "You found a small key for this dungeon!",
        "Item_Dungeon_BossKey_GetMessage": "You found the boss key for this dungeon!",
    },
}
NAMES = {
    "KokiriSword": "Kokiri Sword", "DekuShield": "Deku Shield", "Slingshot": "Fairy Slingshot",
    "BombBag": "Bomb Bag", "Boomerang": "Boomerang", "Lens": "Lens of Truth", "Hammer": "Megaton Hammer",
    "Bow": "Fairy Bow", "Hookshot": "Hookshot", "Longshot": "Longshot", "IronBoots": "Iron Boots",
    "HoverBoots": "Hover Boots", "SilverGauntlets": "Silver Gauntlets", "GoldGauntlets": "Golden Gauntlets",
    "MirrorShield": "Mirror Shield", "GoronTunic": "Goron Tunic", "ZoraTunic": "Zora Tunic",
    "GoronBracelet": "Goron's Bracelet", "FairyOcarina": "Fairy Ocarina", "GerudoCard": "Gerudo Membership Card",
}

@dataclass
class Settings:
    seed: int = 0
    shuffle_chests: bool = True
    shuffle_floor: bool = True
    shuffle_shops: bool = True
    shuffle_maps_compasses: bool = True
    cutscene_chests: bool = True
    shuffle_npcs: bool = True
    shuffle_rupees: bool = True
    shuffle_hearts: bool = True
    shuffle_pots: bool = True
    shuffle_crates: bool = True
    shuffle_beehives: bool = True
    shuffle_grass: bool = True
    shuffle_rocks: bool = True
    color_breakables: bool = True
    small_anything: bool = True
    map_markers: bool = True
    open_forest: str = "open"
    skip_intro: bool = True
    hints: str = "balanced"
    tokens: str = "off"
    scrubs: bool = False
    starting_items: list = field(default_factory=list)
    skip_zelda: bool = False
    skip_area_intros: bool = True
    door_of_time: str = "closed"
    kakariko_gate: str = "closed"
    zora_fountain: str = "closed"
    gerudo_fortress: str = "vanilla"
    bridge: str = "vanilla"
    trials: int = 6
    ganon_boss_key: str = "vanilla"
    small_keys: str = "vanilla"
    boss_keys: str = "vanilla"
    free_scarecrow: bool = False
    chest_size: str = "match"
    shuffle_ocarinas: bool = False
    shuffle_gerudo_card: bool = False
    shuffle_frogs: bool = False
    shuffle_minigames: bool = False
    shuffle_sidequests: bool = False
    shuffle_skulltula_rewards: bool = False
    shuffle_great_fairies: bool = False
    shuffle_story_gifts: bool = False
    shuffle_trade_rewards: bool = False
    item_pool: str = "balanced"
    mask_quest: bool = False
    shuffle_songs: bool = False
    traps: str = "some"
    logic: str = "relaxed"
    mod_name: str = "OoT Randomizer"
    cosmetics: dict = field(default_factory=dict)

    def start_state(self):
        state = set(FOREST_MODES.get(self.open_forest, FOREST_MODES["closed"])["open"]) | starting.collect(self)[2]
        if self.door_of_time == "open":
            state.add("OpenDoorOfTime")
        if self.kakariko_gate == "open":
            state.add("OpenKakarikoGate")
        if self.zora_fountain == "open":
            state.add("OpenFountain")
        if self.gerudo_fortress == "open":
            state.add("OpenFortress")
        return state


@dataclass
class Location:
    data: dict
    rule: object
    accepts: str
    fixed: bool = False
    item: str = None

    @property
    def floor_item(self):
        return self.data["kind"] in FLOOR_KINDS and self.item is not None and self.item.startswith("Item_")

    @property
    def name(self):
        return places.describe(self.data, PLACES(), self.floor_item)


@dataclass
class Result:
    settings: Settings
    locations: list
    spheres: list = field(default_factory=list)
    cosmetics: dict = field(default_factory=dict)
    hints: list = field(default_factory=list)
    songs: dict = field(default_factory=dict)


def load_locations():
    return json.loads((ROOT / "data" / "locations.json").read_text())


_places = None


def PLACES():
    global _places
    if _places is None:
        cache = places.CACHE
        _places = json.loads(cache.read_text()) if cache.exists() else places.build(Game(), load_locations())
    return _places


def enabled(settings, d):
    kind = d["kind"]
    if kind == "chest":
        if not settings.shuffle_chests:
            return False
        if d["event"] and not settings.cutscene_chests and d["item"] not in ("TBox_Rupee_Blue", "TBox_Rupee_Green"):
            return False
        if d["item"] in ("Item_Dungeon_Map", "Item_Dungeon_Compass") and not settings.shuffle_maps_compasses:
            return False
        return True
    if kind == "skulltula":
        dungeon = d["area"] in logic.DUNGEONS
        return settings.tokens == "all" or settings.tokens == ("dungeons" if dungeon else "overworld")
    if kind in BREAK_KINDS:
        return getattr(settings, breakable_setting(d["actor"]))
    return {"floor": settings.shuffle_floor, "shop": settings.shuffle_shops, "rupee": settings.shuffle_rupees,
            "npc": settings.shuffle_npcs, "scrub": settings.scrubs, "heart": settings.shuffle_hearts}[kind]


BREAKABLE_SETTINGS = {"Obj_Pot_": "shuffle_pots", "Obj_BrokenBox_": "shuffle_crates",
                      "Obj_Kokiri_Beehive_": "shuffle_beehives", "Obj_Plant_Grass_": "shuffle_grass"}


def breakable_setting(actor):
    return next((s for prefix, s in BREAKABLE_SETTINGS.items() if actor.startswith(prefix)), "shuffle_rocks")


TOKEN = "Obj_Token_Gold"
TOKEN_MODES = ("off", "dungeons", "overworld", "all")
ACCEPTS = {"chest": "chest", "floor": "floor", "rupee": "floor", "breakable": "floor", "shop": "shop",
           "skulltula": "floor", "scrub": "scrub", "heart": "floor", "rock": "floor"}
BREAK_KINDS = ("breakable", "rock")
SCRUB_FALLBACK = "Item_StickBag_Medium"


def key_spots(settings):
    return keys.spots(settings, load_locations(), enabled)


def build_locations(settings):
    out = []
    key_hashes = {d["hash"] for d in key_spots(settings)}
    for d in load_locations():
        if not logic.is_shuffled(d, d["hash"] in key_hashes):
            continue
        if d["kind"] == "floor" and d["actor"] != "Obj_Heart_Piece":
            continue
        accepts = ACCEPTS[d["kind"]]
        if accepts == "floor" and settings.small_anything and d["kind"] in FLOOR_KINDS + BREAK_KINDS:
            accepts = "floor_any"
        loc = Location(d, logic.location_rule(d, settings.logic), accepts)
        if not enabled(settings, d):
            if d["item"] not in logic.PROGRESSION:
                continue
            loc.fixed, loc.item = True, d["item"]
        out.append(loc)
    for npc in NPC_GIFTS:
        d = {"kind": "npc", "area": npc["area"], "item": npc["item"], "npc": npc, "variants": [], "room": None}
        loc = Location(d, logic.rule("true" if settings.logic == "none" else npc["rule"]), npc["accepts"])
        optional = npc.get("setting")
        locked = npc["id"] == "GerudoCard" and settings.gerudo_fortress == "open"
        if not settings.shuffle_npcs or (optional and not getattr(settings, optional)) or locked:
            loc.fixed, loc.item = True, npc["item"]
        out.append(loc)
    return out


def compatible(loc, item):
    if keys.is_key(item):
        return keys.fits(loc, item, lambda event: not event or bool(ITEM_GET_EVENT.search(event)))
    if loc.accepts == "shop":
        if item.startswith(ADULT_SHOP_ITEMS) and not any("Adult" in v for v in loc.data["variants"]):
            return False
        return item.startswith("Shop_")
    if item.startswith("Shop_"):
        return False
    if item in DUNGEON_ITEMS:
        return False
    if item == TOKEN and loc.data["kind"] == "npc":
        return False
    if loc.accepts == "scrub":
        return item.startswith("Item_") and not item.startswith("Item_Dungeon_") or item == "Obj_Heart_Piece"
    if loc.accepts == "pouch":
        return (item.startswith("Item_") and not item.startswith("Item_Dungeon_")) or item in POUCH_JUNK \
            or item == "Obj_Heart_Piece"
    if loc.accepts == "floor":
        if loc.data.get("actor") == pickups.LIFT_ROCK and item == pickups.HEART_PIECE:
            return False
        return item.startswith("Obj_")
    if loc.accepts == "floor_any":
        if item.startswith(NO_PICKUP):
            return False
        if loc.data.get("actor") == pickups.LIFT_ROCK and pickups.is_pickup(item) and item not in TRACKED:
            return False
        return item.startswith(("Obj_", "Item_")) and not item.startswith("Item_Dungeon_")
    if loc.accepts == "flagged":
        return item in FLAGGED and item != "Obj_Heart_Piece" and not item.startswith(("Obj_", "TBox_"))
    return not item.startswith("Obj_") or item == "Obj_Heart_Piece"


def collect(locations, start_items):
    """Collects every reachable placed item, returning the final state and the spheres."""
    state = logic.expand(start_items)
    taken = set()
    spheres = []
    while True:
        sphere = [l for l in locations if id(l) not in taken and l.item and l.rule(state)]
        if not sphere:
            return state, spheres
        for l in sphere:
            taken.add(id(l))
        found = [l for l in sphere if l.item in logic.PROGRESSION]
        spheres.append(found)
        state = logic.expand(state | {logic.PROGRESSION[l.item] for l in found})


BOW = "Item_Range_Bow"
MAGIC_ARROWS = ("Item_Arrow_Fire", "Item_Arrow_Ice", "Item_Arrow_Light")


def sphere_of(locations, start_items):
    state = logic.expand(start_items)
    order = {}
    depth = 0
    while True:
        sphere = [l for l in locations if id(l) not in order and l.item and l.rule(state)]
        if not sphere:
            return order
        for l in sphere:
            order[id(l)] = depth
        depth += 1
        state = logic.expand(state | {logic.PROGRESSION[l.item] for l in sphere if l.item in logic.PROGRESSION})


def arrows_after_bow(rng, locations, start):
    order = sphere_of(locations, start)
    bows = [order[id(l)] for l in locations if l.item == BOW and id(l) in order]
    if not bows:
        return True
    bow = min(bows)
    for loc in [l for l in locations if l.item in MAGIC_ARROWS and order.get(id(l), bow + 1) <= bow]:
        later = [l for l in locations if order.get(id(l), -1) > bow and not l.fixed
                 and l.item not in logic.PROGRESSION and l.item not in MAGIC_ARROWS
                 and compatible(l, loc.item) and compatible(loc, l.item)]
        if not later:
            FAILURES["magic arrows before bow"] += 1
            return False
        other = rng.choice(later)
        loc.item, other.item = other.item, loc.item
    return True


def generate(settings, attempts=200):
    rng = random.Random(settings.seed)
    key_items = keys.pool(key_spots(settings))
    for item in key_items:
        logic.PROGRESSION[item] = keys.token(item)
    small_keys, boss_keys = keys.rules(key_items)
    for _ in range(attempts):
        song_map = songs.shuffle(rng) if settings.shuffle_songs else {}
        logic.configure(songs.event_rules(song_map), settings.bridge, settings.trials, small_keys, boss_keys)
        locations = build_locations(settings)
        place_dungeon_items(rng, locations)
        pool = [l.data["item"] for l in locations if not l.fixed and l.data["item"] not in DUNGEON_ITEMS
                and l.data["item"] not in (None, "None", keys.SMALL_KEY, keys.BOSS_KEY)]
        pool = adjust_pool(rng, pool, settings.item_pool) + key_items
        rng.shuffle(pool)
        start = settings.start_state()
        if fill(rng, locations, pool, settings.traps, start):
            if settings.logic != "none" and not arrows_after_bow(rng, locations, start):
                continue
            if settings.boss_keys == "dungeon":
                shuffle_boss_keys(rng, locations, settings)
            state, spheres = collect(locations, start)
            if settings.logic == "none" or "Ganon" in state:
                return Result(settings, locations, spheres, songs=song_map)
            FAILURES["not beatable"] += 1
    raise RuntimeError(f"could not build a beatable seed with these settings: {dict(FAILURES)}")


def adjust_pool(rng, pool, mode):
    pool = list(pool)
    if mode == "plentiful":
        extras = sorted({i for i in pool if i in logic.PROGRESSION and not i.startswith("Shop_")})
        junk = [n for n, i in enumerate(pool) if i in CHEST_JUNK]
        rng.shuffle(junk)
        for item, n in zip(extras, junk):
            pool[n] = item
    elif mode == "scarce":
        hearts = [n for n, i in enumerate(pool) if i == "Obj_Heart_Piece"]
        for n in rng.sample(hearts, len(hearts) // 2):
            pool[n] = rng.choice(CHEST_JUNK)
    return pool


def shuffle_boss_keys(rng, locations, settings):
    for d in load_locations():
        if d["item"] != BOSS_KEY or d["kind"] != "chest" or d["area"] == "InsideGanonCastle":
            continue
        room_rule = logic.ROOM_RULES.get((d["area"], d["room"]))
        options = [l for l in locations if not l.fixed and l.data["kind"] == "chest" and l.data["area"] == d["area"]
                   and logic.ROOM_RULES.get((d["area"], l.data["room"])) == room_rule]
        if not options:
            continue
        other = rng.choice(options)
        home = Location(d, logic.location_rule(d, settings.logic), "chest", item=other.item)
        other.item = BOSS_KEY
        locations.append(home)


def place_dungeon_items(rng, locations):
    for loc in [l for l in locations if not l.fixed and l.data["item"] in DUNGEON_ITEMS]:
        home = [l for l in locations if l.item is None and not l.fixed and l.data["kind"] == "chest"
                and l.data["area"] == loc.data["area"]]
        rng.choice(home).item = loc.data["item"]


def place_randomly(rng, locations, item):
    options = [l for l in locations if l.item is None and compatible(l, item)]
    if not options:
        return False
    rng.choice(options).item = item
    return True


def fill(rng, locations, pool, trap_setting="off", start=frozenset()):
    counts = collections.Counter(pool)
    progression, seen = [], set()
    for item in pool:
        key = logic.PROGRESSION.get(item)
        if key and key not in seen:
            seen.add(key)
            progression.append(item)
    rest = list(pool)
    for item in progression:
        rest.remove(item)
    uniques = [i for i in rest if counts[i] == 1 and i in FLAGGED and not i.startswith(("Obj_", "TBox_"))]
    for item in uniques:
        rest.remove(item)
    hearts = [i for i in rest if i in ("Obj_Heart_Piece", TOKEN)]
    rest = [i for i in rest if i not in ("Obj_Heart_Piece", TOKEN)]

    remaining = list(progression)
    while remaining:
        item = remaining.pop()
        state, _ = collect(locations, set(start) | {logic.PROGRESSION[i] for i in remaining})
        options = [l for l in locations if l.item is None and compatible(l, item) and l.rule(state)]
        if not options:
            FAILURES[item] += 1
            return False
        flagged = [l for l in options if l.accepts == "flagged"]
        rng.choice(flagged if flagged and rng.random() < 0.15 else options).item = item

    for slot in [l for l in locations if l.item is None and l.accepts == "flagged"]:
        pick = next((i for i in uniques if compatible(slot, i)), None)
        if pick is None:
            FAILURES["empty great fairy"] += 1
            return False
        uniques.remove(pick)
        slot.item = pick
    for item in uniques:
        if not place_randomly(rng, locations, item):
            return False
    for item in hearts:
        if not place_randomly(rng, locations, item):
            return False

    chest_junk = [i for i in rest if not i.startswith(("Obj_", "Shop_"))]
    shop_junk = [i for i in rest if i.startswith("Shop_")]
    shop_junk.sort(key=lambda it: not it.startswith(ADULT_SHOP_ITEMS))
    for item in shop_junk:
        if not place_randomly(rng, locations, item):
            FAILURES["shop"] += 1
            return False
    rng.shuffle(chest_junk)
    for slot in [l for l in locations if l.item is None and l.accepts == "scrub"]:
        pick = next((i for i in chest_junk if compatible(slot, i)), None)
        if pick:
            chest_junk.remove(pick)
        slot.item = pick or SCRUB_FALLBACK
    floor_names, floor_weights = zip(*FLOOR_JUNK)
    trap_rate = TRAP_RATES.get(trap_setting, 0.0)
    for slot in [l for l in locations if l.item is None]:
        if slot.accepts in ("floor", "floor_any"):
            if rng.random() < trap_rate:
                slot.item = rng.choice(TRAPS)
            else:
                slot.item = rng.choices(floor_names, floor_weights)[0]
        elif slot.accepts == "chest":
            slot.item = chest_junk.pop() if chest_junk else rng.choice(CHEST_JUNK)
        elif slot.accepts == "pouch":
            slot.item = rng.choice(POUCH_JUNK)
        else:
            FAILURES[f"unfilled {slot.accepts}"] += 1
            return False
    return True


def is_special(loc, seed):
    if loc.item in JUNK_SMALL:
        return False
    if loc.item in TRAPS:
        return random.Random(f"{seed}-{loc.data['hash']}").random() < FAKE_RATE
    return True


def _set_param(params, key, value):
    current = params.data[key]
    if hasattr(current, "v"):
        current.v = value
    else:
        params.data[key] = value


def set_flag_defaults(builder, flags, section="Bool"):
    entries = builder.placement(GAMEDATA)["Data"][section]
    wanted = {mmh3.hash(name, signed=False): value for name, value in flags.items()}
    for entry in entries:
        value = wanted.get(int(entry.get("Hash", -1)))
        if value is not None:
            entry["DefaultValue"] = value


def chest_model(gyaml, item, mode):
    base, bake = (gyaml[:-len("_NoBake")], "_NoBake") if gyaml.endswith("_NoBake") else (gyaml, "")
    if mode == "vanilla" or base not in CHEST_SIZES.values():
        return gyaml
    key = keys.parse(item)
    big = mode == "match" and (item in logic.PROGRESSION or item == BOSS_KEY) and not (key and key[0])
    return CHEST_SIZES["big" if big else "small"] + bake


def set_enum_defaults(builder, steps):
    for entry in builder.placement(GAMEDATA)["Data"]["Enum"]:
        step = steps.get(int(entry.get("Hash", -1)))
        if step is not None and step in entry["RawValues"]:
            entry["DefaultValue"] = entry["Values"][entry["RawValues"].index(step)]


def cleared_trials(settings):
    order = list(TRIALS)
    random.Random(f"trials-{settings.seed}").shuffle(order)
    return order[:6 - max(0, min(6, int(settings.trials)))]


AREA_INTROS = ["Dm_DeathMtCrater_0000", "Dm_DeathMtTrail_0000", "Dm_Deku_0000", "Dm_DesertColossus_0000",
               "Dm_DodongoCave_0000", "Dm_ForestTemple_0000", "Dm_GanonCastle_0000", "Dm_GerudoValley_0000",
               "Dm_Gerudo_0000", "Dm_Goron_0000", "Dm_Graveyard_0000", "Dm_HrlCastle_0000", "Dm_HrlCastle_0005",
               "Dm_HrlField_0000", "Dm_InsideGanonCastle_0003", "Dm_InsideJabu_Jabu_0000", "Dm_Kakariko_0000",
               "Dm_Kokiri_0045", "Dm_LakeHrl_0000", "Dm_LakeHrl_0003", "Dm_LakeHrl_0005", "Dm_LonLon_0010",
               "Dm_TimeTemple_0000", "Dm_TimeTemple_0065", "Dm_ZoraFountain_0000", "Dm_Zora_0000"]


def world_flags(settings):
    bools, ints, enums = {}, {}, {}
    if settings.skip_area_intros:
        for name in AREA_INTROS:
            bools[f"HavePlayedEvent.{name}"] = True
    if settings.door_of_time == "open":
        bools[DOOR_OF_TIME] = True
        enums[STORY_ENUMS["door_of_time"]] = "Step06"
    if settings.kakariko_gate == "open":
        bools[KAKARIKO_GATE] = True
    if settings.zora_fountain == "open":
        enums[STORY_ENUMS["water"]] = "Step07"
    freed = {"fast": 3, "open": 4}.get(settings.gerudo_fortress, 0)
    for n in CARPENTERS[:freed]:
        bools[f"GerudoFortress_IsAfterHelpCarpenter_Npc_Hylia_{n}_Adult"] = True
    if freed:
        ints["GerudoFortress_Meet_FourCarpenter_NumOfCarpenterFound"] = freed
        ints["GerudoFortress_Meet_FourCarpenter_NumOfCarpenterHelped"] = freed
    if settings.gerudo_fortress == "open":
        bools["IsGet.Item_Token_Gerudo"] = True
        ints["PouchData.Item_Token_Gerudo.StockNum"] = 1
    if settings.bridge == "open":
        bools["HavePlayedEvent.GanonCastle_Adult_Field_Rainbow"] = True
    cleared = cleared_trials(settings)
    for trial in cleared:
        bools[f"InsideGanonCastle_Dungeon_BarrierRemove_{trial}"] = True
        bools[f"HavePlayedEvent.InsideGanonCastle_Dungeon_BarrierRemove_{trial}"] = True
    if cleared:
        ints["InsideGanonCastle_Dungeon_Barrier_Count"] = 6 - len(cleared)
    if len(cleared) == 6:
        bools["InsideGanonCastle_IsAllBarrierClear"] = True
        bools["HavePlayedEvent.InsideGanonCastle_Dungeon_BarrierRemove_All"] = True
    if settings.ganon_boss_key == "start":
        bools["DungeonInfo.InsideGanonCastle.IsGetBossKey"] = True
    if settings.boss_keys == "start":
        for d in BOSS_DUNGEONS:
            bools[f"DungeonInfo.{d}.IsGetBossKey"] = True
    if settings.small_keys == "keysy":
        for d in KEY_DUNGEONS:
            ints[f"DungeonInfo.{d}.SmallKeyNum"] = KEYSY_COUNT
    for d, n in keys.bonus(key_spots(settings)).items():
        ints[f"DungeonInfo.{d}.SmallKeyNum"] = n
    if settings.mask_quest:
        for mask in MASKS:
            bools[f"HappyMaskShop_HasMask_{mask}"] = True
    if settings.free_scarecrow:
        enums[STORY_ENUMS["scarecrow"]] = "Complete"
        bools["IsGet.Item_Melody_ScarecrowSong"] = True
    return bools, ints, enums


def skip_intro(game, builder, settings):
    for path in INTRO_SETTINGS:
        root, version, endian = byml.loads(game.read(path))
        root["Components"].pop("SkipSetting", None)
        builder.put(path, byml.dumps(root, version, endian))


TIME_DOOR = "Obj_TimeTemple_Door_A_01"
TIME_DOOR_BANCS = ["Banc/Market/Market_Child_Static.bcett.byml.zs", "Banc/Market/Market_Adult_Static.bcett.byml.zs"]


def open_time_door(builder):
    for path in TIME_DOOR_BANCS:
        for actor in builder.placement(path)["Actors"]:
            if actor.get("Gyaml") == TIME_DOOR:
                actor["Presence"] = {"FlagName": DOOR_OF_TIME, "IsCheckLazy": False, "IsNegation": True}

def _marked(loc, seed):
    return True


def _map_key(params, path):
    stem = path.rsplit("/", 1)[-1].split(".")[0]
    parts = stem.split("_")
    for n in range(len(parts), 0, -1):
        key = "_".join(parts[:n])
        if key in params:
            return key
    return None


def _location_label(key):
    for suffix in ("_Alternative", "_Child", "_Adult"):
        key = key.removesuffix(suffix)
    return key


def _map_floor(area, y):
    if "Floor" not in area:
        return area
    floors = sorted(area["Floor"], key=lambda f: f.get("TransY", 0.0))
    below = [f for f in floors if f.get("TransY", 0.0) <= y + 1.0]
    return below[-1] if below else floors[0]


def add_map_icons(builder, icons, hidden_marks):
    params = builder.placement(MAP_PARAM)
    flags = set()
    seen = set()
    totals = collections.defaultdict(set)
    spots = collections.defaultdict(lambda: [None, []])
    spot_flags = set()
    spot_links = {}
    exps = {}
    for path, actor, loc in icons:
        key = _map_key(params, path)
        if key is None or (key, loc.data["hash"]) in seen:
            continue
        hash_ = int(actor["Hash"])
        own = hidden_marks.get(hash_)
        kind = "chest" if own else "item"
        if not own:
            if loc.item not in TRACKED:
                continue
            own = _got_flag(loc.item)
            flags.add(own)
        seen.add((key, loc.data["hash"]))
        totals[_location_label(key)].add(loc.data["hash"])
        floor = _map_floor(params[key], actor["Translate"][1])
        spot = spots[(id(floor), kind)]
        spot[0] = floor
        spot[1].append(([float(v) for v in actor["Translate"]], own))
    for (_, kind), (floor, checks) in spots.items():
        for group in _cluster(checks):
            owns = [o for _, o in group]
            rng = random.Random(f"map-spot-{kind}-{owns[0]}-{group[0][0]}")
            if kind == "chest":
                flag = owns[0] if len(owns) == 1 else f"Rando_MapSpot_{owns[0].rsplit('_', 1)[1]}"
                spot_flags.add(flag)
                for o in owns:
                    spot_links[o] = ([x for x in owns if x != o], flag)
            else:
                flag = f"Rando_MapItems_{rng.getrandbits(48):012x}"
                values = []
                for n, o in enumerate(dict.fromkeys(owns)):
                    values += [[BOOL_EXP_PUSH, mmh3.hash(o, signed=False)], [BOOL_EXP_NOT]]
                    if n:
                        values.append([BOOL_EXP_OR])
                exps[flag] = values
            center = [sum(t[i] for t, _ in group) / len(group) for i in range(3)]
            floor.setdefault("Facility", []).append({
                "GameDataHashName": flag, "HeartPieceHash0": byml.U64(0), "HeartPieceHash1": byml.U64(0),
                "IconType": MAP_CHECK_ICON, "InstanceID": byml.U64(rng.getrandbits(64)), "Trans": center})
    return flags, {label: len(hashes) for label, hashes in totals.items()}, spot_flags, spot_links, exps


def add_bool_exps(builder, exps):
    entries = builder.placement(GAMEDATA)["Data"]["BoolExp"]
    known = {int(e["Hash"]) for e in entries}
    kind = type(entries[0]["Hash"])
    for name, values in sorted(exps.items()):
        h = mmh3.hash(name, signed=False)
        if h in known:
            continue
        entries.append({"Hash": kind(h), "ResetTypeValue": 0, "SaveFileIndex": -1,
                        "Values": [[byml.U64(x) for x in v] for v in values]})
        known.add(h)


def _cluster(checks):
    groups = []
    for check in checks:
        trans = check[0]
        for group in groups:
            seed = group[0][0]
            if abs(seed[0] - trans[0]) <= MAP_SPOT_RADIUS and abs(seed[2] - trans[2]) <= MAP_SPOT_RADIUS \
                    and abs(seed[1] - trans[1]) <= MAP_SPOT_HEIGHT:
                group.append(check)
                break
        else:
            groups.append([check])
    return groups


def check_count_names(game, totals):
    archive = sarc.Sarc(game.read(TEXT_ARCHIVES[0]))
    m = Msbt(bytes(archive.get_file(LOCATION_MSBT).data))
    names = {}
    for label, count in totals.items():
        if label in m.labels:
            names[label] = f"{m.plain(m.text(label))} ({count})"
    return names


def _got_flag(item):
    return f"IsGet.{item}"


def _got(item, negate):
    return {"FlagName": _got_flag(item), "IsCheckLazy": False, "IsNegation": negate}


def add_flags(builder, names, default=False):
    entries = builder.placement(GAMEDATA)["Data"]["Bool"]
    known = {int(e["Hash"]) for e in entries}
    kind = type(entries[0]["Hash"])
    for name in sorted(names):
        h = mmh3.hash(name, signed=False)
        if h not in known:
            entries.append({"DefaultValue": default, "Hash": kind(h), "ResetTypeValue": 8, "SaveFileIndex": 0})
            known.add(h)


def _plain_rock(rock, item):
    plain = copy.deepcopy(rock)
    rng = random.Random(f"plain-{rock['Hash']}")
    h = rng.getrandbits(64)
    plain["Hash"] = byml.U64(h)
    plain["SRTHash"] = byml.U32(rng.getrandbits(32))
    if "Phive" in plain:
        plain["Phive"] = {"Placement": {"ID": byml.U64(h)}}
    plain.pop("Links", None)
    plain["Presence"] = dict(_got(item, False), IsCheckLazy=True)
    return plain


def apply(game, result):
    return build_mod(game, result).write()


def build_mod(game, result, progress=None):
    step = progress or (lambda text: None)
    settings = result.settings
    builder = ModBuilder(game, settings.mod_name)
    step("Placing items in the world")
    changed = [l for l in result.locations if not l.fixed and l.data["kind"] != "npc"]
    by_hash = {int(h): l for l in changed for h in l.data.get("hashes", [l.data["hash"]])}
    areas = {l.data["area"] for l in changed}
    gilded = set()
    map_icons = []
    swapped = []
    got_flags = set()
    floor_items = set()
    key_events = set()
    mark_events = set()
    wrapped_events = set()
    hidden_marks = {}
    displays = set()
    vanilla = {d["item"] for d in load_locations() if d["kind"] == "chest"}

    def shown(item):
        if item.startswith("Item_Ocarina_") and item not in vanilla and pickups.needs_display(game, item):
            displays.add(item)
            return pickups.chest_name(item)
        return item

    def mark_chest(actor, dyn):
        hash_ = int(actor["Hash"])
        original = dyn.get("GetEventName")
        if original and keys.can_wrap(game, original):
            mark = keys.wrapped_event(hash_, original)
            wrapped_events.add(mark)
        else:
            mark = keys.mark_event(hash_, actor["Gyaml"])
            if not mark:
                return False
            mark_events.add(mark)
        dyn["GetEventName"] = mark
        hidden_marks[hash_] = keys.mark_flag(hash_)
        return True

    for path in game.glob("Banc/*/*.bcett.byml.zs"):
        if path.split("/")[1] not in areas:
            continue
        root = builder.placement(path)
        for actor in root.get("Actors", []):
            loc = by_hash.get(int(actor.get("Hash", 0)))
            if not loc:
                continue
            dyn = actor.setdefault("Dynamic", {})
            kind = loc.data["kind"]
            if kind == "chest":
                actor["Gyaml"] = chest_model(actor.get("Gyaml", ""), loc.item, settings.chest_size)
                drop, key_event = (keys.chest(loc.item, loc.data["area"], actor["Gyaml"]) if keys.is_key(loc.item)
                                   else (shown(loc.item), None))
                if dyn.get("Drop__DropActor") != drop and ITEM_GET_EVENT.search(dyn.get("GetEventName", "")):
                    dyn.pop("GetEventName")
                dyn["Drop__DropActor"] = drop
                if key_event:
                    if settings.map_markers:
                        key_event = keys.marked_key_event(key_event, int(actor["Hash"]))
                        hidden_marks[int(actor["Hash"])] = keys.mark_flag(int(actor["Hash"]))
                    dyn["GetEventName"] = key_event
                    key_events.add(key_event)
                elif settings.map_markers:
                    mark_chest(actor, dyn)
                dyn.pop("Drop__CheckActor", None)
                dyn.pop("Drop__DropActor_Substitute", None)
            elif kind == "skulltula":
                if loc.item == pickups.HEART_PIECE:
                    dyn["Drop__DropActor"] = pickups.floor_name(loc.item)
                    floor_items.add(loc.item)
                else:
                    dyn["Drop__DropActor"] = loc.item
            elif kind == "scrub":
                dyn["ScrubBusiness_ShopItemActorName0"] = loc.item
            elif kind in BREAK_KINDS:
                if actor.get("Gyaml") == pickups.LIFT_ROCK and loc.item in TRACKED and "Presence" not in actor:
                    swapped.append(_plain_rock(actor, loc.item))
                    actor["Gyaml"] = pickups.RESPAWN_ROCK
                    actor["Presence"] = _got(loc.item, True)
                    got_flags.add(_got_flag(loc.item))
                if pickups.is_pickup(loc.item):
                    dyn["Drop__DropActor"] = pickups.floor_name(loc.item)
                    floor_items.add(loc.item)
                else:
                    dyn["Drop__DropActor"] = loc.item
                dyn.pop("Drop__DropTable", None)
                if settings.color_breakables and is_special(loc, settings.seed):
                    gyaml = actor.get("Gyaml", "")
                    if gyaml.startswith("Obj_Pot_A") and "_Dream" not in gyaml:
                        actor["Gyaml"] = GOLD_POT + ("_Respawn" if gyaml.endswith("_Respawn") else "")
                        gilded.add(int(actor["Hash"]))
                    else:
                        for i, v in enumerate(GOLD_TINT):
                            dyn[f"GameModelController_GeneralInstanceParam{i}"] = v
            elif loc.floor_item:
                rx, ry, _ = actor.get("Rotate", [0.0, 0.0, 0.0])
                actor["Gyaml"] = pickups.floor_name(loc.item)
                actor["Rotate"] = [0.0, float(math.pi - ry if abs(rx) > 3.0 else ry), 0.0]
                actor.pop("Dynamic", None)
                floor_items.add(loc.item)
            else:
                actor["Gyaml"] = loc.item
            if settings.map_markers and _marked(loc, settings.seed):
                map_icons.append((path, actor, loc))
        if swapped:
            root["Actors"].extend(swapped)
            swapped = []

    if settings.map_markers:
        every = {int(h): l for l in result.locations if l.data.get("hash")
                 for h in l.data.get("hashes", [l.data["hash"]])}
        for path in game.glob("Banc/*/*.bcett.byml.zs"):
            if not any(c.encode() in game.read(path) for c in keys.CHESTS):
                continue
            for actor in builder.placement(path).get("Actors", []):
                hash_ = int(actor.get("Hash", 0))
                if hash_ in by_hash or actor.get("Gyaml", "").removesuffix("_NoBake") not in keys.CHESTS:
                    continue
                if actor.get("Dynamic", {}).get("GetEventName", "").startswith(keys.MARK):
                    continue
                if not mark_chest(actor, actor.setdefault("Dynamic", {})):
                    continue
                loc = every.get(hash_) or types.SimpleNamespace(
                    data={"hash": hash_, "kind": "chest"}, item=None)
                map_icons.append((path, actor, loc))

    check_totals = {}
    spot_links = {}
    if map_icons:
        icon_flags, check_totals, spot_flags, spot_links, exps = add_map_icons(builder, map_icons, hidden_marks)
        got_flags |= icon_flags
        add_flags(builder, [*hidden_marks.values(), *spot_flags], default=True)
        add_bool_exps(builder, exps)
    if got_flags:
        pickups.respawn_rock(game, builder)
        add_flags(builder, got_flags)
    pickups.build(game, builder, floor_items)
    pickups.chest_displays(game, builder, displays)
    keys.build(game, builder, key_events | mark_events, spot_links)
    if any(l.item == pickups.RUPOOR for l in changed):
        pickups.rupoor(game, builder)

    forest = FOREST_MODES.get(settings.open_forest, FOREST_MODES["closed"])
    if forest["flags"]:
        set_flag_defaults(builder, {flag: False for flag in forest["flags"]})
    if settings.door_of_time == "open":
        open_time_door(builder)
    world_bools, world_ints, world_enums = world_flags(settings)
    set_flag_defaults(builder, world_bools)
    set_flag_defaults(builder, world_ints, "Int")
    set_enum_defaults(builder, world_enums)
    for path, data in songs.build(game, result.songs).items():
        builder.put(path, data)
    start_ints, start_bools = starting.save_defaults(settings)
    if start_ints:
        set_flag_defaults(builder, start_ints, "Int")
    if start_bools:
        set_flag_defaults(builder, start_bools)
    if settings.skip_intro:
        skip_intro(game, builder, settings)

    if settings.color_breakables:
        for path in game.glob("Banc/*/*.bcett.byml.zs"):
            if b"Obj_Pot_A_02" not in game.read(path):
                continue
            for actor in builder.placement(path).get("Actors", []):
                if actor.get("Gyaml") in PLAIN_POTS and int(actor.get("Hash", 0)) not in gilded:
                    actor["Gyaml"] = PLAIN_POTS[actor["Gyaml"]]
        for path, data in cosmetics.gold_pots(game).items():
            builder.put(path, data)

    step("Rewriting NPC gifts, hints and text")
    flows = {}
    for loc in result.locations:
        if loc.data["kind"] != "npc" or loc.fixed or loc.item == loc.data["item"]:
            continue
        npc = loc.data["npc"]
        path = f"Event/EventFlow/{npc['flow']}.bfevfl.zs"
        if path not in flows:
            f = evfl.EventFlow()
            f.read(builder.current(path))
            flows[path] = f
        events = {ev.name: ev for ev in flows[path].flowchart.events}
        for name, fields in npc["events"].items():
            for key in fields:
                _set_param(events[name].data.params, key, loc.item)
        if npc.get("flag_event"):
            _set_param(events[npc["flag_event"]].data.params, "GameDataName", f"IsGet.{loc.item}")
    for path, f in flows.items():
        out = io.BytesIO()
        f.write(out)
        builder.put(path, out.getvalue())
    keys.wrap(game, builder, wrapped_events, spot_links)
    stone_texts, result.hints = hints.build(result, game, settings.hints, collect)
    edits = copy.deepcopy(TEXT_EDITS)
    if settings.small_keys == "anywhere" or settings.boss_keys == "anywhere":
        edits["ActorMsg/PouchContent.msbt"].update(keys.GENERIC_TEXT)
    if check_totals:
        edits.setdefault(LOCATION_MSBT, {}).update(check_count_names(game, check_totals))
    for path in TEXT_ARCHIVES:
        builder.put(path, edit_text(game.read(path), {hints.MSBT: stone_texts}, keys.messages(key_events), edits))
    step("Recoloring Link's outfit")
    files, result.cosmetics = cosmetics.build(game, settings.cosmetics, random.Random(settings.seed))
    for path, data in files.items():
        builder.put(path, data)
    result.cosmetics.update(models.build(game, builder, settings.cosmetics, random.Random(f"{settings.seed}-models")))
    step("Adding Randomizer to the title logo")
    for path, (data, size) in logo.build(game).items():
        builder.put_compressed(path, data, size)
    return builder


def edit_text(data, voiced=None, added=None, plain=None):
    archive = sarc.Sarc(data)
    writer = sarc.SarcWriter.from_sarc(archive)
    plain = plain or TEXT_EDITS
    for name in sorted(set(plain) | set(added or {})):
        m = Msbt(bytes(archive.get_file(name).data))
        for label, text in plain.get(name, {}).items():
            m.set_text(label, m.encode(text))
        for label, text in (added or {}).get(name, {}).items():
            m.add_text(label, m.encode(text))
        writer.files[name] = m.dumps()
    for name, edits in (voiced or {}).items():
        if not edits:
            continue
        m = Msbt(bytes(archive.get_file(name).data))
        for label, text in edits.items():
            if label in m.labels:
                m.set_text(label, m.leading_tags(m.text(label)) + m.encode(text))
        writer.files[name] = m.dumps()
    return bytes(writer.write()[1])


def spoiler(result):
    lines = [f"OoT Randomizer seed {result.settings.seed}", ""]
    start = [starting.ITEMS[k]["label"] for k in result.settings.starting_items if k in starting.ITEMS]
    if result.settings.skip_zelda:
        start += ["Zelda's Letter", "Zelda's Lullaby"]
    if start:
        lines += ["Starting with: " + ", ".join(start), ""]
    s = result.settings
    remaining = [t for t in TRIALS if t not in cleared_trials(s)]
    lines += ["World:",
              f"  Door of Time: {s.door_of_time}, Kakariko gate: {s.kakariko_gate}, Zora's Fountain: {s.zora_fountain}",
              f"  Gerudo Fortress: {s.gerudo_fortress}, Rainbow Bridge: {s.bridge}",
              f"  Ganon's trials still to do: {', '.join(remaining) if remaining else 'none'}",
              f"  Small keys: {s.small_keys}, boss keys: {s.boss_keys}, Ganon's boss key: {s.ganon_boss_key}", ""]
    if result.songs:
        lines.append("Songs:")
        for spot, song in result.songs.items():
            lines.append(f"  {songs.SPOTS[spot]['where']} teaches {songs.SONG_NAMES[song]}")
        lines.append("")
    lines.append("Playthrough (each round only needs items from earlier rounds):")
    for n, sphere in enumerate(result.spheres, 1):
        for l in sphere:
            lines.append(f"  Round {n}: {NAMES.get(logic.PROGRESSION[l.item], places.item_name(l.item))} at {l.name}")
    lines.append("")
    lines.append("Heart Pieces:")
    for l in sorted(result.locations, key=lambda l: l.name):
        if l.item == "Obj_Heart_Piece":
            lines.append(f"  {l.name}")
    lines.append("")
    if result.hints:
        lines.append("Gossip Stone hints:")
        for area, name, hint in result.hints:
            lines.append(f"  {area}, {name.replace('GOSSIP_', '').replace('_', ' ').title()}: {hint}")
        lines.append("")
    if result.cosmetics:
        lines.append("Cosmetics:")
        for label, color in result.cosmetics.items():
            lines.append(f"  {label}: {color}")
        lines.append("")
    lines.append("All locations:")
    for l in sorted(result.locations, key=lambda l: l.name):
        trap = " (trap)" if l.item in TRAPS else ""
        lines.append(f"  {l.name} -> {places.item_name(l.item)}{trap}{' (unchanged)' if l.fixed else ''}")
    return "\n".join(lines)


def tracker(result, game):
    seed = result.settings.seed
    major = {id(l) for sphere in result.spheres for l in sphere}
    areas = {}
    for i, l in enumerate(result.locations):
        pos = l.data.get("pos")
        if not pos:
            continue
        kind = l.data["kind"]
        important = kind in ("chest", "floor", "npc", "shop") or l.floor_item or \
            (kind in BREAK_KINDS and is_special(l, seed))
        ages = sorted({v.split("_")[0] for v in l.data.get("variants", []) if v.split("_")[0] in ("Child", "Adult")})
        area = areas.setdefault(l.data["area"], {"name": places.area_name(l.data["area"]), "checks": []})
        area["checks"].append({
            "id": f"{l.data.get('hash', l.data['kind'])}-{i}", "x": round(pos[0], 1), "z": round(pos[2], 1),
            "kind": "floor" if l.floor_item else kind, "where": l.name, "item": places.item_name(l.item),
            "trap": l.item in TRAPS, "major": id(l) in major, "important": important, "ages": ages,
        })
    marks = places.landmarks(game, load_locations())
    images = maps.export(game)
    for key, area in areas.items():
        area["landmarks"] = marks.get(key, [])
        area["maps"] = images.get(key, {})
    return {"seed": seed, "areas": dict(sorted(areas.items(), key=lambda kv: kv[1]["name"]))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-cutscene-chests", action="store_true")
    p.add_argument("--no-shops", action="store_true")
    p.add_argument("--no-npcs", action="store_true")
    p.add_argument("--logic", choices=sorted(logic.LOGIC_LEVELS), default="relaxed")
    a = p.parse_args()
    s = Settings(seed=a.seed if a.seed is not None else random.randrange(10**9),
                 cutscene_chests=not a.no_cutscene_chests, shuffle_shops=not a.no_shops,
                 shuffle_npcs=not a.no_npcs, logic=a.logic)
    result = generate(s)
    text = spoiler(result)
    out = ROOT / "spoilers"
    out.mkdir(exist_ok=True)
    (out / f"spoiler_{s.seed}.txt").write_text(text)
    print("\n".join(text.splitlines()[:45]))
    if not a.dry_run:
        print("mod written to", apply(Game(), result))


if __name__ == "__main__":
    main()
