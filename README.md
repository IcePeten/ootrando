# Ocarina of Time Randomizer (Nintendo Switch 2 Edition)

A fan-made item randomizer for *The Legend of Zelda: Ocarina of Time* on Nintendo Switch 2 (title ID `0400486024DEC000`). It reads your own copy of the game and builds a LayeredFS mod folder for an emulator. It never contains or distributes game files.

## Please read first

- **Built with AI assistance.** Nearly all of this code was written with an AI coding assistant. The project owner directed the work and tested every change by playing it in the Lichii emulator. Expect rough edges.
- **Logic is new and still being play-tested.** The rules (`logic.py`) track child and adult Link separately, area by area, and are matched against the remake's own level data: each grotto's cover (Song of Storms, bombable, heavy rock, hammer rock) and what is inside it, each Gold Skulltula's type (bean patch, crate, tree or wall), dungeon rooms, and the remake's moved spots, such as Ruto's Letter at the bottom of Lake Hylia. Every seed is simulated to Ganon before it is accepted. It has not yet been confirmed by full playthroughs, so if a seed expects something you can't reach, please report it.
- **Not affiliated** with Nintendo or the N64 Ocarina of Time Randomizer project. See [CREDITS.md](CREDITS.md).

## What it does

- Shuffles chests, shop stock, NPC and minigame rewards, Gold Skulltula drops, Deku Scrub sales, songs, and optionally floor items, pots, crates, grass, beehives and rocks.
- Keysanity for small and boss keys. Each key names its dungeon.
- Gossip Stone hints, a spoiler log with landmark-based location names, pause-map markers that clear when collected, and check counts per area.
- Timesavers: skippable opening, no first-visit area flyovers, open forest, gate, door and fountain options.
- Cosmetics: tunic colors, plus the "Lank" and "Lunk" body swaps.

## How it works

| Piece | File |
|---|---|
| Reading the game (`.nup`, RomFS folders) | `game.py`, `nup.py`, `folder.py`, `formats.py` |
| File formats (BYML, SARC, MSBT, BNTX, BFRES) | `byml.py`, `sarc.py`, `msbt.py`, `bntx.py`, `bfres.py` |
| Item placement and logic | `randomizer.py`, `logic.py`, `npcs.py`, `keys.py`, `songs.py` |
| Placement data (locations, landmarks) | `data/*.json` |
| Writing the mod (resource size table, LayeredFS) | `mod.py` |
| Cosmetics and models | `cosmetics.py`, `models.py`, `texcodec.py`, `logo.py` |
| Website (runs the Python engine in the browser with Pyodide) | `web/`, `web_build/site/`, `webentry.py`, `build_site.py` |
| Desktop app | `studio.py`, `ui/` |

Item placement is assumed-fill: each progression item is placed only where it is reachable without it, and every seed is simulated to Ganon before it is accepted (unless No Logic is chosen).

Event scripts are edited with [evfl](https://github.com/leoetlino/evfl). The game uses the same file formats as *Tears of the Kingdom*, so public research from that modding community applied directly.

## Running it

You need your own legally dumped copy of the game.

```
pip install -r requirements.txt
python studio.py          # desktop app
python web_server.py      # local copy of the website at http://localhost:8000
python build_site.py      # build the static website into ../ootrando-site
```

The mod is written to your emulator's `load/0400486024DEC000/` (yuzu family) or `mods/contents/0400486024DEC000/` (Ryujinx family) folder. Start a new save after installing.

## Reporting logic problems

If a seed expects you to reach something you can't, send the settings string, the seed, where you got stuck, and the item you expected. Use the **Logic Problem** option in the website's feedback form, or open an issue.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE). This is required because the website bundles evfl (GPL-2.0-or-later). Third-party components keep their own licenses, listed in [CREDITS.md](CREDITS.md).

*The Legend of Zelda* and *Ocarina of Time* are trademarks of Nintendo. No game files are included in this repository.
