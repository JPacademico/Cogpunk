<#
.SYNOPSIS  Record the tModLoader window and convert it to a pixel-art-safe GIF (Directive D5).
.EXAMPLE   powershell -ExecutionPolicy Bypass -File tools/record-gif.ps1 -Name boss-boilerheart-phase2 -Seconds 8 -Crop "640:360:320:180"
#>
param(
    [Parameter(Mandatory = $true)][string]$Name,   # <area>-<feature>[-fix], kebab-case
    [int]$Seconds = 8,                              # keep <= 10
    [ValidateSet(25, 50)][int]$Fps = 25,            # GIF delays are 10 ms units: 25/50 fps play back exactly
    [string]$Crop = "",                             # ffmpeg crop "w:h:x:y" (prefer cropping over scaling)
    [int]$Countdown = 3,
    [string]$OutDir = "docs/media"
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "ffmpeg not found: winget install --id Gyan.FFmpeg -e" }

$window = Get-Process | Where-Object { $_.MainWindowTitle -match '^(Terraria|tModLoader)' } | Select-Object -First 1
if (-not $window) { throw "tModLoader window not found. Start the game windowed at 1280x720 first." }
$title = $window.MainWindowTitle

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$gif   = Join-Path $OutDir ("{0}_{1}.gif" -f (Get-Date -Format "yyyy-MM-dd"), $Name)
$raw   = Join-Path $env:TEMP "cogpunk_capture.mkv"
$sheet = Join-Path $env:TEMP ("cogpunk_{0}_sheet.png" -f $Name)

Write-Host "Capturing '$title' for $Seconds s, starting in $Countdown s..."
Start-Sleep -Seconds $Countdown
& ffmpeg -hide_banner -loglevel error -y -f gdigrab -framerate 50 -draw_mouse 0 -i "title=$title" -t $Seconds -c:v ffv1 $raw

$vf = "fps=$Fps"
if ($Crop) { $vf += ",crop=$Crop" }
$vf += ",split[a][b];[a]palettegen=max_colors=256:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle"
& ffmpeg -hide_banner -loglevel error -y -i $raw -vf $vf -loop 0 $gif

# 12 evenly spaced frames for self-review (not committed)
$step = [Math]::Max(1, [Math]::Ceiling($Seconds * $Fps / 12))
& ffmpeg -hide_banner -loglevel error -y -i $gif -vf "select='not(mod(n\,$step))',scale=480:-1:flags=neighbor,tile=4x3" -frames:v 1 $sheet

$sizeMB = [Math]::Round((Get-Item $gif).Length / 1MB, 2)
Write-Host "GIF:   $gif ($sizeMB MB)"
Write-Host "Sheet: $sheet"
if ($sizeMB -gt 10) { Write-Warning "GIF is over 10 MB: shorten -Seconds or add -Crop." }
Remove-Item $raw -ErrorAction SilentlyContinue
