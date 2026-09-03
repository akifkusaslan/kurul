# KURUL

Mehmet'in danisma kurulu — bes koltuk + bir kutuphane. 3.676 bolum, ~48,9 milyon kelime.

| No | Koltuk | Alan | Bolum |
|---|---|---|---|
| 01 | Andrew Huberman | norobilim, duygu, saglik, kisisel gelisim | 330 |
| 02 | Shane Parrish (The Knowledge Project) | karar verme, muzakere, liderlik, is kurma | 116 |
| 04 | Jordan Harbinger | ikna, insan okuma, beden dili, manipulasyon savunmasi | 194 |
| 05 | Rich Roll | dipten donus, bagimlilik, aliskanlik, anlam | 672 |
| 06 | Sinan Canan (AcikBeyin) — TURKCE | kendini tanima, anlam, beyin, evrim, cocuk, modern hayat | 1.261 |
| — | Chris Williamson (Modern Wisdom) — KUTUPHANE | 1.000+ farkli konuk, celisen gorusler | 1.102 |

Kurallar `CLAUDE.md` icinde. Koltuk tanimlari `koltuklar/` altinda.

## Kullanim

```
python ara.py huberman "self-esteem" "shame" --liste
python ara.py richroll "addiction" "trauma" --n 5 --pencere 900
python ara.py harbinger "negotiation" "tactical empathy" --liste
python ara.py williamson "Jordan Peterson" --liste
python ara.py parrish "positioning" --bolum "Dunford"
python ara.py sinancanan "eksik benlik" "oz sabotaj" --liste
python ara.py richroll --oku "Gabor"
```

Kulliyat `kulliyat/` altinda parcali zip olarak durur; `ara.py` zip icini tarar,
acmaya gerek yoktur. Video linkleri `kulliyat/<koltuk>_INDEKS.txt` icinde.

## Dil

Koltuk 01/02/04/05 ve Williamson kutuphanesi INGILIZCE — orada Ingilizce ara.
Koltuk 06 (Sinan Canan) TURKCE — orada Turkce ara. Cevap her zaman Turkce yazilir.

## Notlar

- Parrish kulliyatinda bir bolum ("#1 Gut Expert", 23 Haz 2026) dosya adindaki
  bozuk karakter yuzunden aktarilamadi — 117 yerine 116 bolum.
- Sinan Canan kulliyati iki kanaldan derlendi: `@AcikBeyin` ve
  `@ProfDrSinanCananileAcikBeyin`. 1.263 bolumden 2'si elendi (biri bos altyazi,
  biri 48 kelimelik tanitim klibi). 1.261 bolumun tamami video linklidir.
