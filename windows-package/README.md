# PowerBot Microsoft Store Packaging

This folder contains the minimal MSIX packaging for PowerBot Windows desktop app.

## Structure
```
windows-package/
  AppxManifest.xml
  Build-Msix.ps1
  Package/
    PowerBot.exe
    AppxManifest.xml
    Assets/
```

## Build steps

1. Build the exe:
```bash
pyinstaller --onefile --windowed --name PowerBot Unified_Laptop_Power_Bot.py
```

2. Add real app icons to `Assets/`:
- StoreLogo.png  512x512
- Square44x44Logo.png
- Square150x150Logo.png
- Wide310x150Logo.png
- SmallTile.png, MediumTile.png, LargeTile.png

3. Run the packaging script:
```powershell
.\Build-Msix.ps1
```

4. Sign the package with a code signing certificate:
```powershell
signtool sign /fd SHA256 /a /n "Beebus Builds" /t http://timestamp.digicert.com PowerBot.msix
```

5. Submit `PowerBot.msix` or `PowerBot.msixbundle` to Partner Center for Microsoft Store.

## Notes
* `runFullTrust` capability is required for shutdown/restart system actions.
* The app is packaged as a Win32 full-trust desktop app.
* For Store compliance, add a privacy policy and ensure PIN protection is documented.
