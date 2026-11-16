import io

import evfl

SPOTS = {
    "Saria": {"song": "Item_Melody_SariaSong", "type": 2, "event": "SariasSong",
              "rule": "C_SFM & ZeldasLetter", "where": "Saria in Sacred Forest Meadow"},
    "Epona": {"song": "Item_Melody_EponaSong", "type": 1, "event": "EponasSong",
              "rule": "C_Field & ZeldasLetter & Ocarina", "where": "Malon at Lon Lon Ranch"},
    "Storm": {"song": "Item_Melody_StormSong", "type": 5, "event": "SongOfStorms",
              "rule": "A_Kak & Ocarina", "where": "the Windmill in Kakariko"},
    "Sun": {"song": "Item_Melody_SunSong", "type": 3, "event": "SunsSong",
            "rule": "(C_Graveyard | A_Graveyard) & Lullaby", "where": "the Royal Family's Tomb"},
    "Forest": {"song": "Item_Melody_ForestMinuet", "type": 6, "event": "MinuetOfForest",
               "rule": "A_LW & Saria", "where": "Sheik in Sacred Forest Meadow"},
    "Fire": {"song": "Item_Melody_FireBolero", "type": 7, "event": "BoleroOfFire",
             "rule": "A_DMCUpper | (A_GCDarunia & Tunic_Goron)", "where": "Sheik in Death Mountain Crater"},
    "Water": {"song": "Item_Melody_WaterSerenade", "type": 8, "event": "SerenadeOfWater",
              "rule": "A_ZF & Bottle", "where": "Sheik in the Ice Cavern"},
    "Shadow": {"song": "Item_Melody_ShadowNocturne", "type": 10, "event": "NocturneOfShadow",
               "rule": "A_Kak & ForestMedallion & FireMedallion & WaterMedallion",
               "where": "Sheik in Kakariko Village"},
    "Spilit": {"song": "Item_Melody_SpiritRequiem", "type": 9, "event": "RequiemOfSpirit",
               "rule": "A_Wasteland & LensUse", "where": "Sheik at the Desert Colossus"},
    "Shine": {"song": "Item_Melody_LightPrelude", "type": 11, "event": "PreludeOfLight",
              "rule": "adult & ForestMedallion", "where": "Sheik in the Temple of Time"},
}
SONG_NAMES = {
    "Item_Melody_SariaSong": "Saria's Song", "Item_Melody_EponaSong": "Epona's Song",
    "Item_Melody_StormSong": "Song of Storms", "Item_Melody_SunSong": "Sun's Song",
    "Item_Melody_ForestMinuet": "Minuet of Forest", "Item_Melody_FireBolero": "Bolero of Fire",
    "Item_Melody_WaterSerenade": "Serenade of Water", "Item_Melody_ShadowNocturne": "Nocturne of Shadow",
    "Item_Melody_SpiritRequiem": "Requiem of Spirit", "Item_Melody_LightPrelude": "Prelude of Light",
}
BY_SONG = {spot["song"]: spot for spot in SPOTS.values()}


def shuffle(rng):
    songs = [spot["song"] for spot in SPOTS.values()]
    rng.shuffle(songs)
    return dict(zip(SPOTS, songs))


def event_rules(mapping):
    return {BY_SONG[song]["event"]: SPOTS[spot]["rule"] for spot, song in mapping.items()}


def _swap(params, old, new):
    for key, value in list(params.data.items()):
        raw = value.v if hasattr(value, "v") else value
        text = str(raw)
        if key == "MelodyType" and text == str(old["type"]):
            replacement = type(raw)(new["type"]) if not isinstance(raw, str) else str(new["type"])
        elif key in ("ActorName", "GameDataName") and old["song"] in text:
            replacement = text.replace(old["song"], new["song"])
        else:
            continue
        if hasattr(value, "v"):
            value.v = replacement
        else:
            params.data[key] = replacement


def build(game, mapping):
    files = {}
    for spot, song in mapping.items():
        old, new = SPOTS[spot], BY_SONG[song]
        if old is new:
            continue
        for path in game.glob(f"Event/EventFlow/Dm_MelodyGet_{spot}*.bfevfl.zs"):
            f = evfl.EventFlow()
            f.read(game.read(path))
            for event in f.flowchart.events:
                params = getattr(event.data, "params", None)
                if params is not None:
                    _swap(params, old, new)
            out = io.BytesIO()
            f.write(out)
            files[path] = out.getvalue()
    return files
