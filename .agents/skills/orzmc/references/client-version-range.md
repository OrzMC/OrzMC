# 测试服「客户端能进哪些版本」判定法

玩家/老板问「支持哪些客户端版本」，或升级核心/Geyser/Eaglercraft 后确认范围变化时，用本文。

**核心口径**：范围由**入口插件**决定，不是服务端原生版本决定。后台 Paper/Folia 是 26.3/26.2，客户端却能跑 1.7.2 —— 因为后端有 ViaVersion 系翻译层。回答时必须按通道拆（Java / 基岩 / 网页），不能只报服务端核心版本。

## 一条命令取证（三通道并行）

```bash
# 1) Java：状态包版本串就是代理对外宣称的范围（形如 "Velocity 1.7.2-26.3"）
PYTHONPATH="" python "$LOCALAPPDATA/hermes/scripts/orzmc_entry_probe.py"   # 内含 Java 握手

# 2) 基岩：/v1/join 的 version 字段 = 当前支持的最新 Bedrock 版本
curl -s --max-time 8 http://127.0.0.1:19132/v1/join

# 3) 网页：443 只要 404 + Server: EaglercraftXServer 就说明 WebSocket 入口活着
curl -sk --max-time 8 --resolve dev.{SERVER_NAME}.cn:443:127.0.0.1 https://dev.{SERVER_NAME}.cn/ -I
```

## 各通道上下限的「真值」怎么读

### Java：读插件 jar 的协议类，不靠记忆

```bash
# 下限：ViaRewind 里有 Protocol1_7_6_10To1_7_2_5 → 1.7.2 起
# 上限：ViaVersion 的 Protocol1_* 类最高到哪个版本 → 就是上限（= 服务端自身版本）
PYTHONPATH="" python - <<'EOF'
import zipfile
for p in ('ViaVersion-5.12.2.jar','ViaRewind-4.2.0.jar'):
    z=zipfile.ZipFile(f'mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/plugins/{p}')
    print(p, [n.split('/')[-1] for n in z.namelist() if 'Protocol1_' in n][-3:])
EOF
```

**上限铁律**：客户端比服务端新就进不去（ViaVersion 只能向下翻译）。核心升到 26.4 之前，27.x 客户端一律 "outdated server"。

**还要减掉 `block-versions`**：`plugins/ViaVersion/config.yml` 里的安全基线会把 1.20.5/1.20.6、1.21/1.21.1、1.21.2/1.21.3、1.21.4 直接踢掉（提示 `You are using an unsupported Minecraft version!`）。lobby 配了这份 config、folia 没配，但玩家从 `VELOCITY_TRY=lobby` 进，所以全服生效。答范围时必须显式列这几个例外，否则答「1.7.2–26.3 全支持」是错的。

> 想实测某个协议号是否被拒，不能只做握手——握手成功只代表代理收下了，`block-versions` 的拒绝发生在**后端** join 阶段。要么读 config，要么完整走 login + UUID 字段并读 disconnect 包；不完整登录会被 Velocity 的 "logging in too fast" 限流挡住，看到的是假阴性。

### 基岩：扫 Geyser jar 里的版本字符串表

```bash
PYTHONPATH="" python - <<'EOF'
import zipfile,re
z=zipfile.ZipFile('eagler/proxy/plugins/Geyser-Velocity.jar')
hits=set()
for n in z.namelist():
    if n.endswith('.class'):
        for s in re.findall(rb'[ -~]{4,20}', z.read(n)):
            t=s.decode()
            if re.fullmatch(r'(1\.2[0-9]|26)\.\d{1,2}(\.\d{1,2})?', t): hits.add(t)
print(sorted(hits, key=lambda s:[int(x) for x in s.split('.')]))
EOF
```

Geyser 2.12.1 的表覆盖 **Bedrock 1.20.0 → 1.26.6x**（`/v1/join` 通告的 `version` 是最新那一项，`protocol` 是 NetherNet 协议号，两者别混）。窗口会随 Geyser 升级整体前移，升级后重扫一次。

### 网页：读 listeners.toml 的 `[protocols]`

> 网页入口本身该怎么搭（有没有代理层、EaglerXPaper vs Velocity 插件、双栈与 TLS）见 `references/eagler-client-access.md`；本文只答「范围」。

```bash
grep -nE '^\[|min_minecraft_protocol|max_minecraft_protocol' eagler/proxy/plugins/eaglerxserver/listeners.toml
```

默认 `min_minecraft_protocol = 3`（1.7）、`max_minecraft_protocol = 340`（1.12.2）、`max_minecraft_protocol_v5 = -1`（v5 客户端不限）。所以网页端是「EaglercraftX 客户端，MC 协议 3–340」，实际玩家多数用 1.8.8。

老 Eaglercraft 1.5.2 客户端走 `legacy_redirect`（默认空）→ 空值即拒绝，不是故障。要说「1.5.2 能不能进」得先看这个键，别默认支持。

## 回答模板（老板/玩家问时）

| 通道 | 地址 | 范围 |
|:--|:--|:--|
| Java | `dev.{SERVER_NAME}.cn:25565` | 1.7.2 – <服务端版本>，减掉 block-versions 四段 |
| 基岩 | `dev.{SERVER_NAME}.cn:19132` | Bedrock 1.20.0 – 最新（`/v1/join` 的 version） |
| 网页 | `https://dev.{SERVER_NAME}.cn` | EaglercraftX，MC 协议 3–340 |

附一句「上限 = 服务端版本，比它新的客户端要等核心升级」，以及客户端侧 mod 一般能进（`announce-forge=false` 丢 FML 标记）、带服务端 mod 的整合包进不去。
