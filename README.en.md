# AionPulse

[Português (Brasil)](README.md) · **English**

Track your group's performance in AION2 with a compact combat overlay and an interface available in Portuguese and English. Compare damage dealt, healing and damage taken with bars for each player, encounter totals and rates over the last five seconds.

![AionPulse icon](assets/aionpulse-64.png)

**Windows x64 · 0.1.0 Beta 1** · Developed by [@GabrielMartorello](https://github.com/GabrielMartorello).

## Features

- Independent DPS, Healing, Damage taken and All views in the main window and overlay.
- Per-player bars, encounter totals and rolling five-second rates.
- Damage taken combines health damage and verified shield absorption.
- Automatic character identification and party updates from observed game packets.
- Reset button in the overlay, saved overlay position and configurable size.
- Skill details, CSV export and local diagnostic counters.
- Single instance, no account or Discord login, no uploads or packet injection.

Keep the overlay above the game or use the main window on a second screen. If the party list is empty or shows IDs, keep capture running during a loading screen and when party members become visible again. Combat is not required, but identification depends on the packets the game sends. The detailed [party identification guide](docs/guia-do-usuario.md) is currently in Portuguese.

## Install

[Download the Windows installer](https://github.com/GabrielMartorello/AionPulse/releases/tag/v0.1.0-beta.1) and run **AionPulse-Setup-0.1.0-beta.1-x64.exe**.

Python, Tcl/Tk and lz4 are included; there is no need to set up Python or pip. If Npcap is missing, the wizard offers a download from the official vendor and opens its installer. It also creates shortcuts and includes an uninstaller. See the [installation guide](docs/instalacao.md), currently in Portuguese.

The executable is not digitally signed yet and may trigger SmartScreen warnings. Do not disable antivirus protection. The release includes SHA-256 hashes for checking the downloads.

### Requirements for running from source

64-bit Windows 10/11, Python 3.12 or later with Tkinter, and Npcap. If Npcap restricts capture to administrators, run the meter with administrator privileges. The default port is 13328; capture reads traffic sent from the server to the client.

## Run from source

In the project directory, using PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py --capture --overlay
```

Add `--show-main` to display the main window as well. You can also run `app.py` without arguments and start capture from the interface.

To build the launcher with the application icon:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
.\AionPulse.exe
```

The launcher uses `.venv\Scripts\pythonw.exe`, the optional `AIONPULSE_PYTHON` environment variable, or `pythonw.exe` on PATH. This executable is a launcher: Python, dependencies and project files are still required. The build uses the .NET Framework 4.x C# compiler and does not download a compiler.

## Preferences and local data

The language selector applies Portuguese (Brazil) or English to both windows. **Full values** switches the bars between abbreviated and complete numbers. These preferences are saved. **Reset** clears encounter counters while keeping detected identities and party membership.

Region identification uses the captured game server address without querying geolocation services. In this beta, `193.202.112.174` and `193.202.112.191` were observed in sessions reported as South America; this mapping does not extend to the rest of the address range. Korea identification uses the public reference listed in [THIRD_PARTY.md](THIRD_PARTY.md). Other addresses appear as **unidentified**. Server IDs shared across services are not used to guess the region.

Preferences, temporary identities and error logs are stored in `%LOCALAPPDATA%\AionPulse`. Set `AIONPULSE_DATA_DIR` to change the directory. Cached identities and party data expire after 15 minutes and are tied to the observed TCP connection; they are not a fixed list of players.

`--diagnostic-state` writes a local debugging snapshot containing names and counters. It is disabled by default. Do not commit these snapshots, captures or private reports. `.gitignore` also excludes copies placed inside the project directory.

## Development

### Build the installer

Install [Inno Setup 6.7.3](https://jrsoftware.org/isdl.php) and the build dependencies. From a source checkout:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build-installer.ps1 -Compiler 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
```

Output is written to `dist\installer`. The build includes the runtime and an archive of the public source, excluding personal preferences, identities, logs and packets. The installer does not bundle Npcap; it offers the official download with a pinned hash. Update the driver version and hash in the `.iss` file when needed. The Inno Setup 6.7.3 compiler used for this build permits noncommercial use; consult its license before commercial distribution.

### Tests and code checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Tests use synthetic data and protocol fixtures. They do not require a game account or network capture. CI runs tests, lint, formatting checks and a launcher build. See [CONTRIBUTING.md](CONTRIBUTING.md) and [architecture notes](docs/architecture.md), currently in Portuguese.

## Known limitations

Party recovery without combat correlates remote party identity (`1C92`) with the persistent identity block in `4536`, using character and server identifiers. Your own character does not need to be identified first. This association has been validated for the formats observed in this beta. If the meter starts after a member's identity packet and the game does not resend it, that member's name still requires another observation. Reset processes queued identity and party updates before clearing counters.

Recognized packet formats are experimental and may change between game versions or regions. Not all skills or formats are covered. Healing is the amount reported in packets; it does not distinguish effective healing from overhealing. Generic HP changes are not treated as healing.

Damage taken combines health damage and verified shield absorption, but does not reconstruct raw damage before all reductions. Block/parry indicators alone do not disclose how much damage was mitigated. Shield absorption requires observing the start of the pool; starting the app while a shield is already active can miss that association.

Party joins and complete rosters update membership without combat. Before a complete roster arrives, party-specific status packets (`1B92`) can recover observed member IDs; names require identity packets. Once a complete roster confirms the group, status packets from excluded players do not add them back. Generic health updates do not prove membership. Remote updates without identities or rosters cannot reconstruct names. An absence of damage does not prove a player has left. Capture losses or parsing errors make totals incomplete.

## License

GPL-3.0-only. Adapted code and references are listed in [THIRD_PARTY.md](THIRD_PARTY.md). The project is not affiliated with NCSOFT or the reference projects. The original AionPulse logo is a project asset, not an official game trademark.

