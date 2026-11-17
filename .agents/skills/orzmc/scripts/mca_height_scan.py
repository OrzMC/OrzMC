#!/usr/bin/env python3
"""Parse Minecraft region files (.mca) and inspect chunk vertical extents.

Self-contained: minimal NBT reader + MCA reader. No third-party deps.

Usage:
  python mca_scan.py probe <region_file>      # dump one region's chunk sections summary
  python mca_scan.py scan <dim_dir> [out.csv] # scan whole dimension
"""
import os
import sys
import json
import zlib
import gzip
import struct
import glob

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

# Default section index ranges per dimension (1.17+). section index Y maps to
# blocks [Y*16 + min_y, Y*16+15+min_y] where min_y is per-dimension default.
# Overworld/Nether: min_y=-64, max_y=319  -> sections 0..23 (384 blocks)
# End:              min_y=0,   max_y=255  -> sections 0..15 (256 blocks)
DEFAULT_RANGES = {
    "overworld": (0, 23),
    "the_nether": (0, 23),
    "the_end": (0, 15),
}


class NBTParser:
    """Very small NBT reader returning python-native structures.

    Compound -> dict, List -> list, numeric arrays -> list/bytes.
    """

    def __init__(self, data, offset=0):
        self.data = data
        self.off = offset

    def _read(self, n):
        v = self.data[self.off:self.off + n]
        if len(v) < n:
            raise ValueError("unexpected EOF in NBT")
        self.off += n
        return v

    def _u8(self):
        return self._read(1)[0]

    def _u16(self):
        return struct.unpack(">H", self._read(2))[0]

    def _u32(self):
        return struct.unpack(">I", self._read(4))[0]

    def _u64(self):
        return struct.unpack(">Q", self._read(8))[0]

    def _i8(self):
        return struct.unpack(">b", self._read(1))[0]

    def _i16(self):
        return struct.unpack(">h", self._read(2))[0]

    def _i32(self):
        return struct.unpack(">i", self._read(4))[0]

    def _i64(self):
        return struct.unpack(">q", self._read(8))[0]

    def _f32(self):
        return struct.unpack(">f", self._read(4))[0]

    def _f64(self):
        return struct.unpack(">d", self._read(8))[0]

    def _string(self):
        n = self._u16()
        return self._read(n).decode("utf-8", errors="replace")

    def parse(self):
        t = self._u8()
        if t != TAG_COMPOUND:
            raise ValueError("root is not a compound (type %d)" % t)
        name = self._string()  # root name (often empty)
        return self._compound(), name

    def _compound(self):
        out = {}
        while True:
            t = self._u8()
            if t == TAG_END:
                break
            name = self._string()
            out[name] = self._value(t)
        return out

    def _value(self, t):
        if t == TAG_BYTE:
            return self._i8()
        if t == TAG_SHORT:
            return self._i16()
        if t == TAG_INT:
            return self._i32()
        if t == TAG_LONG:
            return self._i64()
        if t == TAG_FLOAT:
            return self._f32()
        if t == TAG_DOUBLE:
            return self._f64()
        if t == TAG_BYTE_ARRAY:
            return self._read(self._u32())
        if t == TAG_STRING:
            return self._string()
        if t == TAG_LIST:
            et = self._u8()
            n = self._u32()
            if et == TAG_END:
                return []
            return [self._value(et) for _ in range(n)]
        if t == TAG_COMPOUND:
            return self._compound()
        if t == TAG_INT_ARRAY:
            n = self._u32()
            return list(struct.unpack(">%di" % n, self._read(4 * n)))
        if t == TAG_LONG_ARRAY:
            n = self._u32()
            return list(struct.unpack(">%dq" % n, self._read(8 * n)))
        raise ValueError("unknown tag type %d" % t)


def read_region_file(path):
    """Yield (x, z, nbt_dict) for every chunk present in a region file."""
    with open(path, "rb") as f:
        header = f.read(8192)
        if len(header) < 8192:
            return
        locations = struct.unpack(">1024i", header[0:4096])
        for idx, loc in enumerate(locations):
            if loc == 0:
                continue
            sector_off = (loc >> 8) & 0xFFFFFF
            sector_count = loc & 0xFF
            if sector_count <= 0:
                continue
            x = idx & 0x1F
            z = (idx >> 5) & 0x1F
            f.seek(sector_off * 4096)
            raw = f.read(sector_count * 4096)
            if len(raw) < 5:
                continue
            (length,) = struct.unpack(">I", raw[0:4])
            comp = raw[4]
            payload = raw[5:5 + length]
            try:
                if comp == 1:
                    data = gzip.decompress(payload)
                elif comp == 2:
                    data = zlib.decompress(payload)
                elif comp == 3:
                    data = payload  # uncompressed
                else:
                    continue
            except Exception:
                continue
            try:
                nbt, _ = NBTParser(data).parse()
            except Exception:
                continue
            yield x, z, nbt


def find_sections(chunk):
    """Locate section list in a chunk NBT (handles 1.17 Level.Sections and 1.18+ root sections)."""
    if isinstance(chunk, dict):
        if "sections" in chunk:
            secs = chunk["sections"]
            if isinstance(secs, list):
                return secs
        lvl = chunk.get("Level")
        if isinstance(lvl, dict):
            secs = lvl.get("Sections")
            if isinstance(secs, list):
                return secs
    return None


def section_info(sec):
    """Return (y, nonempty) for a section compound."""
    if not isinstance(sec, dict):
        return None
    y = sec.get("Y")
    if y is None:
        return None
    # 1.18+ block_states present means the section has some block data.
    # 1.17 used "Blocks" byte array. A section that exists on disk in 1.18
    # implies it is non-empty (empty sections are omitted), but verify anyway.
    has = False
    bs = sec.get("block_states")
    if isinstance(bs, dict):
        pal = bs.get("palette")
        if isinstance(pal, list):
            if len(pal) > 1:
                has = True
            elif len(pal) == 1:
                st = pal[0]
                if isinstance(st, dict):
                    name = st.get("Name", "")
                    has = (name != "minecraft:air")
    if sec.get("Blocks") is not None:
        has = True
    if sec.get("BlockStates") is not None:
        has = True
    return y, has


def scan_dimension(region_dir, dim_name, out_csv=None):
    lo, hi = DEFAULT_RANGES[dim_name]
    region_files = sorted(glob.glob(os.path.join(region_dir, "r.*.mca")))
    total_chunks = 0
    affected_chunks = 0
    affected_sections = 0
    affected_section_vol = 0
    chunks_with_air_only = 0
    y_hist = {}
    # per region file stats
    region_stats = []
    for rpath in region_files:
        base = os.path.basename(rpath)
        parts = base[2:-4].split(".")
        rx, rz = int(parts[0]), int(parts[1])
        aff_chunks = set()
        aff_secs = 0
        aff_vol = 0
        for x, z, nbt in read_region_file(rpath):
            total_chunks += 1
            secs = find_sections(nbt)
            if secs is None:
                continue
            chunk_aff = False
            chunk_secs = 0
            chunk_vol = 0
            chunk_air_only = 0
            for sec in secs:
                info = section_info(sec)
                if info is None:
                    continue
                y, has = info
                if y < lo or y > hi:
                    y_hist[y] = y_hist.get(y, 0) + 1
                    if has:
                        chunk_secs += 1
                        chunk_vol += 16 * 16 * 16
                        chunk_aff = True
                    else:
                        # air-only out-of-range section still counts as touched height
                        chunk_air_only += 1
                        chunk_aff = True
            if chunk_aff:
                affected_chunks += 1
                affected_sections += chunk_secs
                affected_section_vol += chunk_vol
                chunks_with_air_only += chunk_air_only
                aff_chunks.add((x, z))
                aff_secs += chunk_secs
                aff_vol += chunk_vol
        if aff_chunks:
            region_stats.append((rx, rz, len(aff_chunks), aff_secs, aff_vol))
    return {
        "dim": dim_name,
        "regions": len(region_files),
        "chunks": total_chunks,
        "affected_chunks": affected_chunks,
        "affected_sections": affected_sections,
        "affected_vol": affected_section_vol,
        "air_only": chunks_with_air_only,
        "y_hist": y_hist,
        "region_stats": region_stats,
    }


def probe_region(path):
    print("== probing %s" % path)
    count = 0
    yset = set()
    seen = 0
    for x, z, nbt in read_region_file(path):
        seen += 1
        secs = find_sections(nbt)
        if secs is None:
            continue
        count += 1
        for sec in secs:
            info = section_info(sec)
            if info:
                yset.add(info[0])
    print("chunks in file: %d" % seen)
    print("chunks with sections: %d" % count)
    print("section Y values seen: %s" % sorted(yset))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "help"
    if mode == "probe":
        probe_region(sys.argv[2])
    elif mode == "scan":
        dim_dir = sys.argv[2]
        dim_name = sys.argv[3]
        res = scan_dimension(dim_dir, dim_name)
        print(json_dumps(res))
    else:
        print(__doc__)
