param(
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    throw "Arquivo .env nao encontrado na raiz do projeto. Configure-o antes do build."
}

Write-Host "Installing development dependencies..."
& $PythonExecutable -m pip install -r requirements-dev.txt

Write-Host "Generating application icon..."
& $PythonExecutable "scripts/generate_icon.py"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to generate assets/totvs_helper.ico"
}

Write-Host "Generating splash assets..."
& $PythonExecutable "scripts/generate_splash_assets.py"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to generate assets/splash.png"
}

Write-Host "Running PyInstaller build..."
& $PythonExecutable -m PyInstaller --clean --noconfirm "totvs_helper.spec"

Write-Host "Build complete: dist/TotvsHelper.exe"

