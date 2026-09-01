# KURUL

Mehmet'in danisma kurulu — uc podcast kulliyati, 1.548 bolum, ~28,6 milyon kelime.

| Koltuk | Kim | Bolum |
|---|---|---|
| 01 | Andrew Huberman | 330 |
| 02 | Shane Parrish (The Knowledge Project) | 116 |
| — | Chris Williamson (Modern Wisdom) — KUTUPHANE | 1.102 |

Kurallar `CLAUDE.md` icinde. Koltuk tanimlari `koltuklar/` altinda.

## Kullanim

```
python ara.py huberman "self-esteem" "shame" --liste
python ara.py huberman "self-esteem" --n 5 --pencere 900
python ara.py williamson "Jordan Peterson" --liste
python ara.py parrish "negotiation" --bolum "Voss"
python ara.py huberman --oku "Terry Real"
```

Kulliyat `kulliyat/` altinda parcali zip olarak durur; `ara.py` zip icini tarar,
acmaya gerek yoktur. Video linkleri `kulliyat/<koltuk>_INDEKS.txt` icinde.
