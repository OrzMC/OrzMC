#!/usr/bin/env python3
"""OrzMC 插件质量周报生成器
- 跑 gradlew test + integrationTest + jacoco（有缓存时 ~20s）
- 解析用例数/失败/错误 + JaCoCo 覆盖率指标
- 对比上周基线，输出 Markdown 报告（供 cron 发飞书）
用法: python3 ~/.hermes/scripts/orzmc_quality_report.py
输出: stdout Markdown；历史基线存 ~/.hermes/state/orzmc_quality.json
"""
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime

try:  # Windows 控制台默认 GBK：统一转 UTF-8，避免 emoji/中文触发 UnicodeEncodeError 中断巡检
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def _hermes_home():
    """Hermes 配置目录（Windows %LOCALAPPDATA%\\hermes 优先，回退 ~/.hermes）"""
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cand = os.path.join(la, "hermes")
        if os.path.isdir(cand):
            return cand
    return os.path.expanduser("~/.hermes")


def _plugin_dir():
    """插件仓路径候选（Windows 迁移后本机克隆在 E:/orzmc/src/OrzMC/plugin）"""
    cands = [os.environ.get("ORZMC_PLUGIN_DIR", ""),
             "E:/orzmc/src/OrzMC/plugin",
             os.path.expanduser("~/OrzMC/plugin")]
    for c in cands:
        if c and os.path.isdir(c):
            return c
    return "E:/orzmc/src/OrzMC/plugin"


def _gradlew():
    """返回可直接 exec 的 gradle 入口（**必须绝对路径**：Windows CreateProcess
    不会在 child 的 cwd 里找 `gradlew.bat`，传相对名会 FileNotFoundError WinError 2）"""
    if os.name == "nt":
        for c in (os.path.join(PLUGIN_DIR, "gradlew.bat"),
                  r"E:\orzmc\tools\gradle\bin\gradle.bat"):
            if os.path.isfile(c):
                return c
        return "gradle.bat"
    for c in (os.path.join(PLUGIN_DIR, "gradlew"), "./gradlew"):
        if os.path.exists(c):
            return c
    return "./gradlew"


PLUGIN_DIR = _plugin_dir()
STATE_FILE = os.path.join(_hermes_home(), "state", "orzmc_quality.json")
JACOCO_XML = os.path.join(PLUGIN_DIR, "build/reports/jacoco/test/jacocoTestReport.xml")
RUN_START = 0.0
JACOCO_STALE = False


def _java_env():
    """JAVA_HOME：Windows 用本机 Temurin 25（E:/orzmc/tools/jdk25），Mac 走 java_home"""
    env = dict(os.environ)
    if os.name == "nt":
        jh = env.get("JAVA_HOME") or r"E:\orzmc\tools\jdk25"
        env["JAVA_HOME"] = jh
        env["PATH"] = os.path.join(jh, "bin") + os.pathsep + env.get("PATH", "")
        return env
    java_home = subprocess.run(
        ["/usr/libexec/java_home", "-v", "25"], capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.strip()
    if java_home:
        env["JAVA_HOME"] = java_home
    return env


def _gradle(*tasks, timeout=900):
    """跑一组 gradle 任务；--continue 保证同组内互不连坐。"""
    cmd = [_gradlew(), *tasks, "--no-daemon", "-q", "--continue"]
    r = subprocess.run(cmd, cwd=PLUGIN_DIR, env=_java_env(),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, ((r.stdout or "")[-1500:] + (r.stderr or "")[-1500:])


def _task_exists(name):
    """任务不存在时不能硬跑（会整体失败），先探测。"""
    try:
        r = subprocess.run([_gradlew(), "-q", "tasks", "--all"], cwd=PLUGIN_DIR,
                           env=_java_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        return name in r.stdout
    except Exception:
        return False


def _jacoco_enabled():
    """没装 jacoco 插件时跑 jacocoTestReport 会直接报错 —— 先看构建脚本。"""
    for f in ("build.gradle", "build.gradle.kts"):
        p = os.path.join(PLUGIN_DIR, f)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    if "jacoco" in fh.read().lower():
                        return True
            except OSError:
                pass
    return False


def run_gradle():
    """分三段跑，互不连坐（2026-11-06 修：单测失败不再连坐集成测试；缺 jacoco 不再整体崩）。
    返回 (overall_rc, results, tail)。results 值：0=通过 / 非0=失败 / None=跳过（任务不存在或未启用）"""
    global RUN_START
    RUN_START = time.time()
    results = {}
    tails = []

    rc, tail = _gradle("test")
    results["test"] = rc
    tails.append("== test (rc=%s) ==\n%s" % (rc, tail))

    if _task_exists("integrationTest"):
        rc2, tail2 = _gradle("integrationTest")
        results["integrationTest"] = rc2
        tails.append("== integrationTest (rc=%s) ==\n%s" % (rc2, tail2))
    else:
        results["integrationTest"] = None

    if _jacoco_enabled():
        rc3, tail3 = _gradle("jacocoTestReport", "-x", "test", "-x", "integrationTest")
        results["jacoco"] = rc3
        tails.append("== jacocoTestReport (rc=%s) ==\n%s" % (rc3, tail3))
    else:
        results["jacoco"] = None

    overall = 0 if all(v in (0, None) for v in results.values()) else 1
    return overall, results, "\n\n".join(tails)[-4000:]


def parse_test_results():
    """解析 build/test-results/{test,integrationTest}/*.xml"""
    tests = failures = errors = skipped = classes = 0
    for sub in ("test", "integrationTest"):
        d = os.path.join(PLUGIN_DIR, f"build/test-results/{sub}")
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".xml"):
                continue
            root = ET.parse(os.path.join(d, f)).getroot()
            tests += int(root.attrib.get("tests", 0))
            failures += int(root.attrib.get("failures", 0))
            errors += int(root.attrib.get("errors", 0))
            skipped += int(root.attrib.get("skipped", 0))
            classes += 1
    return tests, failures, errors, skipped, classes


def parse_jacoco():
    """解析 JaCoCo 覆盖率（并标记数据是否陈旧：XML 早于本轮开跑时间即为旧数据）"""
    global JACOCO_STALE
    JACOCO_STALE = False
    if not os.path.exists(JACOCO_XML):
        return {}
    try:
        JACOCO_STALE = os.path.getmtime(JACOCO_XML) < RUN_START
    except OSError:
        JACOCO_STALE = False
    root = ET.parse(JACOCO_XML).getroot()
    out = {}
    for c in root.findall("counter"):
        typ = c.attrib["type"]
        missed, covered = int(c.attrib["missed"]), int(c.attrib["covered"])
        total = missed + covered
        out[typ] = round(covered / total * 100, 1) if total else 0.0
    return out


def git_short_sha():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PLUGIN_DIR,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "?"
    except Exception:
        return "?"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def trend(cur, prev, higher_better=True):
    """返回趋势箭头：▲ 改善 / ▼ 恶化 / ＝ 持平 / 新 首次 / — 本期无数据"""
    if not isinstance(cur, (int, float)):   # 本期无数据（如 jacoco 报告缺失）→ 不参与比较
        return "—"
    if prev is None or not isinstance(prev, (int, float)):
        return "新"
    diff = cur - prev
    if abs(diff) < 0.05:
        return "＝"
    if (diff > 0) == higher_better:
        return f"▲{diff:+.1f}"
    return f"▼{diff:+.1f}"


def main():
    rc, results, tail = run_gradle()
    tests, failures, errors, skipped, classes = parse_test_results()
    cov = parse_jacoco()
    sha = git_short_sha()
    state = load_state()
    prev = state.get("last")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    passed = tests - failures - errors - skipped
    pass_rate = round(passed / tests * 100, 2) if tests else 0.0

    # 行级指标
    rows = []
    rows.append(("测试用例数", tests, prev.get("tests") if prev else None, "更高更好"))
    rows.append(("用例通过率", pass_rate, prev.get("pass_rate") if prev else None, "更高更好"))
    rows.append(("指令覆盖率 INSTRUCTION", cov.get("INSTRUCTION"), prev.get("instr") if prev else None, "更高更好"))
    rows.append(("分支覆盖率 BRANCH", cov.get("BRANCH"), prev.get("branch") if prev else None, "更高更好"))
    rows.append(("方法覆盖率 METHOD", cov.get("METHOD"), prev.get("method") if prev else None, "更高更好"))
    rows.append(("类覆盖率 CLASS", cov.get("CLASS"), prev.get("class_cov") if prev else None, "更高更好"))

    def _seg(key, label):
        v = results.get(key)
        return f"{label} ✅" if v == 0 else (f"{label} ⏭️" if v is None else f"{label} ❌")

    seg = " · ".join([_seg("test", "单测"), _seg("integrationTest", "集成"), _seg("jacoco", "覆盖率")])
    lines = [f"📊 **OrzMC 插件质量周报**（{now}）", "",
             f"commit: `{sha}` · gradle: {'✅' if rc == 0 else '❌'} · 测试类: {classes}", f"{seg}", ""]
    if results.get("integrationTest") is None:
        lines.insert(4, "> ℹ️ 未找到 `integrationTest` 任务，已跳过（不再拖垮整轮）")
    if results.get("jacoco") is None:
        lines.insert(4, "> ℹ️ 构建脚本未启用 jacoco，覆盖率列留空（不再报错）")
    elif JACOCO_STALE or results.get("jacoco") != 0:
        lines.insert(4, "> ⚠️ 覆盖率数据未刷新（jacocoTestReport 未成功），下表覆盖率为上次产物，仅供参考")
    lines.append("| 指标 | 本期 | 上期 | 趋势 |")
    lines.append("|:--|--:|--:|:--|")
    for name, cur, prv, _ in rows:
        cur_s = f"{cur:g}" if isinstance(cur, (int, float)) else str(cur)
        prv_s = f"{prv:g}" if isinstance(prv, (int, float)) else ("—" if prv is None else str(prv))
        lines.append(f"| {name} | {cur_s} | {prv_s} | {trend(cur, prv)} |")
    lines.append("")

    if failures + errors > 0:
        lines.append(f"⚠️ **有失败用例**: {failures} 失败 / {errors} 错误 / {skipped} 跳过")
    else:
        lines.append(f"✅ 全部通过（{skipped} 跳过）")

    # 保存基线
    save_state({"last": {
        "tests": tests, "pass_rate": pass_rate,
        "instr": cov.get("INSTRUCTION"), "branch": cov.get("BRANCH"),
        "method": cov.get("METHOD"), "class_cov": cov.get("CLASS"),
        "failures": failures, "errors": errors,
        "sha": sha, "date": now,
    }})

    print("\n".join(lines))


if __name__ == "__main__":
    main()
