# Windows 真机端到端验证：部署 + 启动一个服务端，等 `Done (` 后发 `stop`，校验退出码。
#
# 用法（在父仓库根执行）：
#   uv sync --directory E:\orzmc-verify\src --all-packages   # 首次：见下方 UV_PYTHON_INSTALL_DIR 说明
#   scripts/win/run.sh -f scripts/win/e2e-server.ps1
#
# 约定：产物一律在收敛工作根 E:\orzmc-verify\ 下（src/ minecraft/ logs/）。
#   ⚠️ E:\orzmc 是生产部署目录，勿动。
#
# 前置（首次）：
#   git clone --depth 1 https://github.com/OrzMC/OrzPythonMC.git E:\orzmc-verify\src
#   $env:UV_PYTHON_INSTALL_DIR="E:\orzmc-verify\uvpython"; uv sync --directory E:\orzmc-verify\src --all-packages
#   —— 必须指定 UV_PYTHON_INSTALL_DIR：默认 uv 托管目录可能残留不可信装入点（os error 448）。

$exe    = "E:\orzmc-verify\src\.venv\Scripts\orzmc.exe"
$root   = "E:\orzmc-verify\minecraft"
$log    = "E:\orzmc-verify\logs\server-e2e.log"
$version = "1.20.4"
$type    = "vanilla"

New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
"== version =="; & $exe version

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.Arguments = "server -v $version -t $type --yes --nogui --root-dir $root"
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"
$p = [System.Diagnostics.Process]::Start($psi)

$sw = [System.IO.StreamWriter]::new($log, $false, (New-Object System.Text.UTF8Encoding($false)))
$sw.AutoFlush = $true
$deadline = (Get-Date).AddMinutes(20); $done = $false
while (-not $p.HasExited -and (Get-Date) -lt $deadline) {
    $line = $p.StandardOutput.ReadLine()
    if ($line -ne $null) {
        $sw.WriteLine($line)
        if (-not $done -and $line -match 'Done \(') {
            $done = $true
            "GOT Done at " + (Get-Date -Format HH:mm:ss)
            $p.StandardInput.WriteLine("stop"); $p.StandardInput.Flush()
        }
    } else { Start-Sleep -Milliseconds 200 }
}
if (-not $p.HasExited) { "TIMEOUT"; $p.Kill() }
$p.WaitForExit()
$sw.Close()

"EXIT=$($p.ExitCode) DONE=$done"
"== log tail =="; Get-Content $log -Tail 6
"== root size =="; "{0:N0} MB" -f ((Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB)
"== lingering java =="; (Get-Process java -ErrorAction SilentlyContinue | Measure-Object).Count
