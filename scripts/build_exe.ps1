# Totvs Helper — build TotvsHelper_64b.exe and optional TotvsHelper_32b.exe
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1 -Python32 "C:\Python39-32\python.exe"

param(
    [string]$Python64 = "",
    [string]$Python32 = ""
)

$ErrorActionPreference = "Stop"

function Invoke-Python {
    param(
        [string]$Exe,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )
    & $Exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Comando falhou: $Exe $($Args -join ' ')"
    }
}

function Get-Bitness {
    param([string]$Exe)
    $out = & $Exe -c "import struct; print(struct.calcsize('P') * 8)" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel ler arquitetura de $Exe" }
    if ($out -is [System.Array]) { $out = $out[-1] }
    return [int]($out.ToString().Trim())
}

function Assert-Tkinter {
    param([string]$Exe, [string]$Label)
    Invoke-Python $Exe -c "import tkinter"
    if ($LASTEXITCODE -ne 0) {
        throw "$Label sem tkinter. Use instalacao completa do Python 3.9 (nao ZIP embeddable)."
    }
}

function Build-One {
    param(
        [string]$Exe,
        [string]$ExeName,
        [string]$WorkPath
    )

    $outFile = "$ExeName.exe"
    Write-Host ""
    Write-Host "=== $outFile ($Exe) ===" -ForegroundColor Cyan

    $env:TOTVS_HELPER_EXE_NAME = $ExeName
    Invoke-Python $Exe -m PyInstaller --clean --noconfirm --workpath $WorkPath totvs_helper.spec
    Remove-Item Env:TOTVS_HELPER_EXE_NAME -ErrorAction SilentlyContinue

    $path = Join-Path "dist" $outFile
    if (-not (Test-Path $path)) {
        throw "Artefato nao encontrado: $path"
    }
    Write-Host "OK: $path"
}

if (-not (Test-Path ".env")) {
    throw "Arquivo .env nao encontrado na raiz. Copie de .env.example antes do build."
}

$py64 = if ($Python64) { $Python64 } else { "python" }
if ((Get-Bitness $py64) -ne 64) {
    throw "Python 64-bit obrigatorio para TotvsHelper_64b (-Python64 ou 'python' no PATH)."
}
Assert-Tkinter $py64 "Python 64-bit"

$py32 = $null
if ($Python32) {
    if ((Get-Bitness $Python32) -ne 32) {
        throw "Python informado em -Python32 nao e 32-bit."
    }
    Assert-Tkinter $Python32 "Python 32-bit"
    $py32 = $Python32
}
else {
    Write-Warning "Python 32-bit nao informado (-Python32); apenas TotvsHelper_64b.exe sera gerado."
}

Write-Host "Python 64-bit: $py64"
if ($py32) { Write-Host "Python 32-bit: $py32" }

Write-Host "Gerando icones e splash..."
Invoke-Python $py64 scripts/generate_icon.py
Invoke-Python $py64 scripts/generate_splash_assets.py

Write-Host "Instalando dependencias de build (64-bit)..."
Invoke-Python $py64 -m pip install -r requirements-dev.txt
if ($py32) {
    Write-Host "Instalando dependencias de build (32-bit)..."
    Invoke-Python $py32 -m pip install -r requirements-dev.txt
}

Build-One $py64 "TotvsHelper_64b" "build_64b"
if ($py32) {
    Build-One $py32 "TotvsHelper_32b" "build_32b"
}

Write-Host ""
Write-Host "Build concluido:" -ForegroundColor Green
Write-Host "  dist/TotvsHelper_64b.exe"
if ($py32) { Write-Host "  dist/TotvsHelper_32b.exe" }
