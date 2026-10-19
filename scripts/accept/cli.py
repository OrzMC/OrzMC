#!/usr/bin/env python3
"""orzmc CLI 自动化验收（**两套实现共用这一份**）：按规范逐项检查，而不是按某个实现。

为什么放在父仓库：Python 与 Swift 各自复制过一份（842 + 724 行，用例集还会漂移）。
判据必须只有一份——`docs/two-cli-strategy.md` 的 M2。实现只通过 `--cli` 注入。

为什么要有它：
- 单测跑的是进程内调用，`main()` / 进程退出码 / 冻结二进制 / 非 TTY / 真实文件落点都覆盖不到；
  2.11.0 的发布二进制里 `--show-completion` / `completion install` 崩过，单测全绿、用户一跑就炸；
- 迭代中改一个命令容易顺手破坏另一条路径（信封、退出码、取消语义、stdout 纯净）。

用法::

    # Swift（构建产物）
    python3 scripts/accept/cli.py --cli .build/release/orzmc

    # Python（源码模式 / 冻结二进制）
    python3 scripts/accept/cli.py --cli 'uv run --directory python orzmc'
    python3 scripts/accept/cli.py --cli dist/orzmc --frozen

    python3 scripts/accept/cli.py --list-cases          # 列用例
    python3 scripts/accept/cli.py --only envelope,completion
    python3 scripts/accept/cli.py --network             # 追加联网用例

设计约束：
- **只用标准库**（6 平台 runner 自带 python 直接跑）；
- 每个用例一个隔离沙箱（HOME / XDG_* / 游戏根都在临时目录）；
- 一律 `stdin=DEVNULL` + 超时——「非交互不阻塞」本身是被测行为；
- 断言取自 `docs/spec/{cli-surface,frontends,install-update}.md`；规范变了就改断言，
  别把断言改成迁就实现。
- `--frozen` 只用于「冻结二进制专属」用例（PyInstaller 打包才有的通路）；
  实现独有的能力差异应写进 `docs/spec/parity.json`，不要在脚本里分叉。

"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import traceback
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # 父仓库根（docs/spec 在这里）

#: 规范命令集(规范 §2)。新增/删除命令时这里和 docs/spec/cli-surface.json 一起改。
EXPECTED_COMMANDS = (
    "client",
    "server",
    "plugin",
    "list",
    "remove",
    "backup",
    "update",
    "uninstall",
    "app",
    "completion",
    "capabilities",
    "mcp",
    "version",
)

#: MCP 不暴露的元 / 自毁命令(规范 §8.2)。
MCP_EXCLUDED = {"capabilities", "completion", "mcp", "uninstall"}

#: 规范 §9 的补全 shell。
COMPLETION_SHELLS = ("bash", "zsh", "fish", "powershell", "pwsh")


# ── 基础设施 ────────────────────────────────────────────────────────────────


class CheckError(AssertionError):
    """断言失败(带上下文,便于定位)。"""


class SkipCase(Exception):
    """前置条件不满足(如未提供规范快照):记 SKIP,不算失败。"""


def skip(reason: str) -> None:
    raise SkipCase(reason)


def check(condition: object, message: str) -> None:
    if not condition:
        raise CheckError(message)


@dataclass
class Result:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration: float = 0.0

    @property
    def combined(self) -> str:
        return self.stdout + self.stderr

    def describe(self) -> str:
        return (
            f"$ orzmc {' '.join(self.args)}\n"
            f"  rc={self.returncode}\n"
            f"  stdout={self.stdout.strip()[:2000]!r}\n"
            f"  stderr={self.stderr.strip()[:2000]!r}"
        )


class Sandbox:
    """一次验收的隔离环境:独立的 HOME / XDG / 游戏根 + 干净的环境变量。"""

    def __init__(self, cli: Sequence[str], *, timeout: float, frozen: bool) -> None:
        self.cli = list(cli)
        self.timeout = timeout
        self.frozen = frozen
        self._tmp = tempfile.TemporaryDirectory(prefix="orzmc-accept-")
        self.dir = Path(self._tmp.name)
        self.home = self.dir / "home"
        self.root = self.dir / "mc"
        for path in (self.home, self.root):
            path.mkdir(parents=True, exist_ok=True)
        self.env = self._clean_env()

    def _clean_env(self) -> dict[str, str]:
        env = {key: value for key, value in os.environ.items() if not key.startswith("ORZMC_")}
        env.update(
            {
                "HOME": str(self.home),
                "USERPROFILE": str(self.home),
                "XDG_STATE_HOME": str(self.dir / "state"),
                "XDG_DATA_HOME": str(self.dir / "data"),
                "XDG_CONFIG_HOME": str(self.dir / "config"),
                "XDG_CACHE_HOME": str(self.dir / "cache"),
                # 稳定输出:关掉颜色/进度动画,固定宽度。
                "NO_COLOR": "1",
                "TERM": "dumb",
                "COLUMNS": "120",
            }
        )
        if os.name != "nt":
            # 让 `completion install` 有确定落点(不探测、不写真实 shell 配置)。
            env["SHELL"] = "/bin/bash"
        return env

    def run(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        drop_env: Iterable[str] = (),
        stdin: str | None = None,
        timeout: float | None = None,
    ) -> Result:
        run_env = dict(self.env)
        run_env.update(env or {})
        for key in drop_env:
            run_env.pop(key, None)
        started = time.monotonic()
        completed = subprocess.run(
            [*self.cli, *args],
            input=stdin,
            stdin=None if stdin is not None else subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=run_env,
            cwd=str(self.dir),
            timeout=self.timeout if timeout is None else timeout,
        )
        return Result(
            list(args),
            completed.returncode,
            completed.stdout,
            completed.stderr,
            time.monotonic() - started,
        )

    def cleanup(self) -> None:
        self._tmp.cleanup()


@dataclass
class Context:
    sandbox: Sandbox
    frozen: bool
    verbose: bool
    state_paths: Path | None = None

    def run(self, *args: str, **kwargs: object) -> Result:
        return self.sandbox.run(*args, **kwargs)  # type: ignore[arg-type]


# ── 通用断言 ────────────────────────────────────────────────────────────────


def no_crash(result: Result) -> None:
    """任何路径都不许把 Python 异常泄漏给用户(尤其冻结二进制里的 import 错误)。"""
    check(
        "Traceback (most recent call last)" not in result.combined,
        "出现未捕获异常(traceback):\n" + result.describe(),
    )
    for needle in ("ModuleNotFoundError", "ImportError", "MissingStyle"):
        check(needle not in result.stderr, f"stderr 出现 {needle}:\n" + result.describe())


def envelope(result: Result) -> dict[str, object]:
    """规范 §6.1:``--json`` 下 stdout **恰好一个** JSON 对象。"""
    text = result.stdout.strip()
    check(bool(text), "stdout 为空,期望 JSON 信封:\n" + result.describe())
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CheckError(f"stdout 不是单个 JSON 对象({exc}):\n" + result.describe()) from None
    check(isinstance(payload, dict), f"信封必须是对象:\n{result.describe()}")
    for key in ("ok", "command", "data", "error"):
        check(key in payload, f"信封缺字段 {key}:\n{result.describe()}")
    check(isinstance(payload["ok"], bool), f"ok 必须是 bool:\n{result.describe()}")
    check("\x1b" not in result.stdout, "JSON stdout 里混入了 ANSI 转义序列:\n" + result.describe())
    return payload


def expect_ok(result: Result, command: str) -> dict[str, object]:
    payload = envelope(result)
    check(payload["command"] == command, f"信封 command 应为 {command}:\n{result.describe()}")
    check(payload["ok"] is True, f"期望成功:\n{result.describe()}")
    check(payload["error"] is None, f"成功时 error 必须为 null:\n{result.describe()}")
    check(result.returncode == 0, f"成功时退出码必须是 0:\n{result.describe()}")
    return payload


def expect_error(result: Result, command: str, code: str | None = None) -> dict[str, object]:
    payload = envelope(result)
    check(payload["command"] == command, f"信封 command 应为 {command}:\n{result.describe()}")
    check(payload["ok"] is False, f"期望失败:\n{result.describe()}")
    check(payload["data"] is None, f"失败时 data 必须为 null:\n{result.describe()}")
    error = payload["error"]
    check(isinstance(error, dict), f"error 必须是对象:\n{result.describe()}")
    assert isinstance(error, dict)  # for type checkers
    check(isinstance(error.get("code"), str), f"error.code 必须是字符串:\n{result.describe()}")
    check(isinstance(error.get("message"), str) and error["message"], f"error.message 不能为空:\n{result.describe()}")
    if code is not None:
        check(error["code"] == code, f"期望错误码 {code},实际 {error['code']}:\n{result.describe()}")
    expected_rc = 130 if error["code"] == "E_CANCELLED" else 1
    check(result.returncode == expected_rc, f"{error['code']} 的退出码应为 {expected_rc}:\n" + result.describe())
    return payload


# ── 用例注册 ────────────────────────────────────────────────────────────────


@dataclass
class Case:
    group: str
    name: str
    func: Callable[[Context], None]
    frozen_only: bool = False
    network: bool = False


CASES: list[Case] = []


def case(group: str, name: str, *, frozen_only: bool = False, network: bool = False) -> Callable:
    def register(func: Callable[[Context], None]) -> Callable[[Context], None]:
        CASES.append(Case(group, name, func, frozen_only=frozen_only, network=network))
        return func

    return register


# ── surface:命令面 / 帮助 / 版本 ────────────────────────────────────────────


def _command_names(ctx: Context) -> list[str]:
    payload = expect_ok(ctx.run("--json", "capabilities"), "capabilities")
    data = payload["data"]
    assert isinstance(data, dict)
    commands = data["commands"]
    assert isinstance(commands, list)
    return [str(item["name"]) for item in commands]


@case("surface", "no-args-prints-help")
def case_no_args(ctx: Context) -> None:
    result = ctx.run()
    no_crash(result)
    check(result.returncode == 0, "无子命令必须打印帮助并退出 0(规范 §1):\n" + result.describe())
    for name in EXPECTED_COMMANDS:
        check(name in result.stdout, f"帮助里缺命令 {name}:\n" + result.describe())


@case("surface", "no-subcommand-json-is-usage-error")
def case_no_subcommand_json(ctx: Context) -> None:
    """`--json` 承诺 stdout 只有信封:缺子命令按用法错误处理(§1/§6.1)。"""
    expect_error(ctx.run("--json"), "_root", "E_USAGE")


@case("surface", "help-flags")
def case_help_flags(ctx: Context) -> None:
    for flag in ("-h", "--help"):
        result = ctx.run(flag)
        no_crash(result)
        check(result.returncode == 0, f"{flag} 应退出 0(规范 §3):\n" + result.describe())
        check("Usage" in result.stdout, f"{flag} 应打印用法:\n" + result.describe())


@case("surface", "help-every-command")
def case_help_every_command(ctx: Context) -> None:
    names = _command_names(ctx)
    check(set(EXPECTED_COMMANDS) <= set(names), f"capabilities 缺命令: {set(EXPECTED_COMMANDS) - set(names)}")
    for name in names:
        for flag in ("--help", "-h"):
            result = ctx.run(name, flag)
            no_crash(result)
            check(result.returncode == 0, f"{name} {flag} 应退出 0:\n" + result.describe())
            check(name in result.stdout or "Usage" in result.stdout, f"{name} {flag} 帮助异常:\n" + result.describe())


@case("surface", "version-subcommand-matches-flag")
def case_version_parity(ctx: Context) -> None:
    sub = ctx.run("version")
    flag = ctx.run("--version")
    no_crash(sub)
    no_crash(flag)
    check(sub.returncode == 0 and flag.returncode == 0, "version 与 --version 都必须成功")
    pattern = re.compile(r"orzmc (\d+\.\d+\.\d+)")
    sub_match = pattern.search(sub.stdout)
    flag_match = pattern.search(flag.stdout)
    check(sub_match is not None, "version 输出里没有版本号:\n" + sub.describe())
    check(flag_match is not None, "--version 输出里没有版本号:\n" + flag.describe())
    assert sub_match and flag_match
    check(sub_match.group(1) == flag_match.group(1), "version 与 --version 报的版本不一致")


@case("surface", "usage-errors-exit-1")
def case_usage_errors(ctx: Context) -> None:
    for args in (("nope",), ("--nope",), ("client", "--nope"), ("remove",)):
        result = ctx.run(*args)
        no_crash(result)
        check(result.returncode == 1, f"用法错误应退出 1(规范 §6):\n{result.describe()}")
        check(result.stderr.strip() != "", f"用法错误信息应写 stderr:\n{result.describe()}")


@case("surface", "global-options-before-subcommand")
def case_global_option_placement(ctx: Context) -> None:
    ok = ctx.run("--json", "--root-dir", str(ctx.sandbox.root), "list")
    expect_ok(ok, "list")
    # 规范 §1:全局选项必须出现在子命令之前;放后面应被明确拒绝(而不是静默忽略)。
    bad = ctx.run("list", "--json")
    no_crash(bad)
    check(bad.returncode == 1, "`list --json`(全局选项在子命令后)应被拒绝:\n" + bad.describe())


# ── envelope:--json 信封行为 ────────────────────────────────────────────────


@case("envelope", "every-command-emits-one-envelope")
def case_envelope_matrix(ctx: Context) -> None:
    sandbox_root = str(ctx.sandbox.root)
    expect_ok(ctx.run("--json", "version"), "version")
    expect_ok(ctx.run("--json", "capabilities"), "capabilities")
    expect_ok(ctx.run("--json", "--root-dir", sandbox_root, "list"), "list")
    expect_ok(ctx.run("--json", "completion", "bash"), "completion")
    # 业务失败也必须是「一个信封 + 稳定错误码」,而不是裸栈或半行文本。
    expect_error(ctx.run("--json", "client", "-t", "paper", "-v", "1.20.4"), "client", "E_UNSUPPORTED_TYPE")
    expect_error(ctx.run("--json", "client", "-m", "nope", "-v", "1.20.4"), "client", "E_USAGE")
    expect_error(ctx.run("--json", "server", "-x", "nope", "-v", "1.20.4"), "server", "E_USAGE")
    expect_error(ctx.run("--json", "client", "-v", "1.20.4", "-j", "0"), "client", "E_USAGE")
    expect_error(ctx.run("--json", "update", "--channel", "nope"), "update", "E_USAGE")
    expect_error(ctx.run("--json", "backup", "--root-dir", sandbox_root), "backup")
    expect_error(ctx.run("--json", "plugin"), "plugin", "E_USAGE")
    # --force:被测二进制可能就在 .build / venv 里(开发环境护栏会先拦下来),
    # 这条断言只关心「非交互缺 --yes → 取消」。
    expect_error(ctx.run("--json", "--root-dir", sandbox_root, "uninstall", "--force"), "uninstall", "E_CANCELLED")


@case("envelope", "failures-do-not-print-human-lines-to-stdout")
def case_envelope_stdout_only_json(ctx: Context) -> None:
    result = ctx.run("--json", "remove", "-v", "9.9.9", "--root-dir", str(ctx.sandbox.root))
    # 规范 §6 错误码表:目标不存在 = E_NOT_FOUND(两套实现一致)。
    expect_error(result, "remove", "E_NOT_FOUND")
    check(
        result.stdout.strip().count("\n") == 0,
        "stdout 只能有信封一行(人类可读内容必须走 stderr):\n" + result.describe(),
    )


# ── contract:退出码 / 取消语义 / 数据不动 ───────────────────────────────────


@case("contract", "remove-without-yes-is-cancelled")
def case_remove_cancel(ctx: Context) -> None:
    target = ctx.sandbox.root / "versions" / "1.20.4" / "client"
    target.mkdir(parents=True)
    (target / "marker").write_text("x", encoding="utf-8")
    result = ctx.run("--json", "remove", "-v", "1.20.4", "--root-dir", str(ctx.sandbox.root))
    expect_error(result, "remove", "E_CANCELLED")
    check(target.is_dir(), "取消后不得删除任何东西(规范 §8.2)")


@case("contract", "remove-with-yes-removes")
def case_remove_yes(ctx: Context) -> None:
    target = ctx.sandbox.root / "versions" / "1.20.5" / "client"
    target.mkdir(parents=True)
    payload = expect_ok(
        ctx.run("--json", "remove", "-v", "1.20.5", "--root-dir", str(ctx.sandbox.root), "--yes"),
        "remove",
    )
    data = payload["data"]
    check(isinstance(data, dict) and data.get("removed") is True, f"应报告 removed=true: {data}")
    check(not target.exists(), "`remove --yes` 应真的删掉该目录")


@case("contract", "list-reports-installed-versions")
def case_list_installed(ctx: Context) -> None:
    client_dir = ctx.sandbox.root / "versions" / "1.21.4" / "client"
    client_dir.mkdir(parents=True)
    server_dir = ctx.sandbox.root / "versions" / "1.21.4" / "server" / "paper"
    server_dir.mkdir(parents=True)
    payload = expect_ok(ctx.run("--json", "--root-dir", str(ctx.sandbox.root), "list"), "list")
    data = payload["data"]
    assert isinstance(data, dict)
    versions = data["versions"]
    assert isinstance(versions, list)
    entry = next((item for item in versions if item["version"] == "1.21.4"), None)
    check(entry is not None, f"list 未报告已安装版本: {versions}")
    assert entry is not None
    check(entry["client"] is True, "list 应识别出客户端")
    check("paper" in entry["servers"], "list 应识别出 paper 服务端")


@case("contract", "uninstall-without-yes-is-cancelled")
def case_uninstall_cancel(ctx: Context) -> None:
    # --force:让「开发环境护栏」不抢先,这里只验证非交互缺 --yes → 取消。
    result = ctx.run("--json", "--root-dir", str(ctx.sandbox.root), "uninstall", "--force")
    expect_error(result, "uninstall", "E_CANCELLED")


@case("contract", "non-interactive-never-blocks")
def case_no_blocking(ctx: Context) -> None:
    # stdin 是 DEVNULL:任何“等输入”的路径都必须立刻返回(规范 §7 红线)。
    # 用**超时**判定是否阻塞,不用墙钟阈值 —— CI 机器忙时 20s 内的正常启动也可能被误判。
    # 真阻塞(等输入)会一直挂着,由 timeout 触发并在这里变成失败。
    for args in (("list",), ("--json", "list"), ("client", "-t", "paper")):
        result = ctx.run(*args, timeout=20)
        no_crash(result)
        check(result.duration < 20, f"{args} 疑似阻塞(耗时 {result.duration:.1f}s)")


# ── completion:补全脚本 / 安装 / 动态补全 ──────────────────────────────────


@case("completion", "scripts-for-every-shell")
def case_completion_scripts(ctx: Context) -> None:
    for shell in COMPLETION_SHELLS:
        result = ctx.run("--json", "completion", shell)
        payload = expect_ok(result, "completion")
        data = payload["data"]
        assert isinstance(data, dict)
        script = data.get("script")
        check(isinstance(script, str) and len(script) > 20, f"{shell} 补全脚本为空: {data}")
        check(data.get("shell") == shell, f"{shell} 上报的 shell 不对: {data}")


@case("completion", "unknown-shell-rejected")
def case_completion_unknown_shell(ctx: Context) -> None:
    result = ctx.run("--json", "completion", "tcsh")
    expect_error(result, "completion", "E_USAGE")


@case("completion", "install-writes-into-home")
def case_completion_install(ctx: Context) -> None:
    home = ctx.sandbox.home
    if os.name == "nt":
        # Windows 默认 shell 是 powershell,而 F6 规定它只生成脚本 → 必须明确报不支持。
        expect_error(ctx.run("--json", "completion", "install"), "completion", "E_UNSUPPORTED")
        return

    targets = {
        "bash": home / ".local" / "share" / "bash-completion" / "completions" / "orzmc",
        "zsh": home / ".zsh" / "completions" / "_orzmc",
    }
    for shell, script in targets.items():
        payload = expect_ok(ctx.run("--json", "completion", "install", env={"SHELL": f"/bin/{shell}"}), "completion")
        data = payload["data"]
        assert isinstance(data, dict)
        check(data.get("shell") == shell, f"应识别出 {shell}: {data}")
        check(data.get("path") == str(script), f"落点应为 {script}: {data}")
        check(script.is_file(), f"未写入补全脚本: {script}")
        check(script.read_text(encoding="utf-8").strip() != "", "补全脚本为空")
        rc = home / (".bashrc" if shell == "bash" else ".zshrc")
        check(rc.is_file(), f"{shell} 需要 rc 里有一行加载语句(否则补全不生效)")
        before = rc.read_text(encoding="utf-8")
        check(before.count("added by orzmc") == 1, f"{shell} rc 应恰好一条 orzmc 标记行: {before!r}")
        # 幂等:再装一次不重复改 rc、脚本内容不变。
        expect_ok(ctx.run("--json", "completion", "install", env={"SHELL": f"/bin/{shell}"}), "completion")
        check(rc.read_text(encoding="utf-8") == before, f"{shell} 重复安装不应再改 rc(必须幂等)")
        check(script.read_text(encoding="utf-8").strip() != "", "补全脚本被清空")


@case("completion", "install-paths-match-state-paths")
def case_completion_paths_match_snapshot(ctx: Context) -> None:
    """`frontends.md` §7「待补 1」:补全落点必须与 `state-paths.json` 逐项一致(防路径漂移)。"""
    if ctx.state_paths is None:
        skip("未提供 --state-paths docs/spec/state-paths.json")
    snapshot = json.loads(ctx.state_paths.read_text(encoding="utf-8"))
    unix_paths = (snapshot.get("unix") or {}).get("completion") or {}
    check(isinstance(unix_paths, dict) and unix_paths, f"state-paths.json 缺 unix.completion: {snapshot}")
    home = str(ctx.sandbox.home)
    for shell, template in unix_paths.items():
        expected = str(template).replace("$HOME", home)
        result = ctx.run("--json", "completion", "install", env={"SHELL": f"/bin/{shell}"})
        payload = expect_ok(result, "completion")
        data = payload["data"]
        assert isinstance(data, dict)
        check(data.get("path") == expected, f"{shell} 落点与 state-paths.json 不一致: {data.get('path')} != {expected}")


@case("completion", "script-only-shells-are-unsupported")
def case_completion_script_only(ctx: Context) -> None:
    """`frontends.md` F6:powershell/pwsh 只生成脚本,`install` 必须明确 E_UNSUPPORTED。"""
    for shell in ("powershell", "pwsh"):
        result = ctx.run("--json", "completion", "install", env={"SHELL": f"/usr/bin/{shell}"})
        payload = expect_error(result, "completion", "E_UNSUPPORTED")
        error = payload["error"]
        assert isinstance(error, dict)
        check(f"completion {shell}" in str(error.get("message")), f"应提示改用 `completion {shell}`: {error}")


@case("completion", "install-without-shell-is-usage-error")
def case_completion_install_no_shell(ctx: Context) -> None:
    # PSModulePath 也去掉:装了 pwsh 的 Linux/macOS 也有它,不能拿它判平台。
    result = ctx.run("--json", "completion", "install", drop_env=("SHELL", "PSModulePath"))
    if os.name == "nt":
        # Windows 上没有 $SHELL 时按平台兜底 powershell,再按 F6 报「不支持自动安装」。
        expect_error(result, "completion", "E_UNSUPPORTED")
        return
    payload = expect_error(result, "completion", "E_USAGE")
    error = payload["error"]
    assert isinstance(error, dict)
    check("completion <shell>" in str(error.get("message")), f"应提示改用 `completion <shell>`: {error}")


@case("completion", "dynamic-completion-dispatch", frozen_only=True)
def case_dynamic_completion(ctx: Context) -> None:
    """`completion <shell>` 生成的脚本会调用本命令的 `_ORZMC_COMPLETE` 路径。

    只对冻结二进制跑:模块模式下 click 的 prog name 是 ``python -m orzmc_app.cli``,
    环境变量名(由 prog name 派生)不是 ``_ORZMC_COMPLETE``,测不到真实路径。
    """
    result = ctx.run(
        env={"_ORZMC_COMPLETE": "complete_bash", "COMP_WORDS": "orzmc cl", "COMP_CWORD": "1"},
    )
    no_crash(result)
    check("client" in result.stdout, "动态补全没有列出 client:\n" + result.describe())


@case("completion", "typer-auto-options-are-gone")
def case_typer_completion_options(ctx: Context) -> None:
    """typer 自带的 `--install-completion`/`--show-completion` 与 `completion` 子命令重复,
    且只能靠 shellingham 探测 shell(冻结二进制里必崩) —— 必须从命令面移除。"""
    for flag in ("--show-completion", "--install-completion"):
        result = ctx.run(flag)
        no_crash(result)
        check(result.returncode == 1, f"{flag} 应已移除(用法错误 rc=1):\n" + result.describe())
        # 只断言**语义**（被拒绝 + 提到该选项 + 没触发 shell 探测），不锁死框架文案：
        # typer 说 "No such option"，ConsoleKit 说 "Unknown command" —— 规范只要求用法错误。
        check(flag in result.stderr, f"{flag} 的报错应提到该选项:\n" + result.describe())
        check("shellingham" not in result.stderr, f"{flag} 不应触发 shell 探测:\n" + result.describe())


# ── mcp:stdio JSON-RPC ─────────────────────────────────────────────────────


@case("mcp", "stdio-session")
def case_mcp_session(ctx: Context) -> None:
    # 先造一个“已安装版本”,这样 tools/call remove 才会走到「需要确认 → 取消」分支。
    installed = ctx.sandbox.root / "versions" / "1.20.4" / "client"
    installed.mkdir(parents=True, exist_ok=True)
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list", "arguments": {"root-dir": str(ctx.sandbox.root)}},
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "remove", "arguments": {"version": "1.20.4", "root-dir": str(ctx.sandbox.root)}},
        },
        {"jsonrpc": "2.0", "id": 5, "method": "ping"},
        {"jsonrpc": "2.0", "id": 6, "method": "nope/nope"},
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "nope", "arguments": {}}},
    ]
    stdin = "".join(json.dumps(message, ensure_ascii=False) + "\n" for message in messages)
    stdin += "{ this is not json }\n"
    result = ctx.run("mcp", stdin=stdin)
    no_crash(result)

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    check(len(lines) >= 7, f"响应行数不足({len(lines)}):\n" + result.describe())
    replies: dict[int, dict[str, object]] = {}
    for line in lines:
        payload = json.loads(line)  # 每行都必须是一条 JSON-RPC 消息(规范 §8.2)
        check(payload.get("jsonrpc") == "2.0", f"缺少 jsonrpc 2.0: {payload}")
        if isinstance(payload.get("id"), int):
            replies[payload["id"]] = payload

    init = replies.get(1, {})
    init_result = init.get("result")
    check(isinstance(init_result, dict), f"initialize 没有 result: {init}")
    assert isinstance(init_result, dict)
    check(init_result.get("protocolVersion") == "2025-06-18", f"protocolVersion 未回显: {init_result}")
    check(init_result.get("serverInfo", {}).get("name") == "orzmc", f"serverInfo 不对: {init_result}")

    tools = replies.get(2, {}).get("result", {}).get("tools")  # type: ignore[union-attr]
    check(isinstance(tools, list), "tools/list 没有返回 tools")
    assert isinstance(tools, list)
    names = {tool["name"] for tool in tools}
    check(names.isdisjoint(MCP_EXCLUDED), f"MCP 不应暴露 {MCP_EXCLUDED & names}")
    check({"list", "remove", "client"} <= names, f"核心命令未暴露: {names}")

    list_result = replies.get(3, {}).get("result")
    check(isinstance(list_result, dict), f"tools/call list 没有 result: {replies.get(3)}")
    assert isinstance(list_result, dict)
    check(list_result.get("isError") is False, f"list 应成功: {list_result}")
    inner = json.loads(list_result["content"][0]["text"])
    check(inner["ok"] is True and inner["command"] == "list", f"tool 信封不对: {inner}")

    remove_result = replies.get(4, {}).get("result")
    check(isinstance(remove_result, dict), f"tools/call remove 没有 result: {replies.get(4)}")
    assert isinstance(remove_result, dict)
    check(remove_result.get("isError") is True, "缺 --yes 的 remove 必须报错(规范 §8.2)")
    inner = json.loads(remove_result["content"][0]["text"])
    check(inner["error"]["code"] == "E_CANCELLED", f"应是 E_CANCELLED: {inner}")
    check(installed.is_dir(), "MCP 下缺 --yes 的 remove 不得真的删除任何东西")

    check(replies.get(5, {}).get("result") == {}, f"ping 应返回空结果: {replies.get(5)}")
    check(replies.get(6, {}).get("error", {}).get("code") == -32601, f"未知方法应 -32601: {replies.get(6)}")
    check(replies.get(7, {}).get("error", {}).get("code") == -32602, f"未知 tool 应 -32602: {replies.get(7)}")


# ── frozen:冻结二进制专属(import / 打包缺口)────────────────────────────────


@case("frozen", "completion-install-does-not-crash", frozen_only=True)
def case_frozen_completion_install(ctx: Context) -> None:
    """2.11.0 及更早发布版的崩溃点:shellingham 动态子模块未被 PyInstaller 收集。"""
    result = ctx.run("--json", "completion", "install", env={"SHELL": "/bin/zsh"} if os.name != "nt" else None)
    no_crash(result)  # 关键断言:不得出现 ModuleNotFoundError / RuntimeError 栈
    if os.name == "nt":
        # Windows 上没有 $SHELL → powershell,按 F6 明确「不支持自动安装」——这是**正确**行为,
        # 只要不是崩溃即可(以前这里直接崩在 shellingham)。
        expect_error(result, "completion", "E_UNSUPPORTED")
        return
    expect_ok(result, "completion")


# ── network(默认不跑)──────────────────────────────────────────────────────


@case("network", "update-check", network=True)
def case_update_check(ctx: Context) -> None:
    result = ctx.run("--json", "update", "--check", timeout=120)
    payload = envelope(result)  # 限流也算“有信封地失败”,但不能裸栈
    no_crash(result)
    if payload["ok"] is True:
        data = payload["data"]
        assert isinstance(data, dict)
        check(data.get("mode") == "check", f"data.mode 应为 check: {data}")
    else:
        error = payload["error"]
        assert isinstance(error, dict)
        check(str(error.get("code", "")).startswith("E_"), f"失败也要有稳定错误码: {error}")


@case("network", "plugin-search", network=True)
def case_plugin_search(ctx: Context) -> None:
    result = ctx.run("--json", "plugin", "--search", "essentials", "--count", "2", timeout=120)
    no_crash(result)
    payload = envelope(result)
    if payload["ok"] is True:
        data = payload["data"]
        assert isinstance(data, dict)
        check(data.get("mode") == "search", f"data.mode 应为 search: {data}")


# ── 运行器 ──────────────────────────────────────────────────────────────────


@dataclass
class Outcome:
    case: Case
    status: str  # PASS / FAIL / SKIP
    detail: str = ""
    duration: float = 0.0


def run_case(case_: Case, sandbox: Sandbox, *, verbose: bool, state_paths: Path | None) -> Outcome:
    ctx = Context(sandbox=sandbox, frozen=sandbox.frozen, verbose=verbose, state_paths=state_paths)
    started = time.monotonic()
    try:
        case_.func(ctx)
    except SkipCase as exc:
        return Outcome(case_, "SKIP", str(exc), time.monotonic() - started)
    except CheckError as exc:
        return Outcome(case_, "FAIL", str(exc), time.monotonic() - started)
    except subprocess.TimeoutExpired as exc:
        return Outcome(case_, "FAIL", f"超时({exc.timeout}s): {exc.cmd}", time.monotonic() - started)
    except Exception:  # pragma: no cover - 断言代码自身的 bug 也要暴露
        return Outcome(case_, "FAIL", "验收脚本自身异常:\n" + traceback.format_exc(), time.monotonic() - started)
    return Outcome(case_, "PASS", "", time.monotonic() - started)


def selected_cases(*, only: set[str], network: bool, frozen: bool) -> list[Case]:
    picked: list[Case] = []
    for case_ in CASES:
        if case_.group == "network" and not network:
            continue
        if case_.frozen_only and not frozen:
            continue
        if only and case_.group not in only:
            continue
        picked.append(case_)
    return picked


def build_cli(explicit: str | None, frozen_flag: bool) -> tuple[list[str], bool]:
    """解析被测 CLI：`--cli` 可以是**可执行文件路径**，也可以是**命令串**（shlex 切分）。

    命令串的形式让 Python 侧沿用 `uv run ... orzmc`、Swift 侧直接给二进制路径，
    脚本本身不需要知道实现来自哪个仓库。
    """
    if not explicit:
        raise SystemExit(
            "--cli 必填：可用可执行文件路径（.build/release/orzmc）"
            "或命令串（'uv run --directory python orzmc'）"
        )
    candidate = Path(explicit).expanduser()
    if candidate.is_file() or (os.name == "nt" and Path(f"{candidate}.exe").is_file()):
        path = candidate.resolve()
        if not path.is_file():
            path = Path(f"{path}.exe")
        return [str(path)], frozen_flag
    parts = shlex.split(explicit, posix=(os.name != "nt"))
    if not parts:
        raise SystemExit(f"--cli 无法解析: {explicit!r}")
    return parts, frozen_flag


def _force_utf8_stdio() -> None:
    """Windows 控制台默认 cp1252,打印中文会 UnicodeEncodeError —— 显式切 UTF-8。

    与 `accept_selfupdate.py` 同一手法;CI 的 windows runner 真的会在第一行中文上炸。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover - 已被替换流(如测试捕获)
            pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="orzmc CLI 自动化验收(按规范断言)")
    parser.add_argument("--cli", help="被测 CLI：可执行文件路径或命令串（必填）")
    parser.add_argument("--only", default="", help="只跑指定组,逗号分隔(如 envelope,completion)")
    parser.add_argument("--network", action="store_true", help="追加联网用例(update --check / plugin 搜索)")
    parser.add_argument("--list", action="store_true", help="列出用例组后退出")
    parser.add_argument("--list-cases", action="store_true", help="列出全部用例后退出")
    parser.add_argument("--timeout", type=float, default=90.0, help="单个用例超时秒数(默认 90)")
    parser.add_argument(
        "--state-paths",
        help="规范快照 state-paths.json（缺省取父仓库 docs/spec/state-paths.json；"
        "提供时额外断言补全落点与之逐项一致，防路径漂移）",
    )
    parser.add_argument(
        "--frozen",
        action="store_true",
        help="被测对象是**冻结二进制**（启用 PyInstaller 专属用例）",
    )
    parser.add_argument("--keep", action="store_true", help="保留沙箱目录(排障用)")
    parser.add_argument("-v", "--verbose", action="store_true", help="打印每个用例的命令与输出")
    args = parser.parse_args(argv)
    _force_utf8_stdio()

    frozen = args.frozen
    only = {item.strip() for item in args.only.split(",") if item.strip()}
    cases = selected_cases(only=only, network=args.network, frozen=frozen)

    # 列用例不需要被测物（CI/文档里常用）。
    if args.list or args.list_cases:
        groups: dict[str, list[str]] = {}
        for case_ in cases:
            groups.setdefault(case_.group, []).append(case_.name)
        for group, names in groups.items():
            print(f"{group}:")
            if args.list_cases:
                for name in names:
                    print(f"  - {name}")
            else:
                print(f"  {len(names)} 个用例")
        return 0

    cli, frozen = build_cli(args.cli, args.frozen)
    default_state = REPO_ROOT / "docs" / "spec" / "state-paths.json"
    state_arg = args.state_paths or (str(default_state) if default_state.is_file() else None)
    state_paths = Path(state_arg).expanduser().resolve() if state_arg else None
    if state_paths is not None and not state_paths.is_file():
        raise SystemExit(f"--state-paths 指向的文件不存在: {state_paths}")

    if not cases:
        print("没有匹配的用例(--only / --network / --cli 组合)", file=sys.stderr)
        return 2

    sandbox = Sandbox(cli, timeout=args.timeout, frozen=frozen)
    print(f"被测对象: {' '.join(cli)}")
    print(f"沙箱: {sandbox.dir}")
    print()

    outcomes: list[Outcome] = []
    try:
        for case_ in cases:
            outcome = run_case(case_, sandbox, verbose=args.verbose, state_paths=state_paths)
            outcomes.append(outcome)
            label = f"[{outcome.status}] {case_.group}/{case_.name} ({outcome.duration:.1f}s)"
            print(label)
            if outcome.status == "FAIL":
                print(_indent(outcome.detail))
            elif args.verbose:
                print(_indent("(通过)"))
    finally:
        if args.keep:
            print(f"\n沙箱已保留: {sandbox.dir}")
        else:
            sandbox.cleanup()

    passed = sum(1 for item in outcomes if item.status == "PASS")
    skipped = [item for item in outcomes if item.status == "SKIP"]
    failed = [item for item in outcomes if item.status == "FAIL"]
    print()
    print(f"结果: {passed} 通过 / {len(failed)} 失败 / {len(skipped)} 跳过 / 共 {len(outcomes)}")
    for item in skipped:
        print(f"  SKIP {item.case.group}/{item.case.name}: {item.detail}")
    if failed:
        print("\n失败用例:")
        for item in failed:
            print(f"  - {item.case.group}/{item.case.name}")
        return 1
    return 0


def _indent(text: str) -> str:
    return "\n".join("    " + line for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())
