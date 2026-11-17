import socket, struct, sys, os


def pack(req_id, ptype, body):
    payload = struct.pack('<ii', req_id, ptype) + body.encode('utf-8') + b'\x00\x00'
    return struct.pack('<i', len(payload)) + payload


def read_packet(s):
    raw = s.recv(4)
    if len(raw) < 4:
        raise ConnectionError('no length')
    (length,) = struct.unpack('<i', raw)
    data = b''
    while len(data) < length:
        chunk = s.recv(length - len(data))
        if not chunk:
            raise ConnectionError('closed')
        data += chunk
    rid, ptype = struct.unpack('<ii', data[:8])
    return rid, ptype, data[8:-2].decode('utf-8', 'replace')


def rcon(host, port, password, command, timeout=10):
    s = socket.create_connection((host, port), timeout=timeout)
    s.settimeout(timeout)
    s.sendall(pack(1, 3, password))
    rid, _, _ = read_packet(s)
    if rid == -1:
        raise PermissionError('RCON auth failed')
    s.sendall(pack(2, 2, command))
    _, _, body = read_packet(s)
    s.close()
    return body


if __name__ == '__main__':
    port = int(sys.argv[1])
    command = ' '.join(sys.argv[2:]) or 'list'
    print(rcon(os.environ.get('RCON_HOST', '127.0.0.1'), port, os.environ['RCON_PASSWORD'], command))
