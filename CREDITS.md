# Credits

## Inspiration

- **[Ocarina of Time Randomizer](https://ootrandomizer.com)** ([source](https://github.com/OoTRandomizer/OoT-Randomizer)) for the Nintendo 64 game, and its contributors. The concept, and many options here, follow ideas they created or popularized: keysanity, song shuffle, Gossip Stone hints, open forest/gate/door/fountain settings, Gold Skulltula and scrub shuffle, traps, and logic built around "reachable without the item". No code, logic files or text from that project are included here. This project's logic was written separately, from knowledge of the original game, and checked against the remake's level files.
- **ZeldaSpeedRuns** and the wider Zelda speedrun and randomizer communities, for years of routing knowledge and entertainment.
- The **"Lank" and "Lonk/Lunk"** body swaps are a nod to the long-running community joke.

## Development

Written with an AI coding assistant, directed and play-tested by the project owner. Game data such as locations, event scripts and map layouts was found by reading the owner's own copy of the game.

## Third-party software

| Component | Use | License |
|---|---|---|
| [evfl](https://github.com/leoetlino/evfl) by leoetlino | Reading and writing event flowcharts | GPL-2.0-or-later |
| [astc-encoder](https://github.com/ARM-software/astc-encoder) by Arm | Texture encoding, compiled to WebAssembly for the site | Apache-2.0 |
| [Pyodide](https://pyodide.org) | Running the Python engine in the browser | MPL-2.0 |
| [python-zstandard](https://github.com/indygreg/python-zstandard) | Zstandard compression | BSD-3-Clause |
| [mmh3](https://github.com/hajimes/mmh3) | MurmurHash3 for game data hashes | MIT |
| [NumPy](https://numpy.org) | Image processing | BSD-3-Clause and others |
| [Pillow](https://python-pillow.org) | Image processing | MIT-CMU |
| [etcpak](https://github.com/K0lb3/etcpak) and [texture2ddecoder](https://github.com/K0lb3/texture2ddecoder) by K0lb3 | Texture encoding and decoding in the desktop app | MIT |
| [pywebview](https://pywebview.flowrl.com) | Desktop app window | BSD-3-Clause |
| TeX Gyre Pagella by GUST e-foundry | Title logo font | GUST Font License (see `fonts/`) |

## File format research

The game shares file formats with *The Legend of Zelda: Tears of the Kingdom*. Format knowledge comes from documentation and tools published by that modding community, including leoetlino's work on BYML, SARC, event flows and the resource size table.
