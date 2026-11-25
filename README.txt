CREDIT TO u/AdChemical1651 for the building blocks of this

Runtime catalogs (JSON only):
- zoids.json: corrected enemy stats/equipment, required levels, and tracker
  display names retained for compatibility with saved enemy sets.
- stats.json: named Tank/Fighter/Scout/Almighty progression tables.
- abilities.json: ability descriptions and numeric modifiers.
- encounters.json: random encounter candidates and their original generator
  stats/levels, preserved separately from the corrected enemy-card stats.
- loot.json: loot items, categories, tiers, weights, and BLOX flags.

The app no longer loads CSVs or requires pandas. Catalog paths are relative to
the application, so running from another working directory is supported.
The original four CSVs and generated required-level reference were moved into
source/. Tracked Python bytecode and IDE settings were archived there as well.
source/, caches, environments, and IDE state are ignored by Git and excluded
from builds. Local archived files are not included in fresh GitHub clones.
The optional tools/convert_csv_catalogs.py rebuilds the migrated catalogs from
archived CSVs; ordinary use, tests, builds, and Character Sheet syncing do not
require those files. Conversion is an explicit maintenance operation and can
overwrite later JSON edits.

Enemy Energy:
Each enemy has editable Current Energy, Maximum Energy, and EPT (Energy Per
Turn). Selecting a Zoid starts it at half maximum Energy, rounded down.
Start Turn adds EPT up to maximum, then pays upkeep for active shields and
invisibility equipment. If the Energy after recharge cannot pay all upkeep,
the turn action changes nothing; deactivate equipment and try again.
Rest sets Energy to half maximum, even
when the current value is higher. Each weapon's Use button spends its editable
Energy Cost; insufficient Energy or an invalid cost leaves Energy unchanged.
Economized Shooting ranks 1-4 reduce Ranged costs by 2/4/6/8 (minimum 2).
Costs already below 2 remain unchanged.
Up to eight rows display fixed weapons and Zoid-specific removable equipment.
Equipment effects and GM stat adjustments are managed through editable fields.
Maximum Energy is base Zoid Energy + actual Level + manual equipment/GM bonuses.
Type abilities' bonus levels do not contribute. Changing Level adjusts maximum
Energy by the level difference, preserving manual bonuses and EPT. It does not
refill Energy; reducing the maximum clamps current Energy when necessary.
Older Energy-enabled saved sets gain the actual-level bonus once on load,
preserving recorded current Energy and manual maximum-Energy adjustments.
Saved sets retain Energy, EPT, costs, and weapon visibility. Older sets gain
half-maximum Energy and catalog costs matched by weapon name while retaining
saved HP and manual edits. Unknown custom weapons need a GM-entered cost.
The bundled catalog includes Energy rules for Zoids and transports; legacy
Heat provenance in catalog metadata is historical only.
To refresh catalog data from the sibling Character Sheet app, run:
  python3 tools/sync_character_energy.py
This sync retains the Encounter Tracker's required-level values.

Ability rules:
To refresh the revised abilities (76 ranks, including Small Expert's inherited
critical-hit protection and Counter Attack) from the Character Sheet:
  python3 tools/sync_character_abilities.py
Iron Defense, Fleet Footed, Expert to-hit, and Economized Shooting bonuses are
calculated automatically. Expert matching uses the same tags as the sheet:
Laser requires Laser, and Rifle requires both Ranged and Bullet. Only the
strongest matching Expert bonus applies (+2/+3/+4/+5).
Selected ability descriptions show the current rules, including cumulative
Smoke/Shield/Fleet perks and Expert critical hits (ranks 2/3/4: 19/18/18;
rank 4 critical hits deal double damage).
Anti-Air Pro, Evasion Master, Sniper, True Tank, shield damage-reduction rules,
critical hits, and multi-attack restrictions are GM-managed: the tracker has
no target/range or equipment-defense calculator.
Each equipment row has Active, Shield HP, and Grants invisibility controls.
Known shields/invisibility are filled from the catalog; custom gear can be
entered manually. Active shields add to one pool. Shield Master adds its
100/150/200/250 HP bonus once when the combined pool is positive.
Shield damage taken is tracked against this pool. Organoid shield HP has no
upkeep; each other active shield/invisibility item pays its displayed Energy
Cost per Start Turn (only once if it grants both). Smoke alone has no upkeep.
Deactivate expired/destroyed equipment explicitly. Use still spends Energy
for an individual use; changing Active does not spend Energy immediately.
Shield damage, equipment activation, custom shield HP, invisibility flags, and
Organoid shields are saved with each enemy. Older sets default to inactive
equipment and zero shield damage; known shield HP is recovered by item name.
Armor/Defense +/- buttons change the stat by 1 and track a temporary modifier.
Rest removes these modifiers, preserving other manual edits. Modifiers survive
recalculation and saving/loading; selecting a new Zoid or clearing resets them.
Old saved sets retain their recorded numeric values; reselect the Zoid and
save again to refresh calculated values. Ability descriptions refresh on load.

Handbook corrections:
- Small Expert ranks 2-4 retain protection against critical hits from L or
  larger enemies. Counter Attack 2 triggers on an enemy roll of 5 or lower.
- Smoke Master coverage is +15/+15/+45/+45m. Ranged Multi Attack grants
  1/2/3/4 extra attacks as part of the attack action.
- AoE dodge: d20 + Reaction equal to or greater than the modified attack roll
  avoids half damage, rather than all damage. The card and weapon tooltips
  display this rule; rolls and damage resolution remain GM-managed.
- Normal OS level is half actual pilot level, rounded down (supported cap 40).
  The tracker uses manually entered Organoid bonuses and shield HP.
- Pit Stop takes one action for a CAS swap; return to battle on the next turn.
  CAS timing remains table-managed.

Current Zoid-specific gear:
- Lightning Saix: Slot 5 Pulse Laser Gun, damage 110, Energy 6.
- Lightning Saix BS: Slot 5 Pulse Laser Gun, damage 130, Energy 8.
- Command Wolf IS: Slot 5 Long Range Rifle, damage 130, Energy 6.
- Shadow Fox: Slot 5 Laser Vulcan Gun, damage 90, Energy 8; AoE 30m by 90m;
  Ranged, Laser, Close Range. Optical Camouflage remains in Slot 8.
Weapon-name tooltips show tags and effect descriptions. Empty removable slots
are hidden while preserving their slot numbers. Older saved enemy sets retain
their saved manual stats: reselect the Zoid to refresh its catalog loadout,
then save the set again.

To run tests (including headless Flet controls):
  .venv/bin/python -m unittest discover -s tests -q

Installing Release:
Download release and extract

To Build:
Uses Python3 and Flet

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
