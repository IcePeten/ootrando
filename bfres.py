import struct

BONE_STRIDE = 88
INV_MATRIX = 48


def _name(d, ptr):
    n = struct.unpack_from("<H", d, ptr)[0]
    return d[ptr + 2:ptr + 2 + n].decode("utf-8", "replace")


def skeleton(d):
    i = d.find(b"FSKL")
    _, _, bone_array, mtx_list, inv = struct.unpack_from("<IQQQQ", d, i + 4)
    count, smooth, rigid = struct.unpack_from("<HHH", d, i + 0x38)
    bones = []
    for b in range(count):
        o = bone_array + b * BONE_STRIDE
        index, parent, smi, rmi = struct.unpack_from("<HhhH", d, o + 32)
        bones.append({"offset": o, "name": _name(d, struct.unpack_from("<Q", d, o)[0]), "index": index,
                      "parent": parent, "smooth": smi, "rigid": -1 if rmi == 0xFFFF else rmi,
                      "scale": struct.unpack_from("<3f", d, o + 48), "rot": struct.unpack_from("<4f", d, o + 60),
                      "pos": struct.unpack_from("<3f", d, o + 76)})
    return {"bones": bones, "smooth": smooth, "rigid": rigid, "mtx_offset": mtx_list, "inv_offset": inv,
            "mtx": list(struct.unpack_from(f"<{smooth + rigid}H", d, mtx_list))}


def pin_bones(data, names, target):
    d = bytearray(data)
    skel = skeleton(d)
    by_name = {b["name"]: b for b in skel["bones"]}
    anchor = by_name[target]
    src = skel["inv_offset"] + anchor["smooth"] * INV_MATRIX
    inverse = bytes(d[src:src + INV_MATRIX])
    for name in names:
        slot = by_name[name]["smooth"]
        if slot < 0:
            continue
        struct.pack_into("<H", d, skel["mtx_offset"] + slot * 2, anchor["index"])
        dst = skel["inv_offset"] + slot * INV_MATRIX
        d[dst:dst + INV_MATRIX] = inverse
    return bytes(d)
