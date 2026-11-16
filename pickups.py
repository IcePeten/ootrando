import copy

import byml
import sarc

TEMPLATE = "Obj_Rupee_Blue"
ITEM_BASE = "Work/Actor/Obj_Item_Base.engine__actor__ActorParam.gyml"
TABLES = {
    "ActorInfo": "RSDB/ActorInfo.Product.111.rstbl.byml.zs",
    "GameActorInfo": "RSDB/GameActorInfo.Product.111.rstbl.byml.zs",
    "PouchActorInfo": "RSDB/PouchActorInfo.Product.111.rstbl.byml.zs",
}
FROM_ITEM = ("ActorNameRef", "AnimationRef", "ModelInfoRef", "PouchContentRef", "ASRef")


RUPOOR = "Obj_Rando_Rupoor"
RUPOOR_LOOK = "Obj_Rupee_Purple"
RUPOOR_MODEL = "Obj_Rupee_Silver"
RUPOOR_COST = -10
HEART_PIECE = "Obj_Heart_Piece"
SHAPE = "Phive/ShapeParam/Rupee_Body_0.phive__ShapeParam.bgyml"
CONTROLLER = "Phive/ControllerSetParam/Rupee.phive__ControllerSetParam.bgyml"
PHYSICS_BASE = "Work/Component/Physics/ProjectBase.engine__component__PhysicsParam.gyml"
BASE_LIFT = 0.15
MAX_LIFT = 0.6
SPARKLE = "Obj_Heart_Piece"


def _clone(game, builder, source_name, name, pouch=None, actor_edit=None, info_edit=None, game_edit=None,
           extra=None):
    source = sarc.Sarc(game.read(_pack_path(source_name)))
    writer = sarc.SarcWriter.from_sarc(source)
    writer.files.update(extra or {})
    old = f"Actor/{source_name}.engine__actor__ActorParam.bgyml"
    actor, version, endian = _load(source.get_file(old).data)
    comps = actor.setdefault("Components", {})
    if pouch is not None:
        pouch_path = f"Component/PouchContentParam/{name}.game__component__PouchContentParam.bgyml"
        parent = "Work/" + _work_to_file(comps["PouchContentRef"]).replace(".bgyml", ".gyml")
        writer.files[pouch_path] = byml.dumps({"$parent": parent, **pouch}, version, endian)
        comps["PouchContentRef"] = _file_ref(pouch_path)
    if actor_edit:
        actor_edit(comps)
    del writer.files[old]
    writer.files[f"Actor/{name}.engine__actor__ActorParam.bgyml"] = byml.dumps(actor, version, endian)
    _, packed = writer.write()
    builder.put_new(_pack_path(name), bytes(packed), _pack_path(source_name))
    for key, path in TABLES.items():
        table = builder.placement(path)
        row = next((r for r in table if r["__RowId"] == source_name), None)
        if row is None:
            continue
        row = copy.deepcopy(row)
        row["__RowId"] = name
        if key == "ActorInfo" and info_edit:
            info_edit(row)
        if key == "GameActorInfo" and game_edit:
            game_edit(row)
        table.append(row)
        table.sort(key=lambda r: r["__RowId"])


def _silver(row):
    row["FmdbName"] = RUPOOR_MODEL
    for k in [k for k in row if k.startswith("ModelVariation")]:
        row.pop(k)


def rupoor(game, builder):
    _clone(game, builder, RUPOOR_LOOK, RUPOOR, pouch={"BundleActorNum": RUPOOR_COST}, info_edit=_silver)


LIFT_ROCK = "Obj_LiftRock_A_01"
RESPAWN_ROCK = "Obj_Rando_LiftRock_A_01"
ALWAYS_RESPAWN = "?Component/ActorGameDataSetting/AlwaysRespawn.game__component__ActorGameDataSetting.bgyml"
RESPAWN_POT = "Obj_Pot_A_05_Respawn"
RESPAWN_DEATH = ("Component/DeathParam/Obj_AllowDeathDuringEventIfNotAffiliationAIGroup_AlwaysRespawn"
                 ".game__component__DeathParam.bgyml")


def respawn_rock(game, builder):
    pot = sarc.Sarc(game.read(_pack_path(RESPAWN_POT)))

    def always(comps):
        comps["ActorGameDataSetting"] = ALWAYS_RESPAWN
        comps["DeathRef"] = _file_ref(RESPAWN_DEATH)
    _clone(game, builder, LIFT_ROCK, RESPAWN_ROCK, actor_edit=always,
           game_edit=lambda row: row.pop("IsRespawn", None),
           extra={RESPAWN_DEATH: bytes(pot.get_file(RESPAWN_DEATH).data)})


def _shift(info):
    low = float((info.get("ModelAabbMin") or {}).get("Y", 0.0))
    return max(-MAX_LIFT, min(0.0, low - BASE_LIFT))


def _raised_physics(template, writer, name, shift, version, endian):
    shape, sv, se = _load(template.get_file(SHAPE).data)
    for capsule in shape.get("Capsule", []):
        for end in ("CenterA", "CenterB"):
            capsule[end]["Y"] = float(capsule[end]["Y"]) + shift
    auto = shape.get("AutoCalc", {})
    for key in ("Center", "Max", "Min"):
        if key in auto:
            auto[key]["Y"] = float(auto[key]["Y"]) + shift
    shape_path = f"Phive/ShapeParam/{name}_Body_0.phive__ShapeParam.bgyml"
    writer.files[shape_path] = byml.dumps(shape, sv, se)
    controller, cv, ce = _load(template.get_file(CONTROLLER).data)
    for entry in controller["ShapeNamePathAry"]:
        if entry["Name"] == "Body_Body":
            entry["FilePath"] = "Work/" + shape_path.replace(".bgyml", ".gyml")
    controller_path = f"Phive/ControllerSetParam/{name}.phive__ControllerSetParam.bgyml"
    writer.files[controller_path] = byml.dumps(controller, cv, ce)
    physics_path = f"Component/Physics/{name}.engine__component__PhysicsParam.bgyml"
    writer.files[physics_path] = byml.dumps(
        {"$parent": PHYSICS_BASE, "ControllerSetPath": "Work/" + controller_path.replace(".bgyml", ".gyml")},
        version, endian)
    return _file_ref(physics_path)


def floor_name(item):
    return "Obj_Rando_" + item.split("_", 1)[1]


def is_pickup(item):
    return item.startswith("Item_") or item == HEART_PIECE


def _pack_path(name):
    return f"Pack/Actor/{name}.pack.zs"


def _work_to_file(ref):
    return ref.lstrip("?").replace("Work/", "", 1).replace(".gyml", ".bgyml")


def _file_ref(path):
    return "?" + path


def _load(data):
    root, version, endian = byml.loads(bytes(data))
    return root, version, endian


def build(game, builder, items):
    items = sorted({i for i in items if is_pickup(i) and _pack_path(i) in game.files})
    if not items:
        return {}
    template = sarc.Sarc(game.read(_pack_path(TEMPLATE)))
    tables = {k: builder.placement(p) for k, p in TABLES.items()}
    rows = {k: {r["__RowId"]: r for r in t} for k, t in tables.items()}
    made = {}
    for item in items:
        name = floor_name(item)
        source = sarc.Sarc(game.read(_pack_path(item)))
        writer = sarc.SarcWriter.from_sarc(template)
        for f in template.get_files():
            if f.name.startswith("Actor/Obj_Rupee"):
                del writer.files[f.name]
        item_actor_path = f"Actor/{item}.engine__actor__ActorParam.bgyml"
        for f in source.get_files():
            if f.name.startswith("Actor/"):
                continue
            writer.files[f.name] = bytes(f.data)
        item_actor, version, endian = _load(source.get_file(item_actor_path).data)
        item_comp = item_actor["Components"]

        base_table_path = "GameParameter/GameParameterTable/Obj_Item_Base.engine__actor__GameParameterTable.bgyml"
        table, tv, te = _load(template.get_file(base_table_path).data)
        if "GameParameterTableRef" in item_comp:
            src = source.get_file(_work_to_file(item_comp["GameParameterTableRef"]))
            if src is not None:
                table["Components"].update(_load(src.data)[0].get("Components", {}))
        table_path = f"GameParameter/GameParameterTable/{name}.engine__actor__GameParameterTable.bgyml"
        writer.files[table_path] = byml.dumps(table, tv, te)

        comps = {k: item_comp[k] for k in FROM_ITEM if k in item_comp}
        comps["GameParameterTableRef"] = _file_ref(table_path)
        if "PouchContentRef" in comps:
            pouch_path = f"Component/PouchContentParam/{name}.game__component__PouchContentParam.bgyml"
            parent = "Work/" + _work_to_file(comps["PouchContentRef"]).replace(".bgyml", ".gyml")
            writer.files[pouch_path] = byml.dumps({"$parent": parent, "DefaultAutoGet": True}, version, endian)
            comps["PouchContentRef"] = _file_ref(pouch_path)
        comps["ASInfoRef"] = "?Component/ASInfo/Item_Obj.engine__component__ASInfo.bgyml"
        comps["PhysicsRef"] = _raised_physics(template, writer, name, _shift(rows["ActorInfo"][item]), version, endian)
        elink_path = f"Component/ELink/{name}.engine__component__ELinkParam.bgyml"
        writer.files[elink_path] = byml.dumps({"UserName": SPARKLE}, version, endian)
        comps["ELinkRef"] = _file_ref(elink_path)
        actor = {"$parent": ITEM_BASE, "Components": comps}
        writer.files[f"Actor/{name}.engine__actor__ActorParam.bgyml"] = byml.dumps(actor, version, endian)
        _, packed = writer.write()
        builder.put_new(_pack_path(name), bytes(packed), _pack_path(TEMPLATE))

        info = copy.deepcopy(rows["ActorInfo"][TEMPLATE])
        src_info = rows["ActorInfo"][item]
        for key in ("FmdbName", "ModelProjectName", "AnimationResources", "ModelAabbMax", "ModelAabbMin"):
            if key in src_info:
                info[key] = copy.deepcopy(src_info[key])
            else:
                info.pop(key, None)
        for key in [k for k in info if k.startswith("ModelVariation")]:
            info.pop(key)
        info["ActorName"] = src_info.get("ActorName", item)
        info["ELinkUserName"] = SPARKLE
        for key in ("InstanceHeapSize", "PreActorRenderInfoHeapSize"):
            info[key] = max(info.get(key, 0), src_info.get(key, 0)) * 2
        info["__RowId"] = name
        tables["ActorInfo"].append(info)

        game_info = {k: v for k, v in rows["GameActorInfo"].get(TEMPLATE, {}).items()
                     if k != "IsRespawn" and not k.startswith("ModelVariation")}
        game_info["__RowId"] = name
        tables["GameActorInfo"].append(game_info)

        if item in rows["PouchActorInfo"]:
            pouch = copy.deepcopy(rows["PouchActorInfo"][item])
            pouch["__RowId"] = name
            tables["PouchActorInfo"].append(pouch)
        made[item] = name
    for t in tables.values():
        t.sort(key=lambda r: r["__RowId"])
    return made


DISPLAY_TEMPLATE = "Item_Boomerang"
DISPLAY_FROM_TEMPLATE = ("ASInfoRef", "ASRef")
DISPLAY_FROM_ITEM = ("ActorNameRef", "GameParameterTableRef", "ModelInfoRef", "PouchContentRef", "AnimationRef")


def chest_name(item):
    return item + "_Get"


def needs_display(game, item):
    if not item.startswith("Item_") or _pack_path(item) not in game.files:
        return False
    actor, _, _ = _load(sarc.Sarc(game.read(_pack_path(item))).get_file(
        f"Actor/{item}.engine__actor__ActorParam.bgyml").data)
    return "ASRef" not in actor.get("Components", {})


def chest_displays(game, builder, items):
    if not items:
        return
    template = sarc.Sarc(game.read(_pack_path(DISPLAY_TEMPLATE)))
    base, version, endian = _load(template.get_file(
        f"Actor/{DISPLAY_TEMPLATE}.engine__actor__ActorParam.bgyml").data)
    tables = {k: builder.placement(p) for k, p in TABLES.items()}
    rows = {k: {r["__RowId"]: r for r in t} for k, t in tables.items()}
    for item in sorted(items):
        name = chest_name(item)
        source = sarc.Sarc(game.read(_pack_path(item)))
        writer = sarc.SarcWriter.from_sarc(template)
        del writer.files[f"Actor/{DISPLAY_TEMPLATE}.engine__actor__ActorParam.bgyml"]
        for f in source.get_files():
            if not f.name.startswith("Actor/"):
                writer.files[f.name] = bytes(f.data)
        item_comps = _load(source.get_file(f"Actor/{item}.engine__actor__ActorParam.bgyml").data)[0]["Components"]
        comps = {k: base["Components"][k] for k in DISPLAY_FROM_TEMPLATE if k in base["Components"]}
        comps.update({k: item_comps[k] for k in DISPLAY_FROM_ITEM if k in item_comps})
        anims = []
        pouch_name = "Pouch_" + item[len("Item_"):]
        if _pack_path(pouch_name) in game.files:
            pouch = sarc.Sarc(game.read(_pack_path(pouch_name)))
            for f in pouch.get_files():
                if not f.name.startswith("Actor/"):
                    writer.files[f.name] = bytes(f.data)
            pouch_comps = _load(pouch.get_file(
                f"Actor/{pouch_name}.engine__actor__ActorParam.bgyml").data)[0]["Components"]
            for k in ("AnimationRef", "GameParameterTableRef"):
                if k in pouch_comps:
                    comps[k] = pouch_comps[k]
            anim_file = comps.get("AnimationRef", "").lstrip("?")
            if anim_file in writer.files:
                anims = byml.loads(writer.files[anim_file])[0].get("AnimationResources", [])
        actor = {"$parent": base["$parent"], "Components": comps}
        writer.files[f"Actor/{name}.engine__actor__ActorParam.bgyml"] = byml.dumps(actor, version, endian)
        _, packed = writer.write()
        builder.put_new(_pack_path(name), bytes(packed), _pack_path(item))
        for key, table in tables.items():
            if item not in rows[key]:
                continue
            row = copy.deepcopy(rows[key][item])
            row["__RowId"] = name
            if key == "ActorInfo":
                row["ActorName"] = row.get("ActorName", item)
                shown = anims or rows[key][DISPLAY_TEMPLATE].get("AnimationResources", [])[:1]
                row["AnimationResources"] = list(shown) + [r for r in row.get("AnimationResources", [])
                                                           if r not in shown]
            table.append(row)
    for t in tables.values():
        t.sort(key=lambda r: r["__RowId"])
