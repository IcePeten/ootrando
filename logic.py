import re

PROGRESSION = {
    "Item_Sword_Kokiri": "KokiriSword",
    "TBox_Shield_Deku": "DekuShield",
    "Shop_Weapon_Shield_Deku": "DekuShield",
    "Item_Range_SlingShot": "Slingshot",
    "Item_BombBag_Small": "BombBag",
    "Item_Boomerang": "Boomerang",
    "Item_GlassTruth": "Lens",
    "Item_Hammer": "Hammer",
    "Item_Range_Bow": "Bow",
    "Item_Hookshot": "Hookshot",
    "Item_Longshot": "Longshot",
    "Item_HeavyBoot": "IronBoots",
    "Item_HoverBoot": "HoverBoots",
    "Item_Gauntlet_Silver": "SilverGauntlets",
    "Item_Gauntlet_Gold": "GoldGauntlets",
    "Item_Shield_Mirror": "MirrorShield",
    "Shop_Armor_Goron": "GoronTunic",
    "Shop_Armor_Zora": "ZoraTunic",
    "Item_Gauntlet_Goron": "GoronBracelet",
    "Item_Ocarina_Fairy": "FairyOcarina",
    "Item_Token_Gerudo": "GerudoCard",
    "Item_WeirdEgg": "WeirdEgg",
    "Item_ZeldaLetter": "ZeldasLetter",
    "Item_Arrow_Light": "LightArrows",
    "Item_FairyBless_MP": "Magic",
}

EVENTS = {
    "DekuTreeAccess": "OpenDeku | (KokiriSword & DekuShield)",
    "DekuTreeBeaten": "child & DekuTreeAccess & DekuShield",
    "Field": "OpenExit | DekuTreeBeaten",
    "Hookshot": "adult",
    "ZeldasLullaby": "child & Field & WeirdEgg",
    "SariasSong": "child & ZeldasLullaby & FairyOcarina",
    "EponasSong": "child & Field & FairyOcarina",
    "Bottle": "Field",
    "DodongosBeaten": "child & GateOpen & GoronBracelet & BombBag",
    "GateOpen": "ZeldasLetter | OpenKakarikoGate",
    "RutosLetter": "Bottle | OpenFountain",
    "SunsSong": "child & Field & ZeldasLullaby",
    "PreludeOfLight": "adult & ForestMedallion",
    "ZoraDomain": "ZeldasLullaby",
    "JabuBeaten": "child & ZoraDomain & RutosLetter & Bottle & Boomerang & Slingshot",
    "adult": "(OpenDoorOfTime & Field) | (DekuTreeBeaten & DodongosBeaten & JabuBeaten)",
    "SongOfTime": "adult",
    "SongOfStorms": "adult",
    "MinuetOfForest": "adult",
    "BoleroOfFire": "adult",
    "SerenadeOfWater": "adult & ZoraDomain",
    "GoronTunicNpc": "adult & BombBag",
    "ZoraTunicNpc": "adult & ZoraDomain & Bottle",
    "Tunic_Goron": "GoronTunic | GoronTunicNpc",
    "Tunic_Zora": "ZoraTunic | ZoraTunicNpc",
    "GerudoCard": "OpenFortress",
    "Wasteland": "GerudoCard & (HoverBoots | Longshot) & Lens",
    "RequiemOfSpirit": "Wasteland",
    "NocturneOfShadow": "ForestMedallion & FireMedallion & WaterMedallion",
}

DUNGEONS = {
    "ForestTemple": ("ForestMedallion", "adult & MinuetOfForest", ["Hookshot", "Bow"]),
    "FireTemple": ("FireMedallion", "adult & Tunic_Goron", ["BombBag", "Hookshot", "Hammer"]),
    "WaterTemple": ("WaterMedallion", "adult & Tunic_Zora & IronBoots & ZeldasLullaby",
                    ["Hookshot", "Longshot", "Bow"]),
    "ShadowTemple": ("ShadowMedallion", "NocturneOfShadow", ["Lens", "Hookshot", "HoverBoots", "BombBag"]),
    "SpiritTemple": ("SpiritMedallion", "RequiemOfSpirit",
                     ["Hookshot", "BombBag", "SilverGauntlets", "MirrorShield"]),
    "BottomOfTheWell": ("WellCleared", "SongOfStorms & ZeldasLullaby", ["Lens", "BombBag"]),
    "IceCavern": ("IceCavernCleared", "adult & ZoraDomain & Bottle", ["Hookshot"]),
    "GerudoTrainingGround": ("TrainingGroundCleared", "GerudoCard",
                             ["Hookshot", "Longshot", "Bow", "Lens", "Hammer", "IronBoots", "BombBag",
                              "SilverGauntlets", "HoverBoots"]),
    "InsideGanonCastle": ("Ganon", "ForestMedallion & FireMedallion & WaterMedallion & ShadowMedallion"
                                   " & SpiritMedallion & LightArrows",
                          ["Bow", "Lens", "Hookshot", "Longshot", "Hammer", "MirrorShield", "SilverGauntlets",
                           "GoldGauntlets", "HoverBoots", "BombBag"]),
}

for _event, _entry, _needs in DUNGEONS.values():
    EVENTS[_event] = " & ".join([f"({_entry})"] + _needs)

BASE_EVENTS = dict(EVENTS)
BRIDGE_RULES = {
    "vanilla": "adult & LightArrows",
    "open": "adult",
}
GANON_FIGHT = "adult & LightArrows & Bow & Magic"

GROTTO = "BombBag & Hammer & SongOfStorms & SilverGauntlets"

AREAS = {
    "KokiriForest": {"child": "true", "adult": "adult"},
    "LostWood": {"child": "SariasSong", "adult": "adult & SariasSong"},
    "SacredForestMeadow": {"child": "SariasSong & Slingshot", "adult": "adult & Hookshot"},
    "HyruleField": {"child": "Field", "adult": "adult"},
    "HyruleCastle": {"child": "Field", "adult": "adult"},
    "Market": {"child": "Field", "adult": "adult"},
    "KakarikoVillage": {"child": "Field", "adult": "adult"},
    "Graveyard": {"child": "Field & ZeldasLullaby", "adult": "adult & ZeldasLullaby & Hookshot"},
    "DeathMountainTrail": {"child": "GateOpen & BombBag", "adult": "adult & BombBag"},
    "GoronCity": {"child": "GateOpen & BombBag & GoronBracelet", "adult": "adult & BombBag & GoronBracelet"},
    "DeathMountainCrater": {"child": "GateOpen & BombBag & GoronBracelet",
                            "adult": "adult & BombBag & Tunic_Goron & Hookshot"},
    "ZoraRiver": {"child": "Field & BombBag", "adult": "adult & BombBag"},
    "ZoraDomain": {"child": "ZoraDomain", "adult": "adult & ZoraDomain"},
    "ZoraFountain": {"child": "ZoraDomain & RutosLetter", "adult": "adult & ZoraDomain & IronBoots & Tunic_Zora"},
    "LakeHylia": {"child": "Field", "adult": "adult & IronBoots & Hookshot"},
    "LonLonRanch": {"child": "Field", "adult": "adult & EponasSong"},
    "GerudoValley": {"child": "Field", "adult": "adult & (EponasSong | Longshot) & Hammer & SilverGauntlets"},
    "GerudoFortress": {"adult": "GerudoCard"},
    "HountedWasteland": {"adult": "Wasteland"},
    "DesertColossus": {"child": "RequiemOfSpirit", "adult": "Wasteland & RequiemOfSpirit"},
    "InsideTheDekuTree": {"child": "DekuTreeAccess"},
    "DodongoCavern": {"child": "GateOpen & GoronBracelet", "adult": "adult & BombBag"},
    "InsideJabuJabuBelly": {"child": "ZoraDomain & RutosLetter & Bottle"},
}

LOGIC_LEVELS = {
    "safe": "Safe: every spot assumes you have the full toolkit for its dungeon or grotto.",
    "relaxed": "Relaxed: a dungeon's own key item spot only needs what the original game needed to reach it.",
    "none": "No Logic: anything can be anywhere. The seed may not be beatable.",
}

ROOM_RULES = {
    ("InsideTheDekuTree", 3): "Slingshot",
    ("InsideTheDekuTree", 4): "Slingshot",
    ("InsideTheDekuTree", 10): "Slingshot",
    ("InsideJabuJabuBelly", 12): "Boomerang",
    ("InsideJabuJabuBelly", 13): "Boomerang",
    ("InsideJabuJabuBelly", 14): "Boomerang",
    ("InsideJabuJabuBelly", 15): "Boomerang & Slingshot",
    ("DodongoCavern", 22): "BombBag",
}

GROTTO_AREAS = {"KokiriForest", "LostWood", "SacredForestMeadow", "HyruleField", "KakarikoVillage",
                "Graveyard", "DeathMountainTrail", "DeathMountainCrater", "ZoraRiver", "GerudoValley",
                "LakeHylia", "LonLonRanch"}

EXCLUDED_EVENTS = ("MiniGame_",)
EXCLUDED_AREAS = {"DreamWorld"}
EXCLUDED_ITEMS = {"Item_Dungeon_SmallKey", "Item_Dungeon_BossKey", "Obj_MiniGame_SmallKey",
                  "Item_ScrubBusinessSeed", "Obj_Heart_Container"}
EXCLUDED_ACTORS = ("Obj_HrlCity_Shop_TBox", "Obj_Dungeon_SmallKey", "Shop_Mask_", "Obj_GerudoValley_Heart_Piece",
                   "Item_OrnamentalBottle_Milk")


class Rule:
    TOKEN = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*|[&|()])")

    def __init__(self, text):
        self.text = text
        self.tokens = self.TOKEN.findall(text)
        self.pos = 0
        self.fn = self._or()

    def _or(self):
        parts = [self._and()]
        while self.pos < len(self.tokens) and self.tokens[self.pos] == "|":
            self.pos += 1
            parts.append(self._and())
        return parts[0] if len(parts) == 1 else (lambda s, p=parts: any(f(s) for f in p))

    def _and(self):
        parts = [self._atom()]
        while self.pos < len(self.tokens) and self.tokens[self.pos] == "&":
            self.pos += 1
            parts.append(self._atom())
        return parts[0] if len(parts) == 1 else (lambda s, p=parts: all(f(s) for f in p))

    def _atom(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        if tok == "(":
            fn = self._or()
            self.pos += 1
            return fn
        if tok == "true":
            return lambda s: True
        if tok == "false":
            return lambda s: False
        if tok == "child":
            return lambda s: True
        return lambda s, t=tok: t in s

    def __call__(self, state):
        return self.fn(state)


_EVENT_RULES = {name: Rule(text) for name, text in EVENTS.items()}
_CACHE = {}
SMALL_KEYS = {}


def configure(overrides=None, bridge="vanilla", trials=6, small_keys=None, boss_keys=None):
    global _EVENT_RULES
    SMALL_KEYS.clear()
    SMALL_KEYS.update(small_keys or {})
    events = dict(BASE_EVENTS)
    for area, (event, _, _) in DUNGEONS.items():
        needs = SMALL_KEYS.get(area, []) + ([boss_keys[area]] if boss_keys and area in boss_keys else [])
        if needs and event in events:
            events[event] = " & ".join([f"({events[event]})"] + needs)
    events.update(overrides or {})
    _, _, needs = DUNGEONS["InsideGanonCastle"]
    tower = needs + SMALL_KEYS.get("InsideGanonCastle", []) if trials > 0 else ["Bow"]
    events["Ganon"] = " & ".join([f"({BRIDGE_RULES.get(bridge, BRIDGE_RULES['vanilla'])})",
                                  f"({GANON_FIGHT})"] + tower)
    EVENTS.clear()
    EVENTS.update(events)
    _EVENT_RULES = {name: Rule(text) for name, text in events.items()}


def rule(text):
    if text not in _CACHE:
        _CACHE[text] = Rule(text)
    return _CACHE[text]


def expand(items):
    """Adds every fixed event the items unlock, until nothing changes."""
    state = set(items)
    changed = True
    while changed:
        changed = False
        for name, r in _EVENT_RULES.items():
            if name not in state and r(state):
                state.add(name)
                changed = True
    return state


SKULLTULA_KILL = "(Boomerang | Hookshot)"
OBJECT_RULES = {
    "Obj_LiftRock_A_01": "adult | GoronBracelet",
    "Obj_BrokenRock_A_01": "BombBag | Hammer",
    "Obj_BrokenRock_A_02": "Hammer",
}


def location_rule(loc, level="safe"):
    if level == "none":
        return rule("true")
    base = _area_rule(loc, level)
    if loc["kind"] == "skulltula":
        return rule(f"({base}) & {SKULLTULA_KILL}")
    need = OBJECT_RULES.get(loc.get("actor")) if loc["kind"] in ("breakable", "rock") else None
    if need:
        return rule(f"({base}) & ({need})")
    return rule(base)


def _area_rule(loc, level):
    if loc["area"] in DUNGEONS:
        _, entry, needs = DUNGEONS[loc["area"]]
        if level == "relaxed":
            own = PROGRESSION.get(loc["item"])
            needs = [n for n in needs if n != own]
        text = " & ".join([f"({entry})"] + needs + SMALL_KEYS.get(loc["area"], []))
        extra = ROOM_RULES.get((loc["area"], loc["room"]))
        return f"({text}) & {extra}" if extra else text
    area = AREAS.get(loc["area"])
    if area is None:
        return "false"
    ages = []
    variants = " ".join(loc["variants"])
    has_child = "Child" in variants or not ("Adult" in variants)
    has_adult = "Adult" in variants or not ("Child" in variants)
    if has_child and "child" in area:
        ages.append(f"({area['child']})")
    if has_adult and "adult" in area:
        ages.append(f"(adult & {area['adult']})" if area["adult"] != "adult" else "adult")
    if not ages:
        return "false"
    text = " | ".join(ages)
    if loc["actor"].endswith("_NoBake") and loc["area"] in GROTTO_AREAS:
        text = f"({text}) & {GROTTO}"
    extra = ROOM_RULES.get((loc["area"], loc["room"]))
    if extra:
        text = f"({text}) & {extra}"
    return text


def is_shuffled(loc, keys=False):
    if loc["area"] in EXCLUDED_AREAS or (loc["item"] in EXCLUDED_ITEMS and not keys):
        return False
    if loc["actor"].startswith(EXCLUDED_ACTORS):
        return False
    if loc["event"] and loc["event"].startswith(EXCLUDED_EVENTS):
        return False
    return loc["area"] in AREAS or loc["area"] in DUNGEONS
