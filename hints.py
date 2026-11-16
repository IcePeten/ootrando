import random
import textwrap

import byml
import logic
import places

MSBT = "EventFlowMsg/GossipStone.msbt"
LINE = 62
LEVELS = {
    "balanced": {"unique": 20, "hero": 5, "foolish": 3, "exact": False},
    "strong": {"unique": 20, "hero": 6, "foolish": 2, "exact": True},
    "very_strong": {"unique": 40, "hero": 6, "foolish": 4, "exact": True},
}
SKIP_AREAS = {"DreamWorld"}


def stones(game):
    out = {}
    for path in game.glob("Banc/*/*.bcett.byml.zs"):
        data = game.read(path)
        if b"GossipStone" not in data:
            continue
        for actor in byml.loads(data)[0].get("Actors", []):
            name = actor.get("Name")
            if "GossipStone" in actor.get("Gyaml", "") and name:
                out.setdefault(name, path.split("/")[1])
    return dict(sorted(out.items()))


def _required(locations, start, collect):
    required = []
    for sphere_loc in [l for l in locations if l.item in logic.PROGRESSION]:
        item = sphere_loc.item
        sphere_loc.item = None
        state, _ = collect(locations, start)
        sphere_loc.item = item
        if "Ganon" not in state:
            required.append(sphere_loc)
    return required


def _wrap(text):
    return "\n".join(textwrap.wrap(text, LINE))


def _item(l):
    name = places.item_name(l.item)
    return name if "'s " in name else f"the {name}"


def _is(l):
    return "are" if places.item_name(l.item).endswith(("Gauntlets", "Boots", "Arrows")) else "is"


THE = ("Graveyard", "Lost Woods", "Sacred Forest Meadow", "Haunted Wasteland", "Ice Cavern", "Bottom of the Well",
       "Gerudo Training Ground", "Forest Temple", "Fire Temple", "Water Temple", "Shadow Temple", "Spirit Temple")


def _place(name):
    if name.startswith("Inside "):
        return name[len("Inside "):]
    return f"the {name}" if name.startswith(THE) else name


def _area(area):
    return _place(places.area_name(area))


def _spot(l):
    area, _, detail = l.name.partition(": ")
    return f"in {_place(area)}, {detail}" if detail else f"in {_place(area)}"


def build(result, game, level, collect):
    spec = LEVELS.get(level)
    if not spec:
        return {}, []
    rng = random.Random(f"hints-{result.settings.seed}")
    locations = result.locations
    start = result.settings.start_state()
    required = _required(locations, start, collect)
    hero_areas = sorted({l.data["area"] for l in required})
    rng.shuffle(hero_areas)

    progress_areas = {l.data["area"] for l in locations if l.item in logic.PROGRESSION}
    all_areas = sorted({l.data["area"] for l in locations
                        if l.data["area"] not in SKIP_AREAS and (l.data["area"] in logic.AREAS or l.data["area"] in logic.DUNGEONS)})
    foolish = [a for a in all_areas if a not in progress_areas]
    rng.shuffle(foolish)

    hints = []
    for area in hero_areas[:spec["hero"]]:
        hints.append(f"They say that {_area(area)} is on the way of the hero.")
    for area in foolish[:spec["foolish"]]:
        hints.append(f"They say that plundering {_area(area)} is a foolish choice.")

    named = [l for l in locations if l.item in logic.PROGRESSION and not l.item.startswith("Rando_SmallKey_")]
    named.sort(key=lambda l: (l not in required, rng.random()))
    seen = set()
    for l in named:
        if len(hints) >= spec["unique"]:
            break
        key = (l.item, l.data["area"])
        if key in seen:
            continue
        seen.add(key)
        if spec["exact"]:
            hints.append(f"They say that {_item(l)} can be found {_spot(l)}.")
        else:
            hints.append(f"They say that {_item(l)} {_is(l)} hidden in {_area(l.data['area'])}.")

    found = stones(game)
    names = list(found)
    rng.shuffle(names)
    if not hints:
        return {}, []
    pool = (hints * (len(names) // len(hints) + 1))[:len(names)]
    texts, table = {}, []
    for name, hint in zip(names, pool):
        texts[name] = _wrap(hint)
        table.append((places.area_name(found[name]), name, hint))
    return texts, sorted(table)
