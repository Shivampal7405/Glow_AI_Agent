"""
GLOW Installer Builder
Creates a one-click installer for GLOW using PyInstaller
"""

import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller"""

    print("=" * 80)
    print("Building GLOW One-Click Installer")
    print("=" * 80)

    # PyInstaller command
    pyinstaller_cmd = [
        'pyinstaller',
        '--name=GLOW',
        '--onefile',
        '--windowed',
        '--icon=assets/glow_icon.ico' if Path('assets/glow_icon.ico').exists() else '',
        '--add-data=config.example.json;.',
        '--add-data=LICENSE;.',
        '--add-data=README.md;.',
        '--hidden-import=google.generativeai',
        '--hidden-import=anthropic',
        '--hidden-import=groq',
        '--hidden-import=PyQt6',
        '--hidden-import=pyautogui',
        '--hidden-import=pywin32',
        '--hidden-import=PIL',
        '--hidden-import=pytesseract',
        '--collect-all=google.generativeai',
        '--collect-all=anthropic',
        '--collect-all=groq',
        '--collect-all=PyQt6',
        'glow_app.py'
    ]

    # Remove empty icon parameter if no icon exists
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg]

    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(pyinstaller_cmd)}")

    try:
        subprocess.run(pyinstaller_cmd, check=True)
        print("\n✅ Executable built successfully!")
        print(f"📁 Output: dist/GLOW.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False

def create_inno_setup_script():
    """Create Inno Setup script for the installer"""

    script_content = """
; GLOW Installer Script for Inno Setup
; This creates a one-click installer that sets up GLOW with minimal user interaction

#define MyAppName "GLOW"
#define MyAppVersion "1.0.5"
#define MyAppPublisher "GLOW Project"
#define MyAppURL "https://github.com/shivampal7405/GLOW"
#define MyAppExeName "GLOW.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-G7H8-I9J0-K1L2M3N4O5P6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer_output
OutputBaseFilename=GLOW-Setup-v{#MyAppVersion}
SetupIconFile=assets\\glow_icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.example.json"; DestDir: "{app}"; DestName: "config.json"; Flags: ignoreversion onlyifdoesntexist
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  ApiKeyPage: TInputQueryWizardPage;
  ModelSelectionPage: TInputOptionWizardPage;

procedure InitializeWizard;
begin
  // Model selection page
  ModelSelectionPage := CreateInputOptionPage(wpLicense,
    'Select AI Model', 'Choose your preferred AI model for GLOW',
    'GLOW supports multiple AI providers. Select the one you want to use:',
    True, False);
  ModelSelectionPage.Add('Groq (Recommended - Free & Fast)');
  ModelSelectionPage.Add('Google Gemini (Vision Capable)');
  ModelSelectionPage.Add('Anthropic Claude (Advanced Reasoning)');
  ModelSelectionPage.Values[0] := True;

  // API Key input page
  ApiKeyPage := CreateInputQueryPage(ModelSelectionPage.ID,
    'API Key Configuration', 'Enter your API key',
    'Please enter your API key for the selected model. You can get a free API key from the provider''s website.');
  ApiKeyPage.Add('API Key:', False);
end;

function GetApiKeyUrl: String;
begin
  if ModelSelectionPage.Values[0] then
    Result := 'https://console.groq.com'
  else if ModelSelectionPage.Values[1] then
    Result := 'https://ai.google.dev'
  else
    Result := 'https://console.anthropic.com';
end;

function GetModelName: String;
begin
  if ModelSelectionPage.Values[0] then
    Result := 'Groq (Fast API)'
  else if ModelSelectionPage.Values[1] then
    Result := 'Gemini Vision (Live Vision)'
  else
    Result := 'Claude (Anthropic)';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigFile: String;
  ConfigContent: TStringList;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigFile := ExpandConstant('{app}\\config.json');
    ConfigContent := TStringList.Create;
    try
      if FileExists(ConfigFile) then
        ConfigContent.LoadFromFile(ConfigFile);

      // Update config with user selections
      // This is a simplified approach - in production, use proper JSON parsing
      ConfigContent.Text := StringReplace(ConfigContent.Text,
        '"conversational_model": "Groq (Fast API)"',
        '"conversational_model": "' + GetModelName + '"',
        [rfReplaceAll]);

      if ModelSelectionPage.Values[0] then
        ConfigContent.Text := StringReplace(ConfigContent.Text,
          '"groq_api_key": "YOUR_GROQ_API_KEY_HERE"',
          '"groq_api_key": "' + ApiKeyPage.Values[0] + '"',
          [rfReplaceAll])
      else if ModelSelectionPage.Values[1] then
        ConfigContent.Text := StringReplace(ConfigContent.Text,
          '"gemini_api_key": "YOUR_GEMINI_API_KEY_HERE"',
          '"gemini_api_key": "' + ApiKeyPage.Values[0] + '"',
          [rfReplaceAll])
      else
        ConfigContent.Text := StringReplace(ConfigContent.Text,
          '"anthropic_api_key": "YOUR_ANTHROPIC_API_KEY_HERE"',
          '"anthropic_api_key": "' + ApiKeyPage.Values[0] + '"',
          [rfReplaceAll]);

      ConfigContent.SaveToFile(ConfigFile);
    finally
      ConfigContent.Free;
    end;
  end;
end;
"""

    script_path = Path("installer.iss")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

    print(f"\n✅ Inno Setup script created: {script_path}")
    print("📝 To build the installer:")
    print("   1. Install Inno Setup from: https://jrsoftware.org/isdl.php")
    print("   2. Right-click installer.iss and select 'Compile'")
    print("   3. The installer will be in installer_output/GLOW-Setup-v1.0.5.exe")

def create_nsis_script():
    """Create NSIS script as an alternative to Inno Setup"""

    script_content = """
; GLOW NSIS Installer Script
; Alternative to Inno Setup

!include "MUI2.nsh"

Name "GLOW - Windows AI Assistant"
OutFile "installer_output\\GLOW-Setup.exe"
InstallDir "$PROGRAMFILES\\GLOW"
InstallDirRegKey HKCU "Software\\GLOW" ""
RequestExecutionLevel admin

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "assets\\glow_icon.ico"
!define MUI_UNICON "assets\\glow_icon.ico"

; Pages
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; Installer Section
Section "Install"
    SetOutPath "$INSTDIR"

    File "dist\\GLOW.exe"
    File "config.example.json"
    File "README.md"
    File "LICENSE"

    ; Copy config if it doesn't exist
    IfFileExists "$INSTDIR\\config.json" ConfigExists
        CopyFiles "$INSTDIR\\config.example.json" "$INSTDIR\\config.json"
    ConfigExists:

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\GLOW"
    CreateShortcut "$SMPROGRAMS\\GLOW\\GLOW.lnk" "$INSTDIR\\GLOW.exe"
    CreateShortcut "$DESKTOP\\GLOW.lnk" "$INSTDIR\\GLOW.exe"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    CreateShortcut "$SMPROGRAMS\\GLOW\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"

    ; Registry
    WriteRegStr HKCU "Software\\GLOW" "" $INSTDIR
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\GLOW" "DisplayName" "GLOW"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\GLOW" "UninstallString" "$INSTDIR\\Uninstall.exe"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    Delete "$INSTDIR\\GLOW.exe"
    Delete "$INSTDIR\\config.example.json"
    Delete "$INSTDIR\\README.md"
    Delete "$INSTDIR\\LICENSE"
    Delete "$INSTDIR\\Uninstall.exe"

    Delete "$SMPROGRAMS\\GLOW\\GLOW.lnk"
    Delete "$SMPROGRAMS\\GLOW\\Uninstall.lnk"
    Delete "$DESKTOP\\GLOW.lnk"
    RMDir "$SMPROGRAMS\\GLOW"
    RMDir "$INSTDIR"

    DeleteRegKey HKCU "Software\\GLOW"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\GLOW"
SectionEnd
"""

    script_path = Path("installer.nsi")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

    print(f"\n✅ NSIS script created: {script_path}")
    print("📝 To build with NSIS:")
    print("   1. Install NSIS from: https://nsis.sourceforge.io/")
    print("   2. Right-click installer.nsi and select 'Compile NSIS Script'")

def create_build_instructions():
    """Create detailed build instructions"""

    instructions = """
# GLOW One-Click Installer Build Instructions

## Prerequisites

1. **Python 3.10+** installed
2. **PyInstaller** - Install with: `pip install pyinstaller`
3. **Inno Setup** (Recommended) - Download from: https://jrsoftware.org/isdl.php
   OR
   **NSIS** (Alternative) - Download from: https://nsis.sourceforge.io/

## Step 1: Build the Executable

Run the build script:

```bash
python build_installer.py
```

This will:
- Create a standalone GLOW.exe in the `dist` folder
- Bundle all dependencies
- Create necessary data files

## Step 2: Build the Installer

### Option A: Using Inno Setup (Recommended)

1. Open Inno Setup Compiler
2. File → Open → Select `installer.iss`
3. Build → Compile
4. The installer will be created in `installer_output/GLOW-Setup-v1.0.5.exe`

### Option B: Using NSIS

1. Right-click `installer.nsi`
2. Select "Compile NSIS Script"
3. The installer will be created in `installer_output/GLOW-Setup.exe`

## Step 3: Test the Installer

1. Run the generated installer
2. Follow the setup wizard
3. Enter your Groq API key (get free at https://console.groq.com)
4. Launch GLOW from desktop icon

## Features of the One-Click Installer

✅ **No Python Required** - Bundles Python runtime
✅ **Automatic Dependency Installation** - All libraries included
✅ **Desktop Icon** - Quick access to GLOW
✅ **API Key Setup** - Prompts during installation
✅ **Model Selection** - Choose Groq/Gemini/Claude
✅ **Clean Uninstaller** - Removes all files properly

## Distribution

The final installer (`GLOW-Setup-v1.0.5.exe`) can be:
- Uploaded to GitHub Releases
- Shared directly with users
- Distributed on your website

Size: Approximately 150-250 MB (includes all dependencies)

## Troubleshooting

### PyInstaller Errors
If PyInstaller fails, try:
```bash
pip install --upgrade pyinstaller
pip install --upgrade PyQt6
```

### Missing Icon
Create an icon file at `assets/glow_icon.ico` or the build will use default icon

### Hidden Imports
If modules are missing in the exe, add them to the `--hidden-import` list in `build_installer.py`

## Creating a GitHub Release

1. Build the installer
2. Go to your GitHub repository
3. Click "Releases" → "Create a new release"
4. Tag: `v1.0.5`
5. Upload `GLOW-Setup-v1.0.5.exe`
6. Add release notes
7. Publish!

---

**For questions or issues, visit: https://github.com/shivampal7405/GLOW/issues**
"""

    with open('BUILD_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
        f.write(instructions)

    print("\n✅ Build instructions created: BUILD_INSTRUCTIONS.md")

def main():
    """Main build process"""
    print("\n🚀 GLOW Installer Build System")
    print("=" * 80)

    choice = input("\nWhat would you like to do?\n"
                  "1. Build executable only\n"
                  "2. Create installer scripts only\n"
                  "3. Both (build exe + create scripts)\n"
                  "4. Create build instructions\n"
                  "Choice (1-4): ").strip()

    if choice == "1":
        build_executable()
    elif choice == "2":
        create_inno_setup_script()
        create_nsis_script()
    elif choice == "3":
        if build_executable():
            create_inno_setup_script()
            create_nsis_script()
    elif choice == "4":
        create_build_instructions()
    else:
        print("❌ Invalid choice")
        return

    print("\n" + "=" * 80)
    print("✅ Build process complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
