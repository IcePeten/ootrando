NPC_GIFTS = [
    {
        "id": "Darunia", "name": "Darunia's Dance", "area": "GoronCity", "item": "Item_Gauntlet_Goron",
        "flow": "Dm_Goron_0030", "events": {"Event127": ["ActorName"]},
        "rule": "child & ZeldasLetter & ZeldasLullaby & SariasSong", "accepts": "chest",
    },
    {
        "id": "GreatFairyDin", "name": "Great Fairy (Din's Fire)", "area": "HyruleCastle", "item": "Item_DinFire",
        "flow": "Dm_FairyFountain_Din", "events": {"Event212": ["ActorName"]}, "flag_event": "Event78",
        "rule": "Field & ZeldasLullaby & BombBag", "accepts": "flagged",
    },
    {
        "id": "GreatFairyFarore", "name": "Great Fairy (Farore's Wind)", "area": "ZoraFountain",
        "item": "Item_FaroreWind", "flow": "Dm_FairyFountain_Frore", "events": {"Event174": ["ActorName"]},
        "flag_event": "Event11", "rule": "ZoraDomain & ZeldasLullaby & BombBag", "accepts": "flagged",
    },
    {
        "id": "GreatFairyNayru", "name": "Great Fairy (Nayru's Love)", "area": "DesertColossus",
        "item": "Item_NayruLove", "flow": "Dm_FairyFountain_Nayru", "events": {"Event163": ["ActorName"]},
        "flag_event": "Event10", "rule": "RequiemOfSpirit & ZeldasLullaby & BombBag", "accepts": "flagged",
    },
    {
        "id": "DivingGame", "name": "Zora Diving Game", "area": "ZoraDomain", "item": "Item_Scale_Silver",
        "flow": "MiniGame_Diving", "events": {"Event21": ["ActorName"]},
        "rule": "child & ZoraDomain", "accepts": "chest",
    },
    {
        "id": "FishingChild", "name": "Fishing Pond (Child)", "area": "LakeHylia", "item": "Obj_Heart_Piece",
        "flow": "MiniGame_Fishing", "events": {"Event821": ["ActorName"], "Event573": ["ReveiveItem"]},
        "rule": "child & Field", "accepts": "chest",
    },
    {
        "id": "FishingAdult", "name": "Fishing Pond (Adult)", "area": "LakeHylia", "item": "Item_Scale_Gold",
        "flow": "MiniGame_Fishing", "events": {"Event822": ["ActorName"], "Event579": ["ReveiveItem"]},
        "rule": "adult", "accepts": "chest",
    },
    {
        "id": "HorsebackArchery", "name": "Horseback Archery", "area": "GerudoFortress", "item": "Obj_Heart_Piece",
        "flow": "Minigame_HorsebackArchery", "events": {"Event322": ["ActorName"]},
        "rule": "GerudoCard & EponasSong & Bow", "accepts": "chest",
    },
    {
        "id": "SkullKid", "name": "Skull Kid (Saria's Song)", "area": "LostWood", "item": "Obj_Heart_Piece",
        "flow": "Npc_SkullKid_Child", "events": {"Event71": ["ActorName"]},
        "rule": "child & SariasSong", "accepts": "chest",
    },
    {
        "id": "SkullKidMemory", "name": "Lost Woods Ocarina Game", "area": "LostWood", "item": "Obj_Heart_Piece",
        "flow": "Npc_SkullKid_Child_02", "events": {"Event24": ["ActorName"]},
        "rule": "child & SariasSong & FairyOcarina", "accepts": "chest",
    },
    {
        "id": "DampeDigging", "name": "Dampe's Digging Tour", "area": "Graveyard", "item": "Obj_Heart_Piece",
        "flow": "Npc_Hylia_Dampe_001",
        "events": {"Event628": ["ActorName"], "Event291": ["DropActorName"], "Event82": ["ActorName"]},
        "rule": "child & Field", "accepts": "floor",
    },
    {
        "id": "SariaOcarina", "name": "Saria's Gift (Fairy Ocarina)", "area": "KokiriForest",
        "item": "Item_Ocarina_Fairy", "flow": "Dm_Kokiri_0155",
        "events": {"Event68": ["Actor"], "Event77": ["ActorName"]},
        "rule": "child & DekuTreeBeaten", "accepts": "pouch",
    },
    {
        "id": "GerudoCard", "name": "Gerudo Membership Card", "area": "GerudoFortress",
        "item": "Item_Token_Gerudo", "flow": "Dm_Gerudo_0025", "events": {"Event294": ["ActorName"]},
        "rule": "adult & (EponasSong | Longshot) & Hookshot & Bow", "accepts": "chest", "setting": "shuffle_gerudo_card",
    },
    {
        "id": "FrogBugs", "name": "Frogs' Bug Game", "area": "ZoraRiver", "item": "Obj_Heart_Piece",
        "flow": "MiniGame_FrogTenors", "events": {"Event161": ["ActorName"], "Event75": ["ActorName"]},
        "rule": "child & Field & BombBag & FairyOcarina", "accepts": "chest", "setting": "shuffle_frogs",
    },
    {
        "id": "FrogSongs", "name": "Frogs' Song Reward", "area": "ZoraRiver", "item": "Obj_Heart_Piece",
        "flow": "MiniGame_FrogTenors", "events": {"Event384": ["ActorName"]},
        "rule": "child & Field & BombBag & FairyOcarina & ZeldasLullaby & EponasSong & SariasSong & SunsSong"
                " & SongOfTime & SongOfStorms", "accepts": "chest", "setting": "shuffle_frogs",
    },
    {
        "id": "MarketGallery", "name": "Castle Town Shooting Gallery", "area": "Market",
        "item": "Item_BulletBag_Medium", "flow": "MiniGame_HitTarget",
        "events": {"Event378": ["ReveiveItem"], "Event241": ["ReveiveItem"]},
        "rule": "child & Field", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "KakarikoGallery", "name": "Kakariko Shooting Gallery", "area": "KakarikoVillage",
        "item": "Item_Quiver_Medium", "flow": "MiniGame_HitTarget",
        "events": {"Event242": ["ReveiveItem"], "Event381": ["ReveiveItem"]},
        "rule": "adult & Bow", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "LostWoodsTargets", "name": "Lost Woods Target Game", "area": "LostWood",
        "item": "Item_BulletBag_Large", "flow": "Dm_LostWood_0040",
        "events": {"Event17": ["ActorName"], "Event30": ["ActorName"]},
        "rule": "child & SariasSong & Slingshot", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "HorsebackArcheryQuiver", "name": "Horseback Archery (1500 Points)", "area": "GerudoFortress",
        "item": "Item_Quiver_Large", "flow": "Minigame_HorsebackArchery",
        "events": {"Event319": ["ActorName"], "Event320": ["ActorName"]},
        "rule": "GerudoCard & EponasSong & Bow", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "RollingGoron", "name": "Rolling Goron", "area": "GoronCity", "item": "Item_BombBag_Medium",
        "flow": "Npc_Goron_006_Child", "events": {"Event58": ["ReveiveItem"], "Event92": ["ReveiveItem"]},
        "rule": "child & GateOpen & BombBag & GoronBracelet", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "BowlingBombBag", "name": "Bombchu Bowling (Bomb Bag)", "area": "Market", "item": "Item_BombBag_Large",
        "flow": "MiniGame_BombchuBowling", "events": {"Event304": ["ReveiveItem"], "Event306": ["ReveiveItem"]},
        "rule": "((child & Field) | adult) & BombBag", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "BowlingHeart", "name": "Bombchu Bowling (Piece of Heart)", "area": "Market",
        "item": "Obj_Heart_Piece", "flow": "MiniGame_BombchuBowling", "events": {"Event143": ["ReveiveItem"]},
        "rule": "((child & Field) | adult) & BombBag", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "BowlingBombchus", "name": "Bombchu Bowling (Bombchus)", "area": "Market",
        "item": "Item_BombchuBundle_Medium", "flow": "MiniGame_BombchuBowling",
        "events": {"Event309": ["ReveiveItem"]},
        "rule": "((child & Field) | adult) & BombBag", "accepts": "chest", "setting": "shuffle_minigames",
    },
    {
        "id": "CuccoLady", "name": "Cucco Lady (Return the Cuccos)", "area": "KakarikoVillage",
        "item": "Item_Bottle", "flow": "Minigame_CatchCucco", "events": {"Event181": ["ReveiveItem"]},
        "rule": "child & Field", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "TalonCuccos", "name": "Talon's Cucco Game", "area": "LonLonRanch", "item": "Item_Bottle_Milk",
        "flow": "Minigame_FindOutCucco", "events": {"Event23": ["ReveiveItem"]},
        "rule": "child & Field", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "DogLady", "name": "Dog Lady (Find Richard)", "area": "Market", "item": "Obj_Heart_Piece",
        "flow": "SubEvent_FindRichard", "events": {"Event16": ["ReveiveItem"]},
        "rule": "child & Field", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "PoeCollector", "name": "Poe Collector (Big Poes)", "area": "Market", "item": "Item_Bottle",
        "flow": "Npc_Hylia_048_BottleShop", "events": {"Event329": ["ActorName"]},
        "rule": "adult & EponasSong & Bow & Bottle", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "PotionShopBottle", "name": "Potion Shop Bug Quest", "area": "Market", "item": "Item_Bottle",
        "flow": "Npc_Hylia_020_Shop_Child", "events": {"Event171": ["ActorName"]},
        "rule": "child & Field", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "MaskOfTruth", "name": "Happy Mask Shop (Mask of Truth)", "area": "Market", "item": "Item_Mask_Truth",
        "flow": "Npc_Hylia_023_Shop_Child", "events": {"Event51": ["ActorName"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "ForestStageSkull", "name": "Forest Stage (Skull Mask)", "area": "LostWood",
        "item": "Item_StickBag_Medium", "flow": "LostWood_ScrubForestStageElder_SkullMaskFirst",
        "events": {"Event29": ["ActorName"], "Event32": ["ActorName"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "ForestStageTruth", "name": "Forest Stage (Mask of Truth)", "area": "LostWood",
        "item": "Item_NutBag_Medium", "flow": "LostWood_ScrubForestStageElder_TrueMaskFirst",
        "events": {"Event2": ["ActorName"], "Event31": ["ActorName"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_sidequests",
    },
    {
        "id": "Skulltula10", "name": "Skulltula House (10 Tokens)", "area": "KakarikoVillage",
        "item": "Item_Wallet_Medium", "flow": "GatheringTokenGold", "events": {"Event398": ["TakenRewardActor"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_skulltula_rewards",
    },
    {
        "id": "Skulltula20", "name": "Skulltula House (20 Tokens)", "area": "KakarikoVillage",
        "item": "Item_AgonyStone", "flow": "GatheringTokenGold", "events": {"Event75": ["TakenRewardActor"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_skulltula_rewards",
    },
    {
        "id": "Skulltula30", "name": "Skulltula House (30 Tokens)", "area": "KakarikoVillage",
        "item": "Item_Wallet_Large", "flow": "GatheringTokenGold", "events": {"Event194": ["TakenRewardActor"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_skulltula_rewards",
    },
    {
        "id": "Skulltula40", "name": "Skulltula House (40 Tokens)", "area": "KakarikoVillage",
        "item": "Item_BombchuBundle_Large", "flow": "GatheringTokenGold",
        "events": {"Event200": ["TakenRewardActor"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_skulltula_rewards",
    },
    {
        "id": "Skulltula50", "name": "Skulltula House (50 Tokens)", "area": "KakarikoVillage",
        "item": "Obj_Heart_Piece", "flow": "GatheringTokenGold", "events": {"Event219": ["TakenRewardActor"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_skulltula_rewards",
    },
    {
        "id": "GreatFairyMagic", "name": "Great Fairy (Magic Meter)", "area": "DeathMountainTrail",
        "item": "Item_FairyBless_MP", "flow": "Dm_FairyFountain_Power", "events": {"Event141": ["ActorName"]},
        "flag_event": "Event11", "rule": "((child & GateOpen) | adult) & BombBag & ZeldasLullaby",
        "accepts": "flagged", "setting": "shuffle_great_fairies",
    },
    {
        "id": "GreatFairyDoubleMagic", "name": "Great Fairy (Double Magic)", "area": "DeathMountainCrater",
        "item": "Item_FairyBless_MPDouble", "flow": "Dm_FairyFountain_Wisdom", "events": {"Event144": ["ActorName"]},
        "flag_event": "Event10", "rule": "adult & BombBag & Hammer & ZeldasLullaby",
        "accepts": "flagged", "setting": "shuffle_great_fairies",
    },
    {
        "id": "GreatFairyDoubleDefense", "name": "Great Fairy (Double Defense)", "area": "GanonCastle",
        "item": "Item_FairyBless_DefenseDouble", "flow": "Dm_FairyFountain_Courage",
        "events": {"Event144": ["ActorName"]}, "flag_event": "Event11",
        "rule": "adult & GoldGauntlets & ZeldasLullaby", "accepts": "flagged", "setting": "shuffle_great_fairies",
    },
    {
        "id": "MalonEgg", "name": "Malon's Gift (Weird Egg)", "area": "HyruleCastle", "item": "Item_WeirdEgg",
        "flow": "Goto_HyruleCastle", "events": {"Event35": ["ActorName"]},
        "rule": "child & Field", "accepts": "chest", "setting": "shuffle_story_gifts",
    },
    {
        "id": "ZeldaLetter", "name": "Princess Zelda (Zelda's Letter)", "area": "HyruleCastle",
        "item": "Item_ZeldaLetter", "flow": "Dm_HrlCastle_0050", "events": {"Event59": ["ActorName"]},
        "rule": "child & Field & WeirdEgg", "accepts": "chest", "setting": "shuffle_story_gifts",
    },
    {
        "id": "LightArrows", "name": "Princess Zelda (Light Arrows)", "area": "HyruleCastle",
        "item": "Item_Arrow_Light", "flow": "Dm_TimeTemple_0130", "events": {"Event85": ["ActorName"]},
        "rule": "adult & ShadowMedallion & SpiritMedallion", "accepts": "pouch", "setting": "shuffle_story_gifts",
    },
    {
        "id": "Biggoron", "name": "Biggoron (Trading Quest)", "area": "DeathMountainTrail",
        "item": "Item_Sword_Biggoron", "flow": "Npc_Goron_Biggoron_Adult", "events": {"Event123": ["ActorName"]},
        "rule": "false", "accepts": "chest", "setting": "shuffle_trade_rewards",
    },
]
