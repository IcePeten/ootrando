import json
import re
from pathlib import Path

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
    "Item_Arrow_Fire": "FireArrows",
    "Item_FairyBless_MP": "Magic",
    "Item_DinFire": "DinsFire",
    "Item_Scale_Silver": "SilverScale",
    "Item_Scale_Gold": "GoldScale",
    "Item_Bottle": "BottleItem",
    "Item_Bottle_Milk": "BottleItem",
    "Item_Bottle_Letter": "RutosLetter",
}

EVENTS = {
    "Ocarina": "FairyOcarina | StonesAtMoat",
    "StonesAtMoat": "C_Field & DekuTreeBeaten & DodongosBeaten & JabuBeaten",
    "adult": "C_Field & (OpenDoorOfTime | StonesAtMoat)",
    "Hookshot": "adult",
    "GateOpen": "ZeldasLetter | OpenKakarikoGate",
    "Dive": "SilverScale | GoldScale",
    "Bottle": "BottleItem | RutosLetter",
    "RutosLetter": "C_Field & Dive",
    "KingZoraMoved": "OpenFountain | (C_ZD & RutosLetter)",

    "ZeldasLullaby": "C_HC & WeirdEgg",
    "SariasSong": "C_SFM & ZeldasLetter",
    "EponasSong": "C_Field & ZeldasLetter & Ocarina",
    "SunsSong": "(C_Graveyard | A_Graveyard) & Lullaby",
    "SongOfTime": "StonesAtMoat",
    "SongOfStorms": "A_Kak & Ocarina",
    "MinuetOfForest": "A_LW & Saria",
    "BoleroOfFire": "A_DMCUpper | (A_GCDarunia & Tunic_Goron)",
    "SerenadeOfWater": "A_ZF & Bottle",
    "NocturneOfShadow": "A_Kak & ForestMedallion & FireMedallion & WaterMedallion",
    "RequiemOfSpirit": "A_Wasteland & LensUse",
    "PreludeOfLight": "adult & ForestMedallion",

    "Lullaby": "ZeldasLullaby & Ocarina",
    "Saria": "SariasSong & Ocarina",
    "Storms": "SongOfStorms & Ocarina",
    "Sun": "SunsSong & Ocarina",
    "Time": "SongOfTime & Ocarina",
    "Minuet": "MinuetOfForest & Ocarina",
    "Bolero": "BoleroOfFire & Ocarina",
    "Serenade": "SerenadeOfWater & Ocarina",
    "Nocturne": "NocturneOfShadow & Ocarina",
    "Requiem": "RequiemOfSpirit & Ocarina",
    "Prelude": "PreludeOfLight & Ocarina",
    "Epona": "adult & EponasSong & Ocarina",

    "Sticks": "KokiriSword | Slingshot | BombBag",
    "ChildWeapon": "KokiriSword | Sticks",
    "ChildAttack": "KokiriSword | Sticks | Slingshot | Boomerang | BombBag | DinsMagic",
    "DinsMagic": "DinsFire & Magic",
    "FireArrowsMagic": "adult & Bow & FireArrows & Magic",
    "ChildFire": "Sticks | DinsMagic",
    "AdultFire": "DinsMagic | FireArrowsMagic",
    "LensUse": "Lens & Magic",
    "GoronTunicNpc": "A_GC & (BombBag | Bow | GoronBracelet)",
    "ZoraTunicNpc": "A_ZF & Bottle",
    "Tunic_Goron": "GoronTunic | GoronTunicNpc",
    "Tunic_Zora": "ZoraTunic | ZoraTunicNpc",
    "GerudoCard": "OpenFortress",

    "C_Field": "OpenExit | DekuTreeBeaten",
    "C_LW": "true",
    "A_LW": "adult",
    "A_KF": "adult",
    "C_SFM": "C_LW & (Slingshot | Sticks | KokiriSword | DinsMagic)",
    "A_SFM": "(A_LW & Saria) | (adult & Minuet)",
    "C_Market": "C_Field",
    "C_HC": "C_Market",
    "C_Kak": "C_Field",
    "A_Kak": "adult",
    "C_Graveyard": "C_Kak",
    "A_Graveyard": "adult",
    "C_DMT": "C_Kak & GateOpen",
    "A_DMT": "adult",
    "C_DMTSummit": "C_DMT & BombBag",
    "A_DMTSummit": "A_DMT & (BombBag | Hammer)",
    "C_GC": "C_DMT",
    "A_GC": "A_DMT",
    "C_GCDarunia": "C_GC & Lullaby",
    "A_GCDarunia": "A_GC & (Lullaby | BombBag | Bow | GoronBracelet)",
    "C_DMCUpper": "C_DMTSummit",
    "A_DMCUpper": "A_DMTSummit",
    "C_DMCLower": "C_GCDarunia",
    "A_DMCLower": "A_GCDarunia | (adult & Bolero)",
    "A_DMCCentral": "Tunic_Goron & (A_DMCLower | A_DMCUpper)",
    "C_ZR": "(C_Field & BombBag) | (C_LW & Dive)",
    "A_ZR": "adult",
    "C_ZD": "C_ZR & Lullaby",
    "A_ZD": "A_ZR & Lullaby",
    "C_ZF": "C_ZD & KingZoraMoved",
    "A_ZF": "A_ZD & KingZoraMoved",
    "A_LH": "adult",
    "C_GV": "C_Field",
    "A_GV": "adult",
    "A_GF": "A_GV & (Epona | Longshot)",
    "A_Wasteland": "A_GF & GerudoCard & (HoverBoots | Longshot)",
    "C_Colossus": "Requiem",
    "A_Colossus": "(A_Wasteland & LensUse) | (adult & Requiem)",

    "DekuTreeAccess": "OpenDeku | (KokiriSword & DekuShield)",
    "DCChild": "C_DMT & (BombBag | GoronBracelet)",
    "DCAdult": "A_DMT & (BombBag | Hammer | GoronBracelet)",
    "SpiritChild": "C_Colossus & (Boomerang | Slingshot) & BombBag",
    "SpiritAdult": "A_Colossus & SilverGauntlets",
}

DUNGEONS = {
    "InsideTheDekuTree": ("DekuTreeBeaten", "DekuTreeAccess",
                          "ChildFire & Slingshot & DekuShield & ChildWeapon"),
    "DodongoCavern": ("DodongosBeaten", "DCChild | DCAdult",
                      "BombBag & ((DCChild & ChildWeapon) | DCAdult)"),
    "InsideJabuJabuBelly": ("JabuBeaten", "C_ZF & Bottle & (Slingshot | Boomerang | BombBag)",
                            "Boomerang & ChildWeapon"),
    "ForestTemple": ("ForestMedallion", "A_SFM", "GoronBracelet & Bow"),
    "FireTemple": ("FireMedallion", "A_DMCCentral & Tunic_Goron", "Hammer & BombBag"),
    "WaterTemple": ("WaterMedallion", "A_LH & IronBoots & Tunic_Zora & Lullaby", "Longshot & Bow & BombBag"),
    "ShadowTemple": ("ShadowMedallion", "adult & Nocturne & AdultFire & LensUse",
                     "HoverBoots & BombBag & Lullaby & (Bow | Longshot)"),
    "SpiritTemple": ("SpiritMedallion", "SpiritChild | SpiritAdult",
                     "SpiritChild & SpiritAdult & MirrorShield & Lullaby & Bow & BombBag"),
    "BottomOfTheWell": ("WellCleared", "C_Kak & Storms", "Lullaby & LensUse"),
    "IceCavern": ("IceCavernCleared", "A_ZF", "Bottle"),
    "GerudoTrainingGround": ("TrainingGroundCleared", "A_GF & GerudoCard",
                             "Bow & LensUse & Hammer & SilverGauntlets & IronBoots & Tunic_Zora & Time"),
    "InsideGanonCastle": ("Ganon", "GanonBridge", "GanonTower"),
}

ROOM_RULES = {
    ("InsideTheDekuTree", 2): "DekuShield",
    **{("InsideTheDekuTree", r): "ChildFire & Slingshot" for r in (5, 6, 7, 8, 9, 10, 11)},
    **{("DodongoCavern", r): "BombBag | GoronBracelet" for r in (3, 5, 10, 13, 16, 18, 20, 22)},
    **{("InsideJabuJabuBelly", r): "Boomerang" for r in (3, 5, 12, 13, 14, 15)},
    ("BottomOfTheWell", 1): "LensUse",
    ("BottomOfTheWell", 2): "ChildFire",
    ("BottomOfTheWell", 3): "ChildFire",
    ("BottomOfTheWell", 4): "LensUse & Boomerang",
    ("BottomOfTheWell", 5): "LensUse & Boomerang",
    ("BottomOfTheWell", 6): "Lullaby & LensUse",
    ("BottomOfTheWell", 7): "LensUse & Boomerang",
    ("BottomOfTheWell", 8): "Lullaby & KokiriSword",
    ("BottomOfTheWell", 9): "BombBag",
    ("BottomOfTheWell", 11): "LensUse",
    **{("IceCavern", r): "Bottle" for r in range(4, 16)},
    **{("ForestTemple", r): "Bow | Time" for r in (8, 12, 14, 15)},
    ("ForestTemple", 4): "GoronBracelet",
    ("ForestTemple", 17): "GoronBracelet",
    **{("ForestTemple", r): "GoronBracelet & Bow" for r in (16, 18, 22, 27, 29)},
    **{("FireTemple", r): "Hammer" for r in (3, 17, 18)},
    ("FireTemple", 19): "Time",
    **{("FireTemple", r): "BombBag" for r in (4, 5, 7, 8, 10, 13)},
    ("FireTemple", 11): "BombBag & Hammer",
    ("FireTemple", 16): "BombBag & Bow",
    ("WaterTemple", 4): "Bow",
    ("WaterTemple", 7): "Bow",
    ("WaterTemple", 15): "Longshot & BombBag",
    ("WaterTemple", 17): "BombBag",
    ("WaterTemple", 20): "GoronBracelet",
    ("WaterTemple", 21): "Longshot",
    ("WaterTemple", 23): "Longshot & Bow",
    ("WaterTemple", 24): "Time & Bow",
    ("WaterTemple", 25): "BombBag",
    **{("ShadowTemple", r): "HoverBoots" for r in (6, 7)},
    **{("ShadowTemple", r): "HoverBoots & BombBag" for r in (11, 13, 14, 15, 16, 17)},
    **{("ShadowTemple", r): "HoverBoots & BombBag & Lullaby" for r in (19, 20, 21, 31)},
    ("ShadowTemple", 24): "HoverBoots & BombBag & Lullaby & (Bow | Longshot)",
    **{("SpiritTemple", r): "SpiritChild" for r in (2, 4, 6)},
    **{("SpiritTemple", r): "SpiritAdult" for r in (15, 16, 26)},
    ("SpiritTemple", 14): "SpiritAdult & Lullaby",
    ("SpiritTemple", 18): "SpiritAdult & MirrorShield",
    ("SpiritTemple", 23): "SpiritAdult & LensUse",
    ("SpiritTemple", 29): "SpiritAdult & Lullaby & Bow",
    ("SpiritTemple", 31): "SpiritAdult & MirrorShield",
    ("SpiritTemple", 33): "SpiritAdult & MirrorShield & Lullaby & Bow & BombBag",
    ("GerudoTrainingGround", 0): "Bow",
    ("GerudoTrainingGround", 3): "BombBag",
    ("GerudoTrainingGround", 4): "LensUse",
    ("GerudoTrainingGround", 5): "HoverBoots | Longshot",
    ("GerudoTrainingGround", 7): "Hammer & Bow",
    ("GerudoTrainingGround", 9): "Time & IronBoots & Tunic_Zora",
    ("GerudoTrainingGround", 10): "SilverGauntlets & LensUse & Bow",
    ("InsideGanonCastle", 2): "AdultFire & Bow",
    ("InsideGanonCastle", 5): "Bottle & Hammer & Bow",
    ("InsideGanonCastle", 8): "LensUse & Hammer & Bow",
    **{("InsideGanonCastle", r): "LensUse" for r in (12, 13, 17)},
    ("InsideGanonCastle", 24): "GanonTower",
}

DUNGEON_CHECKS = {
    "InsideTheDekuTree:37568": "ChildAttack",
    "InsideTheDekuTree:90388": "ChildAttack",
    "InsideTheDekuTree:70603": "Slingshot | Boomerang | BombBag | DinsMagic",
    "InsideTheDekuTree:43983": "Boomerang",
    "InsideTheDekuTree:51747": "DekuShield & ChildWeapon",
    "DodongoCavern:66065": "(DCChild & BombBag) | (DCAdult & (BombBag | Hammer))",
    "DodongoCavern:75927": "(DCChild & ChildWeapon) | DCAdult",
    "DodongoCavern:48957": "DCAdult & Longshot",
    "DodongoCavern:84829": "(DCChild & ChildAttack) | DCAdult",
    "DodongoCavern:06011": "(DCChild & Boomerang) | DCAdult",
    "DodongoCavern:94851": "(DCChild & ChildAttack) | DCAdult",
    "DodongoCavern:43497": "(DCChild & BombBag & Boomerang) | (DCAdult & (BombBag | Hammer))",
    "DodongoCavern:61389": "BombBag & ((DCChild & ChildWeapon) | DCAdult)",
    "InsideJabuJabuBelly:32711": "ChildWeapon",
    "ForestTemple:85827": "GoronBracelet & Bow",
    "ForestTemple:40670": "GoronBracelet & Bow",
    "FireTemple:15044": "Longshot",
    "FireTemple:46138": "Longshot",
    "FireTemple:64248": "Hammer & BombBag",
    "WaterTemple:89517": "Longshot",
    "ShadowTemple:34372": "Longshot",
    "SpiritTemple:11131": "(SpiritAdult & AdultFire) | (SpiritChild & DinsMagic)",
    "SpiritTemple:28435": "SpiritAdult & Lullaby",
    "SpiritTemple:41804": "SpiritAdult",
    "SpiritTemple:34931": "SpiritAdult | (SpiritChild & Boomerang)",
    "SpiritTemple:42636": "Boomerang",
    "SpiritTemple:74946": "SpiritAdult | (SpiritChild & Boomerang)",
    "SpiritTemple:00600": "SpiritAdult",
    "SpiritTemple:95114": "SpiritAdult & Time",
    "SpiritTemple:14969": "SpiritAdult & MirrorShield",
    "GerudoTrainingGround:25188": "true",
    "InsideGanonCastle:76550": "GanonTower",
}

AREAS = {
    "KokiriForest": ("true", "A_KF"),
    "LostWood": ("C_LW", "A_LW"),
    "SacredForestMeadow": ("C_SFM", "A_SFM"),
    "HyruleField": ("C_Field", "adult"),
    "HyruleCastle": ("C_HC", None),
    "Market": ("C_Market", "adult"),
    "KakarikoVillage": ("C_Kak", "A_Kak"),
    "Graveyard": ("C_Graveyard", "A_Graveyard"),
    "DeathMountainTrail": ("C_DMT", "A_DMT"),
    "GoronCity": ("C_GC", "A_GC"),
    "DeathMountainCrater": ("C_DMCUpper | C_DMCLower", "A_DMCUpper | A_DMCLower"),
    "ZoraRiver": ("C_ZR", "A_ZR"),
    "ZoraDomain": ("C_ZD", "A_ZD"),
    "ZoraFountain": ("C_ZF", "A_ZF"),
    "GerudoValley": ("C_GV", "A_GV"),
    "GerudoFortress": (None, "A_GF"),
    "HountedWasteland": (None, "A_Wasteland"),
    "DesertColossus": ("C_Colossus", "A_Colossus"),
    "GanonCastle": (None, "adult"),
}

CHECKS = {
    "KokiriForest:87229": "C_Field | A_KF",
    "KokiriForest:31424": "C_Field | A_KF",
    "KokiriForest:53848": "ChildAttack",
    "LostWood:47230": "A_SFM & Longshot",
    "LostWood:27112": "C_LW & Bottle",
    "HyruleField:23154": "(C_Field & BombBag) | (adult & (BombBag | Hammer))",
    "HyruleField:36203": "A_LH & Ocarina & Longshot",
    "HyruleField:60331": "A_LH & IronBoots",
    "HyruleField:91711": "A_LH & Longshot",
    "HyruleCastle:62607": "C_HC & Storms & BombBag & Boomerang",
    "KakarikoVillage:06002": "C_Kak & (Boomerang | Storms)",
    "Graveyard:56087": "(C_Graveyard | A_Graveyard) & Sun",
    "Graveyard:84951": "A_Graveyard & Longshot",
    "Graveyard:97198": "A_Graveyard",
    "Graveyard:59554": "A_Graveyard",
    "Graveyard:71947": "A_Graveyard",
    "Graveyard:94602": "A_Graveyard",
    "DeathMountainTrail:91725": "(C_DMT & BombBag) | (A_DMT & (BombBag | Hammer))",
    "DeathMountainTrail:82696": "(C_DMT & BombBag & Boomerang) | (A_DMT & (BombBag | Hammer))",
    "DeathMountainTrail:21346": "A_DMT & Hammer",
    "DeathMountainTrail:38406": "A_DMTSummit & Hammer",
    "DeathMountainTrail:87506": "C_DMT & Bottle & (BombBag | GoronBracelet)",
    "GoronCity:65014": "A_GC & (Hammer | SilverGauntlets)",
    "GoronCity:09858": "A_GC & (Hammer | SilverGauntlets)",
    "GoronCity:55120": "(C_GC & BombBag) | (A_GC & (BombBag | Hammer | SilverGauntlets))",
    "GoronCity:13434": "(C_GC & BombBag) | (A_GC & (BombBag | Hammer | SilverGauntlets))",
    "GoronCity:55163": "C_GC & BombBag",
    "DeathMountainCrater:32045": "A_DMCCentral & HoverBoots",
    "DeathMountainCrater:86545": "C_DMCUpper | A_DMCUpper",
    "DeathMountainCrater:11695": "C_DMCLower",
    "DeathMountainCrater:65076": "C_DMCLower & Bottle",
    "DeathMountainCrater:54574": "C_DMCUpper & ChildAttack",
    "ZoraRiver:08272": "C_ZR | (A_ZR & HoverBoots)",
    "ZoraRiver:29345": "C_ZR | (A_ZR & HoverBoots)",
    "ZoraDomain:39233": "C_ZD & ChildFire",
    "ZoraFountain:90602": "A_ZF & IronBoots",
    "ZoraFountain:03742": "(C_ZF & Boomerang) | (A_ZF & SilverGauntlets & (BombBag | Hammer))",
    "GerudoValley:87133": "(C_GV | A_GV) & Storms & LensUse",
    "GerudoValley:55604": "A_GV & Storms",
    "GerudoValley:63865": "C_GV & Storms",
    "GerudoValley:11229": "A_GF & Hammer",
    "GerudoValley:61465": "A_GF",
    "GerudoValley:53934": "A_GF",
    "GerudoFortress:97715": "A_GF & (HoverBoots | Longshot)",
    "GerudoFortress:52038": "A_GF & GerudoCard",
    "HountedWasteland:92638": "A_Wasteland & AdultFire",
    "DesertColossus:05179": "SpiritChild",
    "DesertColossus:63548": "SpiritAdult",
    "DesertColossus:34681": "A_Colossus & Requiem",
    "DesertColossus:17210": "A_Colossus",
    "DesertColossus:12936": "A_Colossus & Longshot",
}
CHECK_KEYS = {"DesertColossus:05179": "SpiritTemple", "DesertColossus:63548": "SpiritTemple"}

SHOP_RULES = {
    "GoronCity": "(C_GC & (BombBag | GoronBracelet | ChildFire)) | (A_GC & (BombBag | Bow | GoronBracelet))",
}

OBJECT_RULES = {
    "Obj_LiftRock_A_01": ("GoronBracelet", "true"),
    "Obj_BrokenRock_A_01": ("BombBag", "BombBag | Hammer"),
    "Obj_BrokenRock_A_02": ("false", "Hammer"),
    "Obj_Kokiri_Beehive_A_01": ("Slingshot | Boomerang | BombBag", "true"),
    "Obj_Heart_InWater": ("Dive", "Dive | IronBoots"),
}

SKULLTULA_RULES = {
    "bean": ("Bottle", "false"),
    "box": ("ChildAttack", "true"),
    "tree": ("ChildAttack", "true"),
    "wall": ("Boomerang", "true"),
}
CHILD_DUNGEONS = {"InsideTheDekuTree", "InsideJabuJabuBelly", "BottomOfTheWell"}

GROTTO_COVERS = {
    "storms": ("Storms", "Storms"),
    "blast": ("BombBag", "BombBag | Hammer"),
    "silver": ("false", "SilverGauntlets"),
    "hammer": ("false", "Hammer"),
    "open": ("true", "true"),
}
GROTTO_INSIDE = {
    "fight": ("KokiriSword | Sticks | DinsMagic", "true"),
    "fire": ("DinsMagic", "AdultFire"),
    "bombs": ("BombBag", "BombBag"),
    "dive": ("GoldScale", "IronBoots | GoldScale"),
    "none": ("true", "true"),
}
GROTTO_HOLES = {"17": ("false", "Tunic_Goron")}

TRIAL_RULES = {
    "Forest": "AdultFire",
    "Fire": "Tunic_Goron & GoldGauntlets & Longshot",
    "Water": "Bottle & Hammer",
    "Shadow": "Hammer & LensUse & (FireArrowsMagic | (Longshot & (HoverBoots | DinsMagic)))",
    "Spirit": "MirrorShield & BombBag",
    "Light": "GoldGauntlets & LensUse",
}
BRIDGE_RULES = {
    "vanilla": "adult & ShadowMedallion & SpiritMedallion & LightArrows",
    "open": "adult",
}
GANON_FIGHT = "adult & LightArrows & Bow & Magic"

LOGIC_LEVELS = {
    "safe": "Safe: follows the game's real requirements, and also expects each dungeon's main item before its other rooms.",
    "relaxed": "Relaxed: follows the game's real requirements room by room, nothing extra.",
    "none": "No Logic: anything can be anywhere. The seed may not be beatable.",
}
SAFE_DUNGEON_ITEMS = {
    "InsideTheDekuTree": "Slingshot",
    "DodongoCavern": "BombBag",
    "InsideJabuJabuBelly": "Boomerang",
    "ForestTemple": "Bow",
    "FireTemple": "Hammer",
    "WaterTemple": "Longshot",
    "ShadowTemple": "HoverBoots",
    "SpiritTemple": "MirrorShield",
    "BottomOfTheWell": "Lens",
    "IceCavern": "IronBoots",
}

EXCLUDED_EVENTS = ("MiniGame_",)
EXCLUDED_AREAS = {"DreamWorld"}
EXCLUDED_ITEMS = {"Item_Dungeon_SmallKey", "Item_Dungeon_BossKey", "Obj_MiniGame_SmallKey",
                  "Item_ScrubBusinessSeed", "Obj_Heart_Container"}
EXCLUDED_ACTORS = ("Obj_HrlCity_Shop_TBox", "Obj_Dungeon_SmallKey", "Shop_Mask_", "Obj_GerudoValley_Heart_Piece",
                   "Item_OrnamentalBottle_Milk")

_DATA = json.loads((Path(__file__).resolve().parent / "data" / "logic_data.json").read_text())
GROTTO_MEMBERS = _DATA["grotto_members"]
GROTTO_TABLE = _DATA["holes"]
SKULLTULA_KINDS = _DATA["skulltulas"]


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
        return lambda s, t=tok: t in s

    def __call__(self, state):
        return self.fn(state)


BASE_EVENTS = dict(EVENTS)
_EVENT_RULES = {}
_CACHE = {}
SMALL_KEYS = {}


def _all(*parts):
    parts = [p for p in parts if p and p != "true"]
    if not parts:
        return "true"
    if "false" in parts:
        return "false"
    return " & ".join(f"({p})" for p in parts)


def _any(*parts):
    parts = [p for p in parts if p and p != "false"]
    if not parts:
        return "false"
    if "true" in parts:
        return "true"
    return " | ".join(f"({p})" for p in parts)


def configure(overrides=None, bridge="vanilla", trials=6, small_keys=None, boss_keys=None):
    global _EVENT_RULES
    SMALL_KEYS.clear()
    SMALL_KEYS.update(small_keys or {})
    events = dict(BASE_EVENTS)
    for area, (event, entry, done) in DUNGEONS.items():
        needs = SMALL_KEYS.get(area, []) + ([boss_keys[area]] if boss_keys and area in boss_keys else [])
        events[event] = _all(entry, done, *needs)
    events.update(overrides or {})
    if isinstance(trials, int):
        trials = list(TRIAL_RULES)[:max(0, min(6, trials))]
    tower = [TRIAL_RULES[t] for t in trials]
    events["GanonBridge"] = BRIDGE_RULES.get(bridge, BRIDGE_RULES["vanilla"])
    events["GanonTower"] = _all("GanonBridge", *(["LightArrows & Bow & Magic"] + tower if tower else []))
    ganon_needs = SMALL_KEYS.get("InsideGanonCastle", []) + (
        [boss_keys["InsideGanonCastle"]] if boss_keys and "InsideGanonCastle" in boss_keys else [])
    events["Ganon"] = _all("GanonBridge", "GanonTower", GANON_FIGHT, *ganon_needs)
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


def check_key(loc):
    return f"{loc['area']}:{loc['hash'][-5:]}"


def ages(loc):
    variants = " ".join(loc["variants"])
    child = "Child" in variants or "Adult" not in variants
    adult = "Adult" in variants or "Child" not in variants
    return child, adult


def location_rule(loc, level="safe"):
    if level == "none":
        return rule("true")
    if loc["area"] in DUNGEONS:
        text = _dungeon_rule(loc, level)
    else:
        text = _overworld_rule(loc)
    return rule(text)


def _dungeon_rule(loc, level):
    area = loc["area"]
    _, entry, _ = DUNGEONS[area]
    parts = [entry, ROOM_RULES.get((area, loc["room"])), DUNGEON_CHECKS.get(check_key(loc))]
    if loc["kind"] == "skulltula" and check_key(loc) not in DUNGEON_CHECKS:
        parts.append("Boomerang" if area in CHILD_DUNGEONS else "true")
    if level == "safe" and area in SAFE_DUNGEON_ITEMS and loc["room"] not in (0, None):
        main = SAFE_DUNGEON_ITEMS[area]
        if PROGRESSION.get(loc["item"]) != main and loc["item"] not in ("Item_Dungeon_Map", "Item_Dungeon_Compass"):
            parts.append("LensUse" if main == "Lens" else main)
    parts += SMALL_KEYS.get(area, [])
    return _all(*parts)


def _overworld_rule(loc):
    key = check_key(loc)
    area = AREAS.get(loc["area"])
    if area is None:
        return "false"
    if key in CHECKS:
        return _all(CHECKS[key], *SMALL_KEYS.get(CHECK_KEYS.get(key), []))
    child_ok, adult_ok = ages(loc)
    child = area[0] if child_ok else None
    adult = area[1] if adult_ok else None
    extra_c, extra_a = [], []
    hole = GROTTO_MEMBERS.get(loc["hash"])
    if hole is not None:
        info = GROTTO_TABLE[hole]
        cover = GROTTO_HOLES.get(hole) or GROTTO_COVERS[info["cover"]]
        inside = GROTTO_INSIDE[info["inside"]]
        extra_c += [cover[0], inside[0]]
        extra_a += [cover[1], inside[1]]
    if loc["kind"] == "skulltula":
        kind = SKULLTULA_RULES[SKULLTULA_KINDS.get(loc["hash"], "wall")]
        extra_c.append(kind[0])
        if kind[1] == "false":
            adult = None
    if loc["kind"] == "shop" and loc["area"] in SHOP_RULES:
        return SHOP_RULES[loc["area"]]
    need = OBJECT_RULES.get(loc.get("actor"))
    if need and loc["kind"] in ("breakable", "rock", "heart", "rupee", "floor"):
        extra_c.append(need[0])
        extra_a.append(need[1])
    return _any(_all(child, *extra_c) if child else None, _all(adult, *extra_a) if adult else None)


def is_shuffled(loc, keys=False):
    if loc["area"] in EXCLUDED_AREAS or (loc["item"] in EXCLUDED_ITEMS and not keys):
        return False
    if loc["actor"].startswith(EXCLUDED_ACTORS):
        return False
    if loc["event"] and loc["event"].startswith(EXCLUDED_EVENTS):
        return False
    return loc["area"] in AREAS or loc["area"] in DUNGEONS


configure()
