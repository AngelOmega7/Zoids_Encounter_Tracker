CREDIT TO u/AdChemical1651 for the building blocks of this

Installing Release:
Download release and extract

To Build:
Uses Python3 with Pandas and Flet

Automatic Builds:
Pushes to the default branch (master) build Windows, macOS, and Linux,
except when only this README.txt changes. Manual builds are also available
under Actions. Only builds from master publish to the existing releases:
  windows: windows-app.zip
  macOS: macos-app.tar.gz (Apple Silicon and Intel)
  linux: linux-app.tar.gz (x64, built on Ubuntu 22.04)
Each successful build replaces its release asset and removes the original
legacy download. Release titles, notes, and tags are preserved; the source
archives still point to the original tagged commit. No custom secrets are
needed: workflows use GITHUB_TOKEN with contents: write permission.
Extract the entire bundle and keep its files together. On Linux, extract
with tar -xzf linux-app.tar.gz into a dedicated folder; compatible GTK 3
and libsecret runtime libraries are required. This is not a .deb installer.
If the default branch is renamed, update the branch filters and publishing
conditions in all three workflows under .github/workflows.

Saved Enemy Sets:
On the Enemy page, fill in enemies, enter a set name, and click Save New Set.
Select a saved set and click Load Set to restore it, including edited HP,
stats, abilities, and weapons. Save Changes updates the currently loaded/saved
set (and its name); Save New Set creates a separate copy with a unique name.
Save before loading another set or closing the app: edits are not autosaved.
Delete Set removes the selected saved set; Clear All Enemies only clears the form.

Sets are stored in enemy_sets.sqlite3 in the app's user-data folder:
Linux: $XDG_DATA_HOME/zoids-encounter-tracker (default ~/.local/share/zoids-encounter-tracker)
Windows: %LOCALAPPDATA%/ZoidsEncounterTracker
macOS: ~/Library/Application Support/ZoidsEncounterTracker
Packaged Flet apps use FLET_APP_STORAGE_DATA when available.
Back up this database file to keep a copy of your sets.

Check out this Character Sheet app: https://github.com/AngelOmega7/Character_Sheet_app.git

Check out Current Rules here: https://docs.google.com/document/d/1QLEzUa894f7YmWbAhS5cNmQMuv08-h6vPFmjzrKmiQA/edit?usp=sharing
