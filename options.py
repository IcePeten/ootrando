import random
import zlib
from dataclasses import asdict

import cosmetics
import hints
import logic
import models
import places
import randomizer
import starting


def random_seed():
    return random.randrange(10**9)


def defaults():
    s = asdict(randomizer.Settings(seed=random_seed()))
    s["levels"] = logic.LOGIC_LEVELS
    s["starting_choices"] = {k: v["label"] for k, v in starting.ITEMS.items()}
    s["cosmetic_slots"] = {k: {"label": v["label"], "default": v["default"], "palette": v["palette"],
                               "match": bool(v.get("match"))} for k, v in cosmetics.SLOTS.items()}
    s["model_slots"] = {k: {"label": v["label"], "default": v["default"], "choices": models.choices_for(k)}
                        for k, v in models.SLOTS.items()}
    s["forest_modes"] = list(randomizer.FOREST_MODES)
    return s


def forest_mode(value):
    if isinstance(value, bool):
        return "open" if value else "closed"
    return value if value in randomizer.FOREST_MODES else "open"


def pick(options, key, allowed):
    value = options.get(key, allowed[0])
    return value if value in allowed else allowed[0]


def parse_seed(text):
    text = str(text or "").strip()
    if text.isdigit():
        return int(text)
    if text:
        return zlib.crc32(text.lower().encode()) % 10**9
    return random_seed()


def settings_from(options):
    return randomizer.Settings(
        seed=parse_seed(options.get("seed", "")),
        shuffle_chests=bool(options.get("shuffle_chests", True)),
        shuffle_floor=bool(options.get("shuffle_floor", True)),
        shuffle_shops=bool(options.get("shuffle_shops", True)),
        shuffle_maps_compasses=bool(options.get("shuffle_maps_compasses", True)),
        cutscene_chests=bool(options.get("cutscene_chests", True)),
        shuffle_npcs=bool(options.get("shuffle_npcs", True)),
        shuffle_rupees=bool(options.get("shuffle_rupees", True)),
        shuffle_pots=bool(options.get("shuffle_pots", options.get("shuffle_breakables", True))),
        shuffle_crates=bool(options.get("shuffle_crates", options.get("shuffle_breakables", True))),
        shuffle_beehives=bool(options.get("shuffle_beehives", options.get("shuffle_breakables", True))),
        shuffle_grass=bool(options.get("shuffle_grass", options.get("shuffle_breakables", True))),
        shuffle_rocks=bool(options.get("shuffle_rocks", True)),
        color_breakables=bool(options.get("color_breakables", True)),
        small_anything=bool(options.get("small_anything", True)),
        map_markers=bool(options.get("map_markers", True)),
        open_forest=forest_mode(options.get("open_forest", "open")),
        skip_intro=bool(options.get("skip_intro", True)),
        hints=options.get("hints") if options.get("hints") in hints.LEVELS or options.get("hints") == "off"
        else "balanced",
        tokens=options.get("tokens") if options.get("tokens") in randomizer.TOKEN_MODES else "off",
        scrubs=bool(options.get("scrubs", False)),
        shuffle_hearts=bool(options.get("shuffle_hearts", True)),
        starting_items=[k for k in options.get("starting_items", []) if k in starting.ITEMS],
        skip_zelda=bool(options.get("skip_zelda", False)),
        skip_area_intros=bool(options.get("skip_area_intros", True)),
        door_of_time="open" if options.get("door_of_time") == "open" else "closed",
        kakariko_gate=pick(options, "kakariko_gate", ("closed", "open")),
        zora_fountain=pick(options, "zora_fountain", ("closed", "open")),
        gerudo_fortress=pick(options, "gerudo_fortress", ("vanilla", "fast", "open")),
        bridge=pick(options, "bridge", ("vanilla", "open")),
        trials=max(0, min(6, int(options.get("trials", 6)))),
        ganon_boss_key=pick(options, "ganon_boss_key", ("vanilla", "start")),
        small_keys=pick(options, "small_keys", ("vanilla", "keysy", "anywhere")),
        boss_keys=pick(options, "boss_keys", ("vanilla", "dungeon", "start", "anywhere")),
        free_scarecrow=bool(options.get("free_scarecrow", False)),
        chest_size=pick(options, "chest_size", ("match", "small", "vanilla")),
        shuffle_ocarinas=bool(options.get("shuffle_ocarinas", False)),
        shuffle_gerudo_card=bool(options.get("shuffle_gerudo_card", False)),
        shuffle_frogs=bool(options.get("shuffle_frogs", False)),
        shuffle_minigames=bool(options.get("shuffle_minigames", False)),
        shuffle_sidequests=bool(options.get("shuffle_sidequests", False)),
        shuffle_skulltula_rewards=bool(options.get("shuffle_skulltula_rewards", False)),
        shuffle_great_fairies=bool(options.get("shuffle_great_fairies", False)),
        shuffle_story_gifts=bool(options.get("shuffle_story_gifts", False)),
        shuffle_trade_rewards=bool(options.get("shuffle_trade_rewards", False)),
        item_pool=pick(options, "item_pool", ("balanced", "plentiful", "scarce")),
        mask_quest=bool(options.get("mask_quest", False)),
        shuffle_songs=bool(options.get("shuffle_songs", False)),
        traps=options.get("traps", "some") if options.get("traps") in randomizer.TRAP_RATES else "some",
        logic=options.get("logic", "relaxed"),
        cosmetics={k: v for k, v in (options.get("cosmetics") or {}).items()
                   if k in cosmetics.SLOTS or (k in models.SLOTS and v in models.CHOICES)},
    )


def summary(result):
    seed = result.settings.seed
    rounds = [[{"item": randomizer.NAMES.get(logic.PROGRESSION[l.item], places.item_name(l.item)), "where": l.name}
               for l in sphere] for sphere in result.spheres]
    moved = sum(1 for l in result.locations if l.item != l.data["item"])
    hidden = sum(1 for l in result.locations if l.data["kind"] in randomizer.BREAK_KINDS and not l.fixed
                 and randomizer.is_special(l, seed))
    traps = sum(1 for l in result.locations if l.item in randomizer.TRAPS)
    return {"ok": True, "seed": seed, "locations": len(result.locations), "moved": moved,
            "hidden": hidden if result.settings.color_breakables else 0, "traps": traps,
            "rounds": [r for r in rounds if r]}
