import bfres
import byml
import sarc

ACTOR_INFO = "RSDB/ActorInfo.Product.111.rstbl.byml.zs"
HEAPS = ("InstanceHeapSize", "PreActorRenderInfoHeapSize")
CLOTH_KEYS = ("Cloth", "ClothAdvandecOption", "ClothList", "ClothReaction",
              "HelperBoneList", "HelperBoneControlBoneGroup")

MODELS = {
    "Lunk (Stout Link)": ("Player_Adult", "Player_Adult"),
    "Lank (Stretched Link)": ("Player_Child", "Player_Child"),
}

SLOTS = {
    "child_model": {
        "label": "Young Link's Body", "default": "Link", "native": "Lank (Stretched Link)",
        "actors": {"Player_Child": "Player_Child"},
    },
    "adult_model": {
        "label": "Adult Link's Body", "default": "Link", "native": "Lunk (Stout Link)",
        "actors": {"Player_Adult": "Player"},
        "cloth": {"Lank (Stretched Link)": (
            "Player_Child", "Phive/ControllerSetParam/Player_Child.phive__ControllerSetParam.bgyml",
            "Actor/Player_Adult.engine__actor__ActorParam.bgyml", "Player_Lank")},
        "pin": {"Lank (Stretched Link)": ("Model/Player_Child.Player_Child.bfres.zs", {
            "Spine_2": ["Ph_ShoulderBelt_Root", "Ph_ShoulderBelt_1", "Ph_ShoulderBelt_2", "Ph_ShoulderBelt_3",
                        "Ph_ShoulderBelt_4"],
            "Spine_1": ["Ph_Belt_A"],
            "Waist": ["Ph_Belt_1", "Ph_Belt_2", "Ph_WaistBelt_2"],
            "Head_2": ["Ph_Feather_1", "Ph_Feather_2", "Ph_HatString_1", "Ph_HatString_2"]})},
    },
}


def _work_paths(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _work_paths(v)
    elif isinstance(value, list):
        for v in value:
            yield from _work_paths(v)
    elif isinstance(value, str) and value.startswith("Work/") and value.endswith(".gyml"):
        yield value[len("Work/"):-len(".gyml")] + ".bgyml"


def _copy_cloth(game, writer, spec):
    source_actor, source_set, actor_param, name = spec
    source = sarc.Sarc(game.read(f"Pack/Actor/{source_actor}.pack.zs"))
    donor, version, endian = byml.loads(bytes(source.get_file(source_set).data))
    controller = {"$parent": "Work/Phive/ControllerSetParam/Player.phive__ControllerSetParam.gyml"}
    for key in CLOTH_KEYS:
        if key in donor:
            controller[key] = donor[key]
            for path in _work_paths(donor[key]):
                if path not in writer.files and source.get_file(path) is not None:
                    writer.files[path] = bytes(source.get_file(path).data)
    writer.files[f"Phive/ControllerSetParam/{name}.phive__ControllerSetParam.bgyml"] = \
        byml.dumps(controller, version, endian)
    physics = {"$parent": "Work/Component/Physics/Player.engine__component__PhysicsParam.gyml",
               "ControllerSetPath": f"Work/Phive/ControllerSetParam/{name}.phive__ControllerSetParam.gyml"}
    writer.files[f"Component/Physics/{name}.engine__component__PhysicsParam.bgyml"] = \
        byml.dumps(physics, version, endian)
    actor, version, endian = byml.loads(writer.files[actor_param])
    actor["Components"]["PhysicsRef"] = f"?Component/Physics/{name}.engine__component__PhysicsParam.bgyml"
    writer.files[actor_param] = byml.dumps(actor, version, endian)


def choices_for(slot):
    return [SLOTS[slot]["default"]] + [m for m in MODELS if m != SLOTS[slot]["native"]] + ["Random"]


CHOICES = sorted({c for slot in SLOTS for c in choices_for(slot)})


def resolve(choices, rng):
    out = {}
    for slot, spec in SLOTS.items():
        value = choices.get(slot, spec["default"])
        if value == "Random":
            value = rng.choice([spec["default"]] + [m for m in MODELS if m != spec["native"]])
        if value not in MODELS or value == spec["native"]:
            continue
        out[slot] = value
    return out


def build(game, builder, choices, rng):
    summary = {}
    picked = resolve(choices, rng)
    rows = {r["__RowId"]: r for r in builder.placement(ACTOR_INFO)} if picked else {}
    for slot, value in picked.items():
        fmdb, source = MODELS[value]
        for actor, info_name in SLOTS[slot]["actors"].items():
            path = f"Pack/Actor/{actor}.pack.zs"
            pack = sarc.Sarc(game.read(path))
            writer = sarc.SarcWriter.from_sarc(pack)
            name = f"Component/ModelInfo/{info_name}.engine__component__ModelInfo.bgyml"
            info, version, endian = byml.loads(bytes(pack.get_file(name).data))
            info["FmdbName"] = fmdb
            info["ModelProjectName"] = fmdb
            info.pop("ModelVariationAnims", None)
            writer.files[name] = byml.dumps(info, version, endian)
            cloth = SLOTS[slot].get("cloth", {}).get(value)
            if cloth:
                _copy_cloth(game, writer, cloth)
            _, data = writer.write()
            builder.put(path, bytes(data))
            pin = SLOTS[slot].get("pin", {}).get(value)
            if pin:
                model, groups = pin
                data = game.read(model)
                for anchor, bones in groups.items():
                    data = bfres.pin_bones(data, bones, anchor)
                builder.put(model, data)
            row, src = rows.get(actor), rows.get(source)
            if row is not None and src is not None:
                for key in HEAPS:
                    row[key] = max(row.get(key, 0), src.get(key, 0))
        summary[SLOTS[slot]["label"]] = value
    return summary
