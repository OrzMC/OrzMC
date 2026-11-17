#!/usr/bin/env python3
"""Streaming scan of command blocks in a Minecraft world (region files).

Only parses the block_entities lists of each chunk, skipping everything else.
Outputs a JSON list per region file: {file, count, blocks: [...]}
"""
import io, json, os, struct, sys, zlib
from concurrent.futures import ProcessPoolExecutor

TAG_END = 0; TAG_BYTE = 1; TAG_SHORT = 2; TAG_INT = 3; TAG_LONG = 4
TAG_FLOAT = 5; TAG_DOUBLE = 6; TAG_BYTE_ARRAY = 7; TAG_STRING = 8
TAG_LIST = 9; TAG_COMPOUND = 10; TAG_INT_ARRAY = 11; TAG_LONG_ARRAY = 12

def _read_utf(buf, pos):
    ln = struct.unpack_from('>H', buf, pos)[0]
    pos += 2
    return buf[pos:pos+ln].decode('utf-8', 'replace'), pos + ln

def _skip(buf, pos, t):
    """Advance pos past a tag of type t. Returns new pos."""
    if t == TAG_BYTE: return pos + 1
    if t == TAG_SHORT: return pos + 2
    if t == TAG_INT: return pos + 4
    if t == TAG_LONG: return pos + 8
    if t == TAG_FLOAT: return pos + 4
    if t == TAG_DOUBLE: return pos + 8
    if t == TAG_BYTE_ARRAY:
        n = struct.unpack_from('>i', buf, pos)[0]; return pos + 4 + n
    if t == TAG_STRING:
        ln = struct.unpack_from('>H', buf, pos)[0]; return pos + 2 + ln
    if t == TAG_INT_ARRAY:
        n = struct.unpack_from('>i', buf, pos)[0]; return pos + 4 + 4 * n
    if t == TAG_LONG_ARRAY:
        n = struct.unpack_from('>i', buf, pos)[0]; return pos + 4 + 8 * n
    if t == TAG_LIST:
        elem = buf[pos]; n = struct.unpack_from('>i', buf, pos+1)[0]
        pos += 5
        for _ in range(n):
            pos = _skip(buf, pos, elem)
        return pos
    if t == TAG_COMPOUND:
        while True:
            t2 = buf[pos]; pos += 1
            if t2 == TAG_END: return pos
            _, pos = _read_utf(buf, pos)
            pos = _skip(buf, pos, t2)
    raise ValueError(f'bad tag {t}')

def _parse_compound_entries(buf, pos):
    """Yield (name, tag_type, pos_at_payload) for each entry; caller skips/parses."""
    while True:
        t = buf[pos]; pos += 1
        if t == TAG_END:
            return
        name, pos = _read_utf(buf, pos)
        yield name, t, pos
        pos = _skip(buf, pos, t)

def _parse_block_entity(buf, pos):
    """Parse a full compound (small object) into a dict."""
    out = {}
    for name, t, p in _parse_compound_entries(buf, pos):
        if t == TAG_STRING:
            s, _ = _read_utf(buf, p); out[name] = s
        elif t == TAG_INT:
            out[name] = struct.unpack_from('>i', buf, p)[0]
        elif t == TAG_BYTE:
            out[name] = buf[p]
        elif t == TAG_LONG:
            out[name] = struct.unpack_from('>q', buf, p)[0]
        elif t == TAG_SHORT:
            out[name] = struct.unpack_from('>h', buf, p)[0]
        elif t == TAG_FLOAT:
            out[name] = struct.unpack_from('>f', buf, p)[0]
        elif t == TAG_DOUBLE:
            out[name] = struct.unpack_from('>d', buf, p)[0]
        elif t == TAG_BYTE_ARRAY:
            n = struct.unpack_from('>i', buf, p)[0]; out[name] = buf[p+4:p+4+n]
        elif t == TAG_INT_ARRAY:
            n = struct.unpack_from('>i', buf, p)[0]; out[name] = list(struct.unpack_from(f'>{n}i', buf, p+4))
        elif t == TAG_LONG_ARRAY:
            n = struct.unpack_from('>i', buf, p)[0]; out[name] = list(struct.unpack_from(f'>{n}q', buf, p+4))
        # lists of primitives inside BE are rare; keep it simple
        elif t == TAG_LIST:
            out[name] = f'<list>'
    return out

def _scan_chunk(buf):
    """Extract command blocks from one decompressed chunk payload."""
    found = []
    be_total = 0
    try:
        if not buf or buf[0] != TAG_COMPOUND:
            return None, str('root not compound'), 0
        pos = 1
        _, pos = _read_utf(buf, pos)  # root compound name (usually empty)
        # root compound entries
        for name, t, p in _parse_compound_entries(buf, pos):
            if name == 'block_entities' and t == TAG_LIST:
                elem = buf[p]; n = struct.unpack_from('>i', buf, p+1)[0]
                be_total += n
                q = p + 5
                for _ in range(n):
                    if elem == TAG_COMPOUND:
                        # list elements have NO type byte — payload starts directly
                        be = _parse_block_entity(buf, q)
                        bid = be.get('id', '')
                        if 'command_block' in bid:
                            found.append(be)
                        q = _skip(buf, q, elem)
                    else:
                        q = _skip(buf, q, elem)
            elif name == 'Level' and t == TAG_COMPOUND:
                # legacy pre-1.18: look inside for block_entities / TileEntities
                for name2, t2, p2 in _parse_compound_entries(buf, p):
                    if name2 in ('block_entities', 'TileEntities') and t2 == TAG_LIST:
                        elem = buf[p2]; n = struct.unpack_from('>i', buf, p2+1)[0]
                        be_total += n
                        q = p2 + 5
                        for _ in range(n):
                            if elem == TAG_COMPOUND:
                                be = _parse_block_entity(buf, q)
                                if 'command_block' in be.get('id', ''):
                                    found.append(be)
                                q = _skip(buf, q, elem)
                            else:
                                q = _skip(buf, q, elem)
    except Exception as e:
        return None, str(e), 0
    return found, None, be_total

def scan_region(path):
    """Scan a single region file. Returns (path, count, blocks, errors, be_total)."""
    blocks = []
    errors = 0
    be_total = 0
    try:
        with open(path, 'rb') as f:
            hdr = f.read(8192)
            if len(hdr) < 8192:
                return path, 0, [], 0, 0
            locs = struct.unpack_from('>1024I', hdr, 0)
            for i, loc in enumerate(locs):
                if loc == 0:
                    continue
                off = (loc >> 8) * 4096
                sectors = loc & 0xFF
                f.seek(off)
                raw = f.read(4)
                if len(raw) < 4:
                    continue
                (ln,) = struct.unpack('>I', raw)
                # Anvil: length includes the compression-type byte
                comp = f.read(1)[0] if ln > 0 else 0
                data = f.read(ln - 1)
                if len(data) < ln - 1:
                    continue
                try:
                    if comp == 1:  # gzip
                        payload = zlib.decompress(data, 16 + zlib.MAX_WBITS)
                    elif comp == 2:  # zlib
                        payload = zlib.decompress(data)
                    elif comp == 3:  # uncompressed
                        payload = data
                    else:
                        errors += 1
                        continue
                    found, err, cbe = _scan_chunk(payload)
                    if err:
                        errors += 1
                        continue
                    be_total += cbe
                    if found:
                        for be in found:
                            be['region'] = os.path.basename(path)
                            be['chunk_idx'] = i
                        blocks.extend(found)
                except Exception:
                    errors += 1
    except FileNotFoundError:
        return path, 0, [], 0, 0
    return path, len(blocks), blocks, errors, be_total

def scan_world(root, max_workers=8, min_size=0):
    region_files = []
    for dim in ('overworld', 'the_nether', 'the_end'):
        d = os.path.join(root, 'dimensions', 'minecraft', dim, 'region')
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.endswith('.mca'):
                    p = os.path.join(d, fn)
                    if min_size and os.path.getsize(p) < min_size:
                        continue
                    region_files.append((dim, p))
    print(f'total region files: {len(region_files)}', file=sys.stderr)
    dim_of = {p: dim for dim, p in region_files}
    total = 0
    errors = 0
    be_total = 0
    all_blocks = []
    if max_workers <= 1:
        # serial mode: minimal memory, no fork — safe on RAM-constrained hosts
        for dim, path in region_files:
            _, cnt, blks, errs, bet = scan_region(path)
            total += cnt
            errors += errs
            be_total += bet
            for b in blks:
                b['dim'] = dim
            all_blocks.extend(blks)
            if cnt:
                print(f'... {total} command blocks so far ({errors} errors)', file=sys.stderr)
        print(f'DONE: {total} command blocks, {be_total} block_entities, {errors} chunk errors', file=sys.stderr)
        return all_blocks
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        for path, cnt, blks, errs, bet in ex.map(scan_region, [p for _, p in region_files]):
            total += cnt
            errors += errs
            be_total += bet
            for b in blks:
                b['dim'] = dim_of[path]
            all_blocks.extend(blks)
            if total % 50 == 0:
                print(f'... {total} command blocks, {be_total} block_entities, {errors} errors', file=sys.stderr)
    print(f'DONE: {total} command blocks, {be_total} block_entities, {errors} chunk errors', file=sys.stderr)
    return all_blocks

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/minecraft-server/world')
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/cmdblocks.json'
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    min_size = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    blocks = scan_world(root, workers, min_size)
    with open(out, 'w') as f:
        json.dump(blocks, f, ensure_ascii=False, indent=1)
    # summary stats
    from collections import Counter
    types = Counter(b.get('id', '?') for b in blocks)
    print('by id:', dict(types))
    print('written to', out)
