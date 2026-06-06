param(
    [string]$KnowledgePath = "$env:USERPROFILE\OneDrive\Documentos\CONHECIMENTO DO HERMES"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$EnvPath = Join-Path $ProjectRoot ".env"
$ProjectKnowledge = Join-Path $ProjectRoot "conhecimento"

New-Item -ItemType Directory -Force -Path $KnowledgePath | Out-Null

if (-not (Test-Path $EnvPath)) {
    Copy-Item (Join-Path $ProjectRoot ".env.example") $EnvPath
}

$envLines = Get-Content $EnvPath
$setting = "HERMES_KNOWLEDGE_SOURCE_DIR=$KnowledgePath"

if ($envLines -match "^HERMES_KNOWLEDGE_SOURCE_DIR=") {
    $envLines = $envLines | ForEach-Object {
        if ($_ -match "^HERMES_KNOWLEDGE_SOURCE_DIR=") { $setting } else { $_ }
    }
    Set-Content -Path $EnvPath -Value $envLines -Encoding UTF8
} else {
    Add-Content -Path $EnvPath -Value ""
    Add-Content -Path $EnvPath -Value "# Base de conhecimento local"
    Add-Content -Path $EnvPath -Value $setting
}

if (Test-Path $ProjectKnowledge) {
    Get-ChildItem -Path $ProjectKnowledge -File -Recurse | ForEach-Object {
        $relative = $_.FullName.Substring($ProjectKnowledge.Length).TrimStart("\", "/")
        $target = Join-Path $KnowledgePath $relative
        New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
        if (-not (Test-Path $target)) {
            Copy-Item $_.FullName $target
        }
    }
}

Write-Host "Base canonica configurada em:"
Write-Host $KnowledgePath
Write-Host ""
Write-Host "O watcher vai sincronizar essa pasta para ./conhecimento e fazer commit/push."
