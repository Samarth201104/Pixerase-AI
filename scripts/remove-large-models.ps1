# PowerShell script to remove large model files from the repository and filesystem.
$paths = @("background/models/u2net.pth", "object/models/migan_512_places2.pt")
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Host "Removing $p from git and filesystem"
        git rm --cached $p -f 2>$null
        Remove-Item $p -Force
    } else {
        Write-Host "$p not found"
    }
}
Write-Host "Done. Add and commit changes: git add . && git commit -m 'Remove large model files'"
