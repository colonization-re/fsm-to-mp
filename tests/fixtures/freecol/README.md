# FreeCol Map Fixtures

Real FreeCol `.fsm` maps are not committed here by default. They can be
downloaded with:

```bash
python scripts/download_test_maps.py
```

The script downloads from the FreeCol repository at commit
`db87a4da4a18af61a622a3781455090670436247` and verifies these SHA-256 hashes:

| file | size | map | SHA-256 |
| --- | ---: | --- | --- |
| `S_Caribbean_Phil.fsm` | 48 x 48 | small map, high seas/ocean/forests/elevation | `ab62beecd06199a4db81f3a829d5ded76b4da7bed5239597c22a0deab08135df` |
| `M_America_Mazim.fsm` | 40 x 180 | rivers, arctic, lakes, broad terrain coverage | `ca0d4c4db4237a3eccaab69b79f668a88c186d27dcf8ade585ea638a4b6fa401` |
| `XL_GigaEarth_Mazim.fsm` | 127 x 230 | unusual dimensions, many major rivers | `067e44f93164f6977ee3692ee6fb4a330f0258822b496f858e6cbd547b1b3fee` |

FreeCol source and packaged data are GPL-2.0-or-later per upstream source
headers and repository metadata. Keeping the downloader instead of vendoring the
maps avoids mixing those assets directly into this repository.
