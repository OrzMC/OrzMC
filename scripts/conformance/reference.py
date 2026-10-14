#!/usr/bin/env python3
"""规范参考适配器（spec-owned，仅标准库）。

把 `docs/spec/**` 的**纯计划**语义编码成可执行参照：给定 fixture 的 `given`，
返回规范期望的输出。它**不是产品实现**——Python/Swift 的适配器应复制同一语义。

协议：stdin 读一个请求 JSON（即 fixture 的 given + id/specVersion），
stdout 写一个响应 JSON：{"ok":true,"data":...} 或 {"ok":false,"code":...,"message":...}。
未实现的操作返回 code=E_UNSUPPORTED_OP（运行器记为 SKIP）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

# 快照定位：优先 env（供子模块适配器用），否则回退到本仓库 fixtures。
FIXTURES = Path(os.environ.get("ORZMC_CONFORMANCE_FIXTURES") or
                Path(__file__).resolve().parents[2] / "docs" / "spec" / "fixtures")
RANGE_THRESHOLD = 8 * 1024 * 1024
RANGE_PARTS = 4
FUTURE_SKEW = 300
DEFAULT_TTL = 86400
CLIENT_CAPABLE = ("vanilla", "fabric", "forge")
SERVER_JAR = {"vanilla": "server.jar", "paper": "paper-{v}.jar",
              "forge": "forge-{v}.jar", "fabric": "fabric-server-launch.jar"}


def ok(data):
    return {"ok": True, "data": data}


def err(code, message):
    return {"ok": False, "code": code, "message": message}


def load(rel):
    with open(FIXTURES / rel, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- layout
def layout(root, version, gtype=None, java_major=None, object_sha1=None, windows=False):
    v = f"{root}/versions/{version}"
    c = f"{v}/client"
    out = {
        "root": root,
        "versionsDir": f"{root}/versions",
        "versionDir": v,
        "clientDir": c,
        "clientAssetsDir": f"{c}/assets",
        "clientIndexesDir": f"{c}/assets/indexes",
        "clientObjectsDir": f"{c}/assets/objects",
        "clientLibrariesDir": f"{c}/libraries",
        "clientNativesDir": f"{c}/natives",
        "clientJarPath": f"{c}/{version}.jar",
        "clientProfilesDir": f"{c}/profiles",
        "javaDir": f"{root}/java",
        "cacheDir": f"{root}/cache",
        "versionManifestPath": f"{root}/cache/version_manifest.json",
        "versionJsonsDir": f"{root}/cache/versions",
        "downloadTmpDir": f"{root}/cache/download_tmp",
        "backupDir": f"{root}/backup",
    }
    if gtype:
        s = f"{v}/server/{gtype}"
        name = SERVER_JAR[gtype].format(v=version)
        out.update({
            "serverDir": s,
            "serverJarName": name,
            "serverJarPath": f"{s}/{name}",
            "serverEulaPath": f"{s}/eula.txt",
            "serverPropertiesPath": f"{s}/server.properties",
            "serverPluginsDir": f"{s}/plugins",
            "serverWorldDir": f"{s}/world",
        })
    if java_major is not None:
        out["javaMajorDir"] = f"{root}/java/{java_major}"
        out["javaExecutable"] = f"{root}/java/{java_major}/bin/java" + (".exe" if windows else "")
    if object_sha1:
        out["clientObjectPath"] = f"{c}/assets/objects/{object_sha1[:2]}/{object_sha1}"
    return out


def op_plan_layout(req):
    windows = (req.get("platform") or {}).get("os") == "windows"
    return ok(layout(req["root"], req["version"], req.get("type"),
                     req.get("javaMajor"), req.get("objectSha1"), windows))


# ---------------------------------------------------------------- rules
def rule_match(rule, plat, features):
    os_ = rule.get("os")
    if os_:
        if os_.get("name") and os_["name"] != plat["os"]:
            return False
        if os_.get("arch") and os_["arch"] != plat["arch"]:
            return False
    feats = rule.get("features")
    if feats:
        for k, v in feats.items():
            if bool(features.get(k)) != bool(v):
                return False
    return True


def rules_allow(rules, plat, features):
    if not rules:
        return True
    allowed = False
    for r in rules:
        if rule_match(r, plat, features):
            allowed = r.get("action") == "allow"
    return allowed


def collect(entries, plat, features):
    out = []
    for e in entries:
        if isinstance(e, str):
            out.append(e)
        elif isinstance(e, dict) and rules_allow(e.get("rules"), plat, features):
            val = e.get("value")
            if isinstance(val, list):
                out += val
            elif val is not None:
                out.append(val)
    return out


def subst(arg, tokens):
    return re.sub(r"\$\{(\w+)\}", lambda m: tokens.get(m.group(1), m.group(0)), arg)


# ---------------------------------------------------------------- client launch
def op_client_launch(req):
    gtype = req.get("type", "vanilla")
    if gtype not in CLIENT_CAPABLE:
        return err("E_UNSUPPORTED_TYPE", f"类型 {gtype} 不支持客户端")
    snap = load(req["snapshot"])
    plat = req["platform"]
    opts = req.get("options") or {}
    features = opts.get("features") or {}
    root, version = req["root"], req["version"]
    major = (snap.get("javaVersion") or {}).get("majorVersion", 8)
    exe = f"{root}/java/{major}/bin/java" + (".exe" if plat["os"] == "windows" else "")
    lay = layout(root, version)
    client_dir, libs_dir = lay["clientDir"], lay["clientLibrariesDir"]

    cp = []
    for lib in snap.get("libraries", []):
        if not rules_allow(lib.get("rules"), plat, features):
            continue
        art = (lib.get("downloads") or {}).get("artifact")
        if art and art.get("path"):
            cp.append(f"{libs_dir}/{art['path']}")
    cp.append(lay["clientJarPath"])
    sep = ";" if plat["os"] == "windows" else ":"

    tokens = {
        "natives_directory": lay["clientNativesDir"],
        "launcher_name": "orzmc",
        "launcher_version": "0.1",
        "classpath": sep.join(cp),
        "classpath_separator": sep,
        "library_directory": libs_dir,
        "auth_player_name": opts.get("username") or "guest",
        "version_name": version,
        "game_directory": client_dir,
        "assets_root": lay["clientAssetsDir"],
        "assets_index_name": (snap.get("assetIndex") or {}).get("id", ""),
        "auth_uuid": "00000000000000000000000000000000",
        "auth_access_token": "0",
        "user_type": "legacy",
        "version_type": snap.get("type", "release"),
        "clientid": "",
        "auth_xuid": "",
    }
    if "arguments" in snap:
        jvm = collect(snap["arguments"].get("jvm", []), plat, features)
        game = collect(snap["arguments"].get("game", []), plat, features)
    else:  # legacy
        jvm = ["-Djava.library.path=${natives_directory}"]
        game = (snap.get("minecraftArguments") or "").split()
    # 沿用 Python 现行：classpath 由 "-cp <joined>" 显式装配，jvmArgs 不含 -cp/${classpath}
    jvm = [a for a in jvm if a != "-cp" and "${classpath}" not in a]
    jvm = [subst(a, tokens) for a in jvm]
    game = [subst(a, tokens) for a in game]
    return ok({
        "executable": exe,
        "cwd": client_dir,
        "mainClass": snap.get("mainClass"),
        "jvmArgs": jvm,
        "gameArgs": game,
        "classpath": cp,
        "classpathString": sep.join(cp),
        "memory": {"min": opts.get("minMem") or "512M", "max": opts.get("maxMem") or "2G"},
        "tokens": tokens,
        "features": features,
    })


# ---------------------------------------------------------------- java
def op_required_java(req):
    snap = load(req["snapshot"])
    major = (snap.get("javaVersion") or {}).get("majorVersion", 8)
    return ok({"majorVersion": major, "distribution": "temurin", "runtimeKind": "jre"})


# ---------------------------------------------------------------- verify
def op_verify(req):
    data = (req.get("dataUtf8") or "").encode("utf-8")
    digest = hashlib.new(req.get("hashType", "sha1"), data).hexdigest()
    return ok({"valid": digest == (req.get("expectedSha1") or "").lower()})


# ---------------------------------------------------------------- cache
def op_cache(req):
    if req.get("refresh"):
        return ok({"action": "refresh"})
    age = req["now"] - req["mtime"]
    ttl = req.get("ttl", DEFAULT_TTL)
    if -FUTURE_SKEW <= age < ttl:
        return ok({"action": "hit"})
    if req.get("offline"):
        return ok({"action": "fallback" if req.get("hasStale") else "error"})
    return ok({"action": "miss"})


# ---------------------------------------------------------------- download
def op_plan_client_download(req):
    gtype = req.get("type", "vanilla")
    if gtype not in CLIENT_CAPABLE:
        return err("E_UNSUPPORTED_TYPE", f"类型 {gtype} 不支持客户端")
    snap = load(req["snapshot"])
    plat = req["platform"]
    features = (req.get("options") or {}).get("features") or {}
    lay = layout(req["root"], req["version"])
    items = []
    client = (snap.get("downloads") or {}).get("client") or {}
    if client.get("url"):
        items.append({"url": client["url"], "path": lay["clientJarPath"],
                      "sha1": client.get("sha1"), "size": client.get("size")})
    index = snap.get("assetIndex") or {}
    if index.get("url"):
        items.append({"url": index["url"],
                      "path": f"{lay['clientIndexesDir']}/{index.get('id', '')}.json",
                      "sha1": index.get("sha1"), "size": index.get("size")})
    if req.get("assetIndex"):
        for meta in (load(req["assetIndex"]).get("objects") or {}).values():
            h = meta.get("hash")
            if h:
                items.append({
                    "url": f"https://resources.download.minecraft.net/{h[:2]}/{h}",
                    "path": f"{lay['clientObjectsDir']}/{h[:2]}/{h}",
                    "sha1": h, "size": meta.get("size"),
                })
    for lib in snap.get("libraries", []):
        if not rules_allow(lib.get("rules"), plat, features):
            continue
        art = (lib.get("downloads") or {}).get("artifact")
        if art and art.get("url") and art.get("path"):
            items.append({"url": art["url"], "path": f"{lay['clientLibrariesDir']}/{art['path']}",
                          "sha1": art.get("sha1"), "size": art.get("size")})
    return ok({"items": items, "count": len(items)})


def op_plan_server_launch(req):
    gtype = req.get("type", "vanilla")
    opts = req.get("options") or {}
    major = req.get("javaMajor", 8)
    lay = layout(req["root"], req["version"], gtype, java_major=major)

    jvm = list(opts.get("jvmOpts") or [])
    jvm += [f"-Xms{opts.get('minMem', '512M')}", f"-Xmx{opts.get('maxMem', '2G')}"]

    user_server = opts.get("userServerArgs") or []
    server_args: list[str] = []
    if opts.get("nogui") and "nogui" not in user_server:
        server_args.append("nogui")
    server_args += user_server
    if opts.get("forceUpgrade") and "--forceUpgrade" not in server_args:
        server_args.append("--forceUpgrade")

    return ok({
        "executable": lay["javaExecutable"],
        "cwd": lay["serverDir"],
        "jarPath": lay["serverJarPath"],
        "jvmArgs": jvm,
        "serverArgs": server_args,
    })


def op_plan_server_deploy(req):
    gtype = req.get("type", "vanilla")
    if gtype != "vanilla":
        return err("E_UNSUPPORTED_OP", f"{gtype} 无离线部署计划")
    snap = load(req["snapshot"])
    server = (snap.get("downloads") or {}).get("server")
    if not server:
        return err("E_NO_SERVER_DOWNLOAD", "快照缺少服务端下载")
    version = snap.get("id", req.get("version", ""))
    lay = layout(req["root"], version, gtype)
    name = SERVER_JAR[gtype].format(v=version)
    return ok({
        "version": version,
        "type": gtype,
        "workdir": lay["serverDir"],
        "jarName": name,
        "eula": True,
        "coreArtifact": {
            "url": server["url"],
            "sha1": server.get("sha1"),
            "size": server.get("size"),
            "filename": name,
        },
    })


def op_dl_concurrency(req):
    if req["sizeBytes"] >= RANGE_THRESHOLD:
        return ok({"mode": "ranged", "parts": RANGE_PARTS})
    return ok({"mode": "single", "parts": 1})


def op_concurrency(req):
    return ok({"concurrency": max(1, min(64, req["threads"]))})


# ---------------------------------------------------------------- misc
def op_resolve_version(req):
    man = load(req["snapshot"])
    ch = req["channel"]
    vid = man["latest"]["release"] if ch == "release" else man["latest"]["snapshot"]
    entry = next((e for e in man["versions"] if e["id"] == vid), None)
    if not entry:
        return err("E_VERSION_NOT_FOUND", f"未找到版本 {vid}")
    return ok({"id": vid, "channel": "release" if entry["type"] == "release" else "snapshot",
               "type": entry["type"]})


def op_non_tty(req):
    man = load(req["snapshot"])
    return ok({"version": req.get("providedVersion") or man["latest"]["release"],
               "username": req.get("providedUsername") or "guest",
               "interactive": False, "confirm": True})


def op_progress(req):
    i = req["input"]
    return ok({"kind": i["kind"], "description": i.get("description"),
               "total": i.get("total"), "current": i.get("current"),
               "phase": i.get("phase"), "indefinite": i.get("total") is None})


OPS = {
    "planLayout": op_plan_layout,
    "planClientLaunch": op_client_launch,
    "planClientDownload": op_plan_client_download,
    "requiredJava": op_required_java,
    "verifyArtifact": op_verify,
    "cacheDecision": op_cache,
    "planServerLaunch": op_plan_server_launch,
    "planServerDeploy": op_plan_server_deploy,
    "planDownloadConcurrency": op_dl_concurrency,
    "resolveConcurrency": op_concurrency,
    "resolveVersion": op_resolve_version,
    "nonTtyDefaults": op_non_tty,
    "normalizeProgress": op_progress,
}


def dispatch(req):
    fn = OPS.get(req.get("operation"))
    if fn is None:
        return err("E_UNSUPPORTED_OP", f"未实现操作 {req.get('operation')}")
    try:
        return fn(req)
    except Exception as e:  # noqa: BLE001
        return err("E_INTERNAL", f"{type(e).__name__}: {e}")


def main():
    if "--operations" in sys.argv:
        print(json.dumps(sorted(OPS), indent=2))
        return 0
    req = json.load(sys.stdin)
    if isinstance(req, list):  # 批量
        print(json.dumps([dispatch(r) for r in req]))
    else:
        print(json.dumps(dispatch(req), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
