# Atmosphere_Kit - Switch SD Package Builder

Atmosphere_Kit is a Python builder for generating a ready-to-copy Switch SD card package. It pulls the latest GitHub Releases from configured upstream projects, creates `SwitchSD/`, and packages it as `SwitchSD.zip`.

## Usage

Python 3.11+ is required:

```bash
python -m atmosphere_kit
```

Optionally set `GITHUB_TOKEN` to raise the GitHub API rate limit:

```bash
GITHUB_TOKEN=ghp_xxx python -m atmosphere_kit
```

The build generates:

- `SwitchSD/`
- `SwitchSD.zip`
- `description.txt`

## Configuration

- Download manifest: `kit.toml`
- Static SD text resources: `resources/sd/`

The CI build requires the core packages to download and extract successfully:

- `Atmosphere`
- `Fusee`
- `Hekate + Nyx`

Other upstream components are included on a best-effort basis and are reported in the build log and release description when successfully installed.

## Included Components

- Core CFW
  - `Atmosphere + Fusee`
  - `Hekate + Nyx`
- Payloads
  - `Lockpick_RCM`
  - `TegraExplorer`
- NRO homebrew
  - `Switch_90DNS_tester`
  - `DBI` with Simplified Chinese translation
  - `daybreak`, bundled with the official Atmosphere package
- Ultrahand Overlay framework
  - `nx-ovlloader`, bundled with the Ultrahand sdout package
  - `Ultrahand-Overlay`
- OVL overlays and sysmodules
  - `EdiZon`
  - `ovl-sysmodules`
  - `StatusMonitor`
  - `ReverseNX-RT`
  - `ldn_mitm`
  - `emuiibo`
  - `QuickNTP`
  - `sys-patch`
  - `sys-clk`
  - `MissionControl`

## Key File Operations

- Move `fusee.bin` to `bootloader/payloads/`
- Rename `hekate_ctcaer_*.bin` to `payload.bin`
- Write `hekate_ipl.ini`, `exosphere.ini`, and `boot.ini`
- Write `atmosphere/hosts/emummc.txt` and `atmosphere/hosts/sysmmc.txt`
- Write Atmosphere `override_config.ini` and `system_settings.ini`
- Remove `switch/haze.nro` and `switch/reboot_to_payload.nro`
- Disable sysmodule autostart by default, keeping only the `nx-ovlloader` `boot2.flag`

## Ultrahand Overlay

- Hotkey: `ZL + ZR + D-Pad Down`
- Must be opened from a game or Homebrew; it does not open from the HOME menu
- This package uses Ultrahand instead of Tesla Menu
- Sysmodules can be enabled or disabled through `ovl-sysmodules`

## Nintendo Domain Blocking

In CFW mode, Atmosphere uses `atmosphere/hosts/` to redirect Nintendo domains to `127.0.0.1`, blocking telemetry and report uploads. Because of this, the Switch connection test will show a failure.

## GitHub Actions Secrets

| Secret | Description |
| ------ | ----------- |
| `TOKEN` | GitHub Personal Access Token with `repo` permission, used to create releases and clean up old workflow runs |

## References

| Resource | URL |
| -------- | --- |
| Switchbrew Title List | https://switchbrew.org/wiki/Title_list |
