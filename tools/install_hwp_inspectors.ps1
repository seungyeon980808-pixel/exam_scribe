$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    npm install

    $headers = @{ "User-Agent" = "HwpPalette-tool-installer" }
    $release = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/edwardkim/rhwp/releases/latest" `
        -Headers $headers
    $assetName = "rhwp-$($release.tag_name)-windows-x86_64.zip"
    $asset = $release.assets | Where-Object { $_.name -eq $assetName }
    $sums = $release.assets | Where-Object { $_.name -eq "SHA256SUMS.txt" }
    if (-not $asset -or -not $sums) {
        throw "rhwp $($release.tag_name) Windows 배포 파일이나 체크섬을 찾지 못했습니다."
    }

    $downloadDir = Join-Path ([System.IO.Path]::GetTempPath()) "hwp-palette-rhwp"
    New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
    $zip = Join-Path $downloadDir $assetName
    $sumFile = Join-Path $downloadDir "SHA256SUMS.txt"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip
    Invoke-WebRequest -Uri $sums.browser_download_url -OutFile $sumFile

    $line = Get-Content $sumFile |
        Where-Object { $_ -match [regex]::Escape($assetName) } |
        Select-Object -First 1
    if (-not $line) {
        throw "$assetName 체크섬 항목이 없습니다."
    }
    $expected = ($line -split "\s+")[0].ToLowerInvariant()
    $actual = (Get-FileHash -Algorithm SHA256 $zip).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        throw "rhwp 체크섬 불일치: expected=$expected actual=$actual"
    }

    $dest = Join-Path $PSScriptRoot "bin"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force
    $exe = Get-ChildItem -Recurse $dest -Filter "rhwp.exe" |
        Select-Object -First 1 -ExpandProperty FullName
    if (-not $exe) {
        throw "압축을 풀었지만 rhwp.exe를 찾지 못했습니다."
    }

    & $exe --version
    & ".\node_modules\.bin\kordoc.cmd" --version
    Write-Host "설치 완료: $exe"
    Write-Host "rhwp SHA-256: $actual"
}
finally {
    Pop-Location
}
