ITEMS = {
    "kokiri_sword": {"label": "Kokiri Sword", "pouch": {"Weapon_Sword_Kokiri": 1}, "logic": ["KokiriSword"]},
    "deku_shield": {"label": "Deku Shield", "pouch": {"Weapon_Shield_Deku": 1}, "logic": ["DekuShield"]},
    "ocarina": {"label": "Fairy Ocarina", "pouch": {"Item_Ocarina_Fairy": 1}, "logic": ["FairyOcarina"]},
    "sticks": {"label": "Deku Sticks", "pouch": {"Item_StickBag_Small": 1, "Item_DekuStick": 10}, "logic": []},
    "nuts": {"label": "Deku Nuts", "pouch": {"Item_NutBag_Small": 1, "Item_DekuNut": 20}, "logic": []},
    "slingshot": {"label": "Fairy Slingshot", "pouch": {"Weapon_Range_SlingShot": 1, "Item_BulletBag_Small": 1,
                                                        "Item_DekuSeed": 30}, "logic": ["Slingshot"]},
    "bombs": {"label": "Bomb Bag", "pouch": {"Item_BombBag_Small": 1, "Item_Bomb": 20}, "logic": ["BombBag"]},
    "boomerang": {"label": "Boomerang", "pouch": {"Item_Boomerang": 1}, "logic": ["Boomerang"]},
    "bow": {"label": "Fairy Bow", "pouch": {"Weapon_Range_Bow": 1, "Item_Quiver_Small": 1, "Item_Arrow_Normal": 30},
            "logic": ["Bow"]},
    "hookshot": {"label": "Hookshot", "pouch": {"Item_Hookshot": 1}, "logic": ["Hookshot"]},
    "hammer": {"label": "Megaton Hammer", "pouch": {"Item_Hammer": 1}, "logic": ["Hammer"]},
    "lens": {"label": "Lens of Truth", "pouch": {"Armor_GlassTruth": 1}, "logic": ["Lens"]},
    "bracelet": {"label": "Goron's Bracelet", "pouch": {"Armor_Child_Gauntlet_Goron": 1}, "logic": ["GoronBracelet"]},
    "iron_boots": {"label": "Iron Boots", "pouch": {"Armor_Adult_HeavyBoot": 1}, "logic": ["IronBoots"]},
    "hover_boots": {"label": "Hover Boots", "pouch": {"Armor_Adult_HoverBoot": 1}, "logic": ["HoverBoots"]},
    "goron_tunic": {"label": "Goron Tunic", "pouch": {"Armor_Adult_Goron": 1}, "logic": ["GoronTunic"]},
    "zora_tunic": {"label": "Zora Tunic", "pouch": {"Armor_Adult_Zora": 1}, "logic": ["ZoraTunic"]},
    "silver_scale": {"label": "Silver Scale", "pouch": {"Item_Scale_Silver": 1}, "logic": []},
    "wallet": {"label": "Adult's Wallet", "pouch": {"Item_Wallet_Medium": 1}, "logic": []},
}
SKIP_ZELDA = {"pouch": {"Item_ZeldaLetter": 1}, "songs": ["Item_Melody_ZeldaLullaby"],
              "logic": ["ZeldasLullaby", "ZeldasLetter"]}


def collect(settings):
    pouch, songs, tokens = {}, [], set()
    picks = [ITEMS[k] for k in settings.starting_items if k in ITEMS]
    if settings.skip_zelda:
        picks.append(SKIP_ZELDA)
    for pick in picks:
        for name, count in pick["pouch"].items():
            pouch[name] = max(pouch.get(name, 0), count)
        songs += pick.get("songs", [])
        tokens.update(pick["logic"])
    return pouch, songs, tokens


def save_defaults(settings):
    pouch, songs, _ = collect(settings)
    ints = {f"PouchData.{name}.StockNum": count for name, count in pouch.items()}
    bools = {f"IsGet.{name}": True for name in list(pouch) + songs}
    return ints, bools
