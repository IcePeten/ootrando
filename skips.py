import io

import evfl
from evfl.event import ActionEvent, ForkEvent, JoinEvent, SubFlowEvent, SwitchEvent
from evfl.util import make_index

FAREWELL_FLOW = "Goto_HyruleCastle"
FAREWELL = ["Dm_Kokiri_0150", "Dm_Kokiri_0155"]
FAREWELL_FLAGS = {
    "HavePlayedEvent.Dm_Kokiri_0150": True,
    "HavePlayedEvent.Dm_Kokiri_0155": True,
}


def _flow(game, name):
    f = evfl.EventFlow()
    f.read(game.read(f"Event/EventFlow/{name}.bfevfl.zs"))
    return f


def _write(f):
    out = io.BytesIO()
    f.write(out)
    return out.getvalue()


def _redirect(fc, old, new):
    for ev in fc.events:
        d = ev.data
        if isinstance(d, (ActionEvent, SubFlowEvent, JoinEvent)) and d.nxt.v is old:
            d.nxt = make_index(new)
        elif isinstance(d, SwitchEvent):
            for case, target in list(d.cases.items()):
                if target.v is old:
                    d.cases[case] = make_index(new)
        elif isinstance(d, ForkEvent):
            d.forks = [make_index(new) if b.v is old else b for b in d.forks]
    for entry in fc.entry_points:
        if entry.main_event.v is old:
            entry.main_event = make_index(new)


def _transition(fc, event_name):
    for ev in fc.events:
        d = ev.data
        if (isinstance(d, ActionEvent) and d.actor_action.v.v == "EventTransition" and d.params
                and str(d.params.data.get("EventName")) == event_name):
            return ev
    raise KeyError(event_name)


def _drop_transition(fc, event_name):
    ev = _transition(fc, event_name)
    _redirect(fc, ev, ev.data.nxt.v)


def _without(game, flow, *event_names):
    f = _flow(game, flow)
    for name in event_names:
        _drop_transition(f.flowchart, name)
    return _write(f)


def build(game, builder, skip_farewell=True):
    if not skip_farewell:
        return {}
    builder.put(f"Event/EventFlow/{FAREWELL_FLOW}.bfevfl.zs", _without(game, FAREWELL_FLOW, *FAREWELL))
    return dict(FAREWELL_FLAGS)
