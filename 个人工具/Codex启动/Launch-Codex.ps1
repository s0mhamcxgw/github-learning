$ErrorActionPreference = 'Stop'
try {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $ready = $client.ConnectAsync('127.0.0.1', 10090).Wait(1500) -and $client.Connected
    } catch { $ready = $false } finally { $client.Dispose() }
    if (-not $ready) {
        Write-Host 'Open MAOMAOYUN, connect a node, enable System Proxy and TUN, then run this launcher again.' -ForegroundColor Yellow
        exit 1
    }
    $tun = @(Get-NetAdapter | Where-Object { $_.Name -eq 'MAOMAOYUN' -and $_.Status -eq 'Up' })
    if ($tun.Count -eq 0) {
        Write-Host 'Enable TUN / virtual adapter in MAOMAOYUN, then run this launcher again.' -ForegroundColor Yellow
        exit 1
    }
    foreach ($proxyName in @('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY')) {
        [Environment]::SetEnvironmentVariable($proxyName, 'http://127.0.0.1:10090', 'Process')
    }
    [Environment]::SetEnvironmentVariable('NO_PROXY', 'localhost,127.0.0.1,::1', 'Process')
    $package = Get-AppxPackage -Name OpenAI.Codex | Select-Object -First 1
    if (-not $package) { throw 'Codex desktop package was not found.' }
    $appPath = Join-Path $package.InstallLocation 'app\ChatGPT.exe'
    if (-not (Test-Path -LiteralPath $appPath)) { throw 'Codex desktop executable was not found.' }
    Write-Host 'Proxy and TUN are ready. Opening Codex...' -ForegroundColor Green
    Start-Process -FilePath $appPath
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
