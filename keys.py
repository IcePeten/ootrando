import collections
import copy
import io
import re

import byml
import evfl
from evfl.common import StringHolder
from evfl.container import Container
from evfl.entry_point import EntryPoint
from evfl.event import ActionEvent, Event, SubFlowEvent, SwitchEvent
from evfl.util import make_index, make_rindex

import places

SMALL_KEY = "Item_Dungeon_SmallKey"
BOSS_KEY = "Item_Dungeon_BossKey"
SMALL = "Rando_SmallKey_"
BOSS = "Rando_BossKey_"
MARK = "Rando_Mark_"
MARKED = "_Mark"
VIA = "_Via_"
ITEM = re.compile(r"^Rando_(Small|Boss)Key_([A-Za-z]+?)(?:_(\d+))?$")
VANILLA_SMALL = {"ForestTemple": 5, "FireTemple": 8, "WaterTemple": 6, "ShadowTemple": 5, "SpiritTemple": 5,
                 "BottomOfTheWell": 3, "GerudoTrainingGround": 9, "InsideGanonCastle": 2}
BOSS_DUNGEONS = ["ForestTemple", "FireTemple", "WaterTemple", "ShadowTemple", "SpiritTemple"]
COUNTERS = ["ForestTemple", "FireTemple", "WaterTemple", "ShadowTemple", "SpiritTemple", "BottomOfTheWell",
            "IceCavern", "GerudoTrainingGround", "InsideGanonCastle", "InsideTheDekuTree", "DodongoCavern",
            "InsideJabuJabuBelly", "GerudoFortress"]
FLOW = "Event/EventFlow/GetPouchContent.bfevfl.zs"
EVENT_TABLE = "RSDB/EventSetting.Product.111.rstbl.byml.zs"
ANALYZED_TABLE = "RSDB/GameAnalyzedEventInfo.Product.111.rstbl.byml.zs"
SMALL_CHEST = "Obj_TBox_A_01"
BIG_CHEST = "Obj_TBox_A_02"
CHESTS = {SMALL_CHEST: "Dm_SY_TreasureboxSmall", BIG_CHEST: "Dm_SY_Treasurebox"}
OPEN_FLOW = CHESTS[SMALL_CHEST]
TEMPLATE_ENTRY = {CHESTS[SMALL_CHEST]: "Success_MidoHouse", CHESTS[BIG_CHEST]: "Success"}
BIG = "_Big"
MSBT = "ActorMsg/PouchContent.msbt"
MESSAGE_FILE = "ActorMsg/PouchContent"
TALK_TEMPLATE = "EventFlowMsg/Dm_InsideJabu_Jabu_0030:Dm_InsideJabu_Jabu_0030_0019"
GENERIC_TEXT = {
    "Item_Dungeon_SmallKey_GetMessage": "You found a small key!",
    "Item_Dungeon_SmallKey_GetCaption": "Each key only fits the locks of its own dungeon.",
    "Item_Dungeon_BossKey_GetMessage": "You found a boss key!",
}


def small(area, n):
    return f"{SMALL}{area}_{n}"


def boss(area):
    return f"{BOSS}{area}"


def parse(item):
    m = ITEM.match(item or "")
    return (m.group(1) == "Small", m.group(2)) if m else None


def is_key(item):
    return parse(item) is not None


def token(item):
    is_small, area = parse(item)
    return f"{area}Key{item.rsplit('_', 1)[1]}" if is_small else f"{area}BossKey"


def place(area):
    return places.area_name(area).removeprefix("Inside ")


def name(item):
    is_small, area = parse(item)
    return f"{place(area)} {'Small Key' if is_small else 'Boss Key'}"


def spots(settings, locations, enabled):
    out = []
    for d in locations:
        if d["kind"] != "chest" or not enabled(settings, d):
            continue
        if d["item"] == SMALL_KEY and settings.small_keys == "anywhere" and d["area"] in VANILLA_SMALL:
            out.append(d)
        elif d["item"] == BOSS_KEY and settings.boss_keys == "anywhere" and d["area"] in BOSS_DUNGEONS:
            out.append(d)
    return out


def pool(found):
    counts = collections.Counter()
    items = []
    for d in found:
        if d["item"] == SMALL_KEY:
            counts[d["area"]] += 1
            items.append(small(d["area"], counts[d["area"]]))
        else:
            items.append(boss(d["area"]))
    return items


def rules(items):
    small_keys, boss_keys = {}, {}
    for item in items:
        is_small, area = parse(item)
        if is_small:
            small_keys.setdefault(area, []).append(token(item))
        else:
            boss_keys[area] = token(item)
    return small_keys, boss_keys


def bonus(found):
    shuffled = collections.Counter(d["area"] for d in found if d["item"] == SMALL_KEY)
    return {area: VANILLA_SMALL[area] - n for area, n in shuffled.items() if VANILLA_SMALL[area] > n}


def fits(loc, item, ok_event):
    if loc.data["kind"] != "chest" or not ok_event(loc.data.get("event")):
        return False
    is_small, area = parse(item)
    here = loc.data["area"]
    if here != area and loc.data.get("actor", "").removesuffix("_NoBake") not in CHESTS:
        return False
    return is_small or here == area or (here not in BOSS_DUNGEONS and here != "InsideGanonCastle")


def chest(item, here, gyaml=SMALL_CHEST):
    is_small, area = parse(item)
    drop = SMALL_KEY if is_small else BOSS_KEY
    if here == area:
        return drop, None
    event = f"Rando_{'Small' if is_small else 'Boss'}Key_{area}"
    if is_small and here in COUNTERS:
        event += f"_In_{here}"
    if gyaml.removesuffix("_NoBake") == BIG_CHEST:
        event += BIG
    return drop, event


def mark_event(hash_, gyaml):
    if gyaml.removesuffix("_NoBake") not in CHESTS:
        return None
    return f"{MARK}{hash_}" + (BIG if gyaml.removesuffix("_NoBake") == BIG_CHEST else "")


def mark_flag(hash_):
    return f"Rando_MapCheck_{hash_}"


def marked_key_event(event, hash_):
    big = event.endswith(BIG)
    return f"{event.removesuffix(BIG)}{MARKED}{hash_}" + (BIG if big else "")


def _flow_for(event):
    return CHESTS[BIG_CHEST if event.endswith(BIG) else SMALL_CHEST]


def _message_label(event):
    event = event.removesuffix(BIG)
    is_small = event.startswith("Rando_SmallKey_")
    area = event.split("_")[2]
    return f"Rando_{'SmallKey' if is_small else 'BossKey'}_{area}", is_small, area


def messages(events):
    out = {}
    for event in events:
        label, is_small, area = _message_label(event)
        where = place(area)
        where = where if where.startswith("Ganon") else f"the {where}"
        out[label] = (f"This small key opens a door in {where}." if is_small
                      else f"This is the Boss Key for {where}!")
    return {MSBT: out} if out else {}


def _action(actor, action, params, nxt=None):
    ev = Event()
    ev.data = ActionEvent()
    ev.data.actor = make_rindex(actor)
    ev.data.actor_action = make_rindex(action)
    ev.data.params = params
    ev.data.nxt = make_index(nxt)
    return ev


def _find_action(actor, name):
    for holder in actor.actions:
        if holder.v == name:
            return holder
    holder = StringHolder(name)
    actor.actions.append(holder)
    return holder


def _find_query(actor, name):
    for holder in actor.queries:
        if holder.v == name:
            return holder
    holder = StringHolder(name)
    actor.queries.append(holder)
    return holder


def _if_false(actor, query, flag, nxt, otherwise=None):
    ev = Event()
    ev.data = SwitchEvent()
    ev.data.actor = make_rindex(actor)
    ev.data.actor_query = make_rindex(query)
    params = Container()
    params.data.update({"Index": -1, "GameDataName": flag})
    ev.data.params = params
    ev.data.cases = {0: make_index(nxt)}
    if otherwise is not None:
        ev.data.cases[1] = make_index(otherwise)
    return ev


def _mark_chain(data, set_bool, is_bool, own, others, spot, cont=None):
    chain = []
    if spot != own:
        chain.append(_action(data, set_bool, _game_data(spot, False), cont))
        for flag in reversed(others):
            chain.insert(0, _if_false(data, is_bool, flag, chain[0], cont))
    chain.insert(0, _action(data, set_bool, _game_data(own, False), chain[0] if chain else cont))
    return chain


def wrapped_event(hash_, original):
    return f"{MARK}{hash_}{VIA}{original}"


def _flow_name(row):
    return row["FlowchartFileName"].rsplit("/", 1)[1].removesuffix(".evfc")


_ROWS = {}


def can_wrap(game, original):
    if id(game) not in _ROWS:
        _ROWS[id(game)] = {r["__RowId"]: r for r in byml.loads(game.read(EVENT_TABLE))[0]}
    row = _ROWS[id(game)].get(original)
    return row is not None and _flow_name(row) not in CHESTS.values()


def wrap(game, builder, events, spots=None):
    if not events:
        return
    spots = spots or {}
    rows = {r["__RowId"]: r for r in builder.placement(EVENT_TABLE)}
    by_flow = collections.defaultdict(list)
    for event in events:
        by_flow[_flow_name(rows[event.split(VIA, 1)[1]])].append(event)
    src = evfl.EventFlow()
    src.read(game.read(f"Event/EventFlow/{OPEN_FLOW}.bfevfl.zs"))
    template = next(a for a in src.flowchart.actors if str(a.identifier) == "GameDataActor")
    for flowchart, mine in sorted(by_flow.items()):
        path = f"Event/EventFlow/{flowchart}.bfevfl.zs"
        f = evfl.EventFlow()
        f.read(builder.current(path))
        fc = f.flowchart
        data = next((a for a in fc.actors if str(a.identifier) == "GameDataActor"), None)
        if data is None:
            data = copy.deepcopy(template)
            data.actions, data.queries = [], []
            fc.actors.append(data)
        set_bool = _find_action(data, "EventTriggerSetGameDataBool")
        is_bool = _find_query(data, "EventQueryIsGameDataBool")
        entries = {e.name: e for e in fc.entry_points}
        for event in sorted(mine):
            hash_, original = event.removeprefix(MARK).split(VIA, 1)
            entry = entries[rows[original]["EntryPointName"]]
            own = mark_flag(hash_)
            others, spot = spots.get(own, ([], own))
            chain = _mark_chain(data, set_bool, is_bool, own, others, spot, entry.main_event.v)
            name = f"Success_{event}"
            for n, ev in enumerate(chain):
                ev.name = f"{name}_{n}"
                fc.events.append(ev)
            new = EntryPoint(name)
            new.main_event = make_index(chain[0])
            new.variable_defs = entry.variable_defs
            new._sub_flow_event_indices = list(entry._sub_flow_event_indices)
            fc.entry_points.append(new)
        builder.put(path, _write(f))
    for table in (EVENT_TABLE, ANALYZED_TABLE):
        table_rows = builder.placement(table)
        have = {r["__RowId"]: r for r in table_rows}
        for event in events:
            original = event.split(VIA, 1)[1]
            if event in have or original not in have:
                continue
            row = copy.deepcopy(have[original])
            row["__RowId"] = event
            if "EntryPointName" in row:
                row["EntryPointName"] = f"Success_{event}"
            table_rows.append(row)
        table_rows.sort(key=lambda r: r["__RowId"])


def _sub(flowchart, entry, nxt=None):
    ev = Event()
    ev.data = SubFlowEvent()
    ev.data.res_flowchart_name = flowchart
    ev.data.entry_point_name = entry
    ev.data.nxt = make_index(nxt)
    return ev


def _add_entry(fc, name, chain):
    for n, ev in enumerate(chain):
        ev.name = f"{name}_{n}"
        fc.events.append(ev)
    entry = EntryPoint(name)
    entry.main_event = make_index(chain[0])
    entry._sub_flow_event_indices = [fc.events.index(ev) for ev in chain if isinstance(ev.data, SubFlowEvent)]
    fc.entry_points.append(entry)


def _write(f):
    out = io.BytesIO()
    f.write(out)
    return out.getvalue()


def _talker(game):
    f = evfl.EventFlow()
    f.read(game.read(FLOW))
    fc = f.flowchart
    talker = next(a for a in fc.actors if str(a.identifier) == "SystemTextNPC")
    talk = next(ev for ev in fc.events if isinstance(ev.data, ActionEvent) and ev.data.params is not None
                and ev.data.actor.v is talker and str(ev.data.params.data.get("MessageId", "")) == TALK_TEMPLATE)
    actor = copy.deepcopy(talker)
    actor.actions = [StringHolder(talk.data.actor_action.v.v)]
    actor.queries = []
    return actor, talk.data.params


def _game_data(name, value):
    params = Container()
    params.data.update({"GameDataName": name, "Value": value, "Index": -1})
    return params


def _open_flow(game, flowchart, events, spots):
    f = evfl.EventFlow()
    f.read(game.read(f"Event/EventFlow/{flowchart}.bfevfl.zs"))
    fc = f.flowchart
    data = next(a for a in fc.actors if str(a.identifier) == "GameDataActor")
    add_int = _find_action(data, "EventTriggerAddOrSubGameDataInt")
    set_bool = _find_action(data, "EventTriggerSetGameDataBool")
    is_bool = _find_query(data, "EventQueryIsGameDataBool")
    talker, talk_params = _talker(game)
    fc.actors.append(talker)
    template = []
    ev = next(e for e in fc.entry_points if e.name == TEMPLATE_ENTRY[flowchart]).main_event.v
    while not isinstance(ev.data, SubFlowEvent):
        template.append(ev)
        ev = ev.data.nxt.v
    template.append(ev)
    for event in sorted(events):
        base = event.removesuffix(BIG)
        if base.startswith(MARK):
            own = mark_flag(base.removeprefix(MARK))
            others, spot = spots.get(own, ([], own))
            after = _mark_chain(data, set_bool, is_bool, own, others, spot)
        else:
            marked = None
            if MARKED in base:
                base, marked = base.split(MARKED)
            label, is_small, area = _message_label(event)
            params = copy.deepcopy(talk_params)
            params.data["MessageId"] = f"{MESSAGE_FILE}:{label}"
            after = [_action(talker, talker.actions[0], params)]
            here = base.split("_In_")[1] if "_In_" in base else None
            if here:
                after.insert(0, _action(data, add_int, _game_data(f"DungeonInfo.{here}.SmallKeyNum", -1), after[0]))
            if is_small:
                after.insert(0, _action(data, add_int, _game_data(f"DungeonInfo.{area}.SmallKeyNum", 1), after[0]))
            else:
                after.insert(0, _action(data, set_bool, _game_data(f"DungeonInfo.{area}.IsGetBossKey", True),
                                        after[0]))
            if marked:
                own = mark_flag(marked)
                others, spot = spots.get(own, ([], own))
                tail = _mark_chain(data, set_bool, is_bool, own, others, spot)
                after[-1].data.nxt = make_index(tail[0])
                after += tail
        name = f"Success_{event}"
        for n, ev in enumerate(after):
            ev.name = f"{name}_After{n}"
        fc.events += after
        chain = []
        for src in template:
            ev = copy.copy(src)
            ev.data = copy.copy(src.data)
            ev.data.params = copy.deepcopy(src.data.params)
            chain.append(ev)
        for ev, nxt in zip(chain, chain[1:] + [after[0]]):
            ev.data.nxt = make_index(nxt)
        _add_entry(fc, name, chain)
    return _write(f)


def build(game, builder, events, spots=None):
    for flowchart in sorted({_flow_for(e) for e in events}):
        mine = [e for e in events if _flow_for(e) == flowchart]
        builder.put(f"Event/EventFlow/{flowchart}.bfevfl.zs", _open_flow(game, flowchart, mine, spots or {}))
    for table in (EVENT_TABLE, ANALYZED_TABLE):
        rows = builder.placement(table)
        have = {r["__RowId"]: r for r in rows}
        for event in events:
            if event in have:
                continue
            row = copy.deepcopy(have[_flow_for(event)])
            row["__RowId"] = event
            if "EntryPointName" in row:
                row["EntryPointName"] = f"Success_{event}"
            rows.append(row)
        rows.sort(key=lambda r: r["__RowId"])
