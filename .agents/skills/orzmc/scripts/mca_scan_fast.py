# -*- coding: utf-8 -*-
"""Fast .mca scanner: extract command-block block_entities using a streaming NBT
walker that SKIPS huge sections/palette data (only the block_entities list is parsed).
Usage: python scan_fast.py <world_dir> <out_csv>
"""
import sys, os, csv, re, time, zlib, gzip

WORLD = ""
OUT = ""
CB_IDS = ("command_block", "chain_command_block", "repeating_command_block")

def find_region_dirs(world):
    dirs = []
    base = os.path.join(world, "dimensions", "minecraft")
    if os.path.isdir(base):
        for d in sorted(os.listdir(base)):
            reg = os.path.join(base, d, "region")
            if os.path.isdir(reg):
                dirs.append((d, reg))
    legacy = os.path.join(world, "region")
    if os.path.isdir(legacy):
        dirs.append(("overworld", legacy))
    return dirs

# ---------- minimal NBT reader (big-endian) ----------
def _i(data, pos, n):
    return int.from_bytes(data[pos:pos+n], 'big', signed=(n==8))

def _read_str(data, pos):
    ln = int.from_bytes(data[pos:pos+2], 'big')
    return data[pos+2:pos+2+ln].decode('utf-8', 'replace'), pos+2+ln

def _skip_payload(data, pos, t):
    """Skip one tag payload (name already consumed) of type t; return new pos."""
    if t == 1: return pos + 1
    if t == 2: return pos + 2
    if t == 3: return pos + 4
    if t == 4: return pos + 8
    if t == 5: return pos + 4
    if t == 6: return pos + 8
    if t == 7:  # byte array
        n = int.from_bytes(data[pos:pos+4], 'big'); return pos + 4 + n
    if t == 8:  # string
        ln = int.from_bytes(data[pos:pos+2], 'big'); return pos + 2 + ln
    if t == 9:  # list
        et = data[pos]; n = int.from_bytes(data[pos+1:pos+5], 'big')
        pos += 5
        for _ in range(n):
            pos = _skip_payload(data, pos, et)
        return pos
    if t == 10:  # compound
        return _skip_compound(data, pos)
    if t == 11:  # int array
        n = int.from_bytes(data[pos:pos+4], 'big'); return pos + 4 + 4*n
    if t == 12:  # long array
        n = int.from_bytes(data[pos:pos+4], 'big'); return pos + 4 + 8*n
    raise ValueError("unknown tag type %d" % t)

def _skip_compound(data, pos):
    while True:
        t = data[pos]; pos += 1
        if t == 0:
            return pos
        _, pos = _read_str(data, pos)
        pos = _skip_payload(data, pos, t)

def _parse_list_of_compounds(data, pos):
    """data[pos] is list tag payload start (after type+name). Returns list of dict."""
    et = data[pos]; n = int.from_bytes(data[pos+1:pos+5], 'big'); pos += 5
    out = []
    if et != 10:
        for _ in range(n):
            pos = _skip_payload(data, pos, et)
        return out, pos
    for _ in range(n):
        d, pos = _parse_compound(data, pos)
        out.append(d)
    return out, pos

def _parse_compound(data, pos):
    """Parse a compound into dict (str->value), stop at TAG_End. pos points at first field tag type."""
    d = {}
    while True:
        t = data[pos]; pos += 1
        if t == 0:
            return d, pos
        name, pos = _read_str(data, pos)
        if t == 1: v = data[pos]; pos += 1
        elif t == 2: v = int.from_bytes(data[pos:pos+2], 'big', signed=True); pos += 2
        elif t == 3: v = int.from_bytes(data[pos:pos+4], 'big', signed=True); pos += 4
        elif t == 4: v = int.from_bytes(data[pos:pos+8], 'big', signed=True); pos += 8
        elif t == 5: v = None; pos += 4
        elif t == 6: v = None; pos += 8
        elif t == 7:
            nn = int.from_bytes(data[pos:pos+4], 'big'); v=data[pos+4:pos+4+nn]; pos += 4+nn
        elif t == 8:
            ln = int.from_bytes(data[pos:pos+2], 'big'); v=data[pos+2:pos+2+ln].decode('utf-8','replace'); pos += 2+ln
        elif t == 9:
            v, pos = _parse_list_of_compounds(data, pos)
        elif t == 10:
            v, pos = _parse_compound(data, pos)
        elif t == 11:
            nn = int.from_bytes(data[pos:pos+4], 'big'); pos += 4+4*nn; v=None
        elif t == 12:
            nn = int.from_bytes(data[pos:pos+4], 'big'); pos += 4+8*nn; v=None
        else:
            raise ValueError("unknown tag type %d" % t)
        d[name] = v
    return d, pos

def extract_block_entities(data):
    """data = decompressed chunk NBT root bytes. Return list of block-entity dicts."""
    pos = 0
    if data[pos] != 10:  # must be compound root
        return []
    pos += 1
    _, pos = _read_str(data, pos)
    # iterate root compound
    while True:
        t = data[pos]; pos += 1
        if t == 0:
            return []
        name, pos = _read_str(data, pos)
        if name == "block_entities" and t == 9:
            lst, _ = _parse_list_of_compounds(data, pos)
            return lst
        pos = _skip_payload(data, pos, t)

def read_chunk_raw(path, off_sector):
    with open(path, 'rb') as f:
        f.seek(off_sector * 4096)
        head = f.read(5)
        if len(head) < 5:
            return None
        length = int.from_bytes(head[0:4], 'big')
        ctype = head[4]
        payload = f.read(length - 1)
    if ctype == 1:
        return gzip.decompress(payload)
    if ctype == 2:
        return zlib.decompress(payload)
    if ctype == 3:
        return payload
    return None

def clean_customname(v):
    s = str(v)
    m = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', s)
    if m:
        return m.group(1)
    return s

def main():
    WORLD = sys.argv[1]
    OUT = sys.argv[2]
    region_dirs = find_region_dirs(WORLD)
    if not region_dirs:
        print("No region dirs found", file=sys.stderr); return
    print("Dimensions:", [d for d, _ in region_dirs])
    total_cb = 0
    total_regions = 0
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fo:
        w = csv.writer(fo)
        w.writerow(["dimension","region_file","x","y","z","type_id","Command","auto","ConditionalMode",
                    "CustomName","powered","TrackOutput","successCount","LastOutput"])
        t0 = time.time()
        for dim, regdir in region_dirs:
            files = sorted(f for f in os.listdir(regdir) if f.endswith(".mca"))
            for fi, fn in enumerate(files):
                path = os.path.join(regdir, fn)
                total_regions += 1
                try:
                    with open(path, 'rb') as f:
                        loc = f.read(4096)
                    for i in range(1024):
                        b = loc[i*4:i*4+4]
                        off = int.from_bytes(b[0:3], 'big')
                        if off == 0:
                            continue
                        raw = read_chunk_raw(path, off)
                        if raw is None:
                            continue
                        bes = extract_block_entities(raw)
                        for be in bes:
                            bid = str(be.get("id", ""))
                            base = bid.split(":")[-1]
                            if base in CB_IDS:
                                total_cb += 1
                                cn = clean_customname(be.get("CustomName", "")) if be.get("CustomName") else ""
                                w.writerow([dim, fn, be.get("x",""), be.get("y",""), be.get("z",""), base,
                                            be.get("Command",""), be.get("auto",""), be.get("conditionMet",""),
                                            cn, be.get("powered",""), be.get("TrackOutput",""),
                                            be.get("SuccessCount",""), str(be.get("LastOutput",""))])
                except Exception as e:
                    print("ERROR region %s: %s" % (path, e), flush=True)
                if (fi + 1) % 400 == 0:
                    print("[%s] %d/%d regions | cum %d | CBs %d | %.0fs"
                          % (dim, fi+1, len(files), total_regions, total_cb, time.time()-t0), flush=True)
    print("DONE. total_regions=%d total_command_blocks=%d elapsed=%.1fs" % (total_regions, total_cb, time.time()-t0))
    print("Output:", OUT)

if __name__ == "__main__":
    main()
