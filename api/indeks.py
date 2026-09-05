# -*- coding: utf-8 -*-
"""
_INDEKS.txt ayristirma ve konuk adi cikarma.

Indeks satiri:  tarih | baslik | video | kelime
DIKKAT: baslik icinde '|' olabilir. Ornek (harbinger):
  20180420 | Body Language Expert: "..." | Vanessa Van Edwards | https://... | 10200
Bu yuzden SAGDAN ayristirilir:
  ilk alan        -> tarih
  son alan        -> kelime sayisi
  sondan ikinci   -> URL
  aradaki her sey -> baslik
Tarih birincil eslestirme anahtaridir (2.414/2.414 bolum tarihle eslesiyor).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class IndeksKaydi:
    tarih: str
    baslik: str
    url: Optional[str]
    kelime: Optional[int]


def _satir_coz(parcalar):
    """Bir indeks satirini bicimden bagimsiz coz.

    Iki bicim var:
      A (01-05):  tarih | baslik | video | kelime        tarih = YYYYAAGG
      B (06):     no | tarih | kelime | link | baslik    tarih = YYYY-AA-GG

    Ortak yontem: tarihi, URL'yi ve sayilari nerede olurlarsa bul;
    geriye kalan en uzun metin basliktir.
    """
    tarih = url = None
    kelime = None
    kalan = []
    for p in parcalar:
        d = p.strip()
        if not d:
            continue
        if tarih is None:
            if len(d) == 8 and d.isdigit():
                tarih = d; continue
            m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", d)
            if m:
                tarih = m.group(1) + m.group(2) + m.group(3); continue
        if url is None and d.startswith(("http://", "https://")):
            url = d; continue
        sayi = d.replace(",", "").replace(".", "")
        if kelime is None and sayi.isdigit() and len(sayi) <= 8:
            # sira numarasi da sayidir; kelime sayisi genelde daha buyuk olur
            kalan.append(("sayi", int(sayi)))
            continue
        kalan.append(("metin", d))

    sayilar = [v for t, v in kalan if t == "sayi"]
    metinler = [v for t, v in kalan if t == "metin"]
    if sayilar:
        kelime = max(sayilar)          # sira no degil, kelime sayisi
    baslik = " | ".join(metinler).strip()
    return tarih, baslik, url, kelime


def indeks_yukle(veri_dizini: str, koltuk: str):
    yol = os.path.join(veri_dizini, "kulliyat", f"{koltuk}_INDEKS.txt")
    kayitlar = {}
    if not os.path.exists(yol):
        return kayitlar
    with open(yol, encoding="utf-8", errors="ignore") as f:
        satirlar = f.read().splitlines()
    basladi = False
    for ln in satirlar:
        s = ln.strip()
        if not basladi:
            if s and set(s) <= {"-"} and len(s) > 10:
                basladi = True
            continue
        if not s or "|" not in s:
            continue
        tarih, baslik, url, kelime = _satir_coz(s.split("|"))
        if not tarih or not baslik:
            continue
        kayitlar.setdefault(tarih, []).append(IndeksKaydi(tarih, baslik, url, kelime))
    return kayitlar


# ---------------- konuk adi ----------------

# Konuk DEGIL: dizi/seri adlari, bolum turleri, program adlari
_SERI = re.compile(
    r"guest series|huberman lab|knowledge project|modern wisdom|jordan harbinger|"
    r"\bjhs\b|roll on|rollback|best of|rewind|\bfull\b|interview|"
    r"\bep\b|episode|podcast|\bq&a\b|lessons|toolkit|\bama\b|"
    r"live event|journal club|mostly wise|\bpart\b|\bvol\b", re.I)

_GECERSIZ = re.compile(r"[?!\"#]|\d")
_EKLER = re.compile(r"\s*\((4K|Audio|Members Only|Replay|Rerun|Full)\)\s*$", re.I)
_UNVAN = re.compile(r"^(dr|dr\.|prof|prof\.|professor|sir)\b", re.I)


def _aday_gecerli(aday: str) -> bool:
    """Konuk adi gibi gorunuyor mu? Emin degilsek None doneriz - asla uydurmayiz."""
    if not aday:
        return False
    aday = aday.strip(" -–—|:")
    if not (3 <= len(aday) <= 60):
        return False
    if _GECERSIZ.search(aday):          # rakam, soru/unlem, tirnak -> baslik parcasi
        return False
    if _SERI.search(aday):              # seri/program adi -> konuk degil
        return False
    if " x " in f" {aday.lower()} ":    # "Julie Piatt X Rich Roll" gibi ortak bolumler
        return False
    kelime = aday.split()
    if not (1 <= len(kelime) <= 5):
        return False
    if aday == aday.upper() and len(aday) > 4:   # "ROLL ON", "PATIENCE IS EVERYTHING"
        return False
    # en az iki buyuk harfli kelime, ya da unvanla baslayan tek isim
    buyuk = sum(1 for x in kelime if x[:1].isupper())
    if _UNVAN.match(aday):
        return buyuk >= 2
    return buyuk >= 2


def konuk_cikar(koltuk: str, baslik: str = None):
    """Basliktan konuk adi cikarir. Cikaramazsa None doner - asla uydurmaz."""
    if not baslik:
        return None
    b = _EKLER.sub("", baslik).strip()
    # program adi kuyrugunu at:  "... | Rich Roll Podcast"
    b = re.sub(r"\s*\|\s*(Rich Roll Podcast|Huberman Lab.*|Modern Wisdom.*|"
               r"The Knowledge Project.*|JHS.*)\s*$", "", b, flags=re.I).strip()

    adaylar = []
    if koltuk == "williamson":
        # "Konu - Konuk"
        if " - " in b:
            adaylar.append(b.rsplit(" - ", 1)[1])
    elif koltuk == "richroll":
        # "... With/with/w/ Konuk"  ya da  "Konu: Konuk"  ya da  "Konuk: Konu"
        for ayirici in (" w/ ", " With ", " with "):
            if ayirici in b:
                adaylar.append(b.rsplit(ayirici, 1)[1])
        if ":" in b:
            sol, sag = b.split(":", 1)
            adaylar.append(sag)
            adaylar.append(sol)
        if " - " in b:
            adaylar.append(b.rsplit(" - ", 1)[1])
    else:  # huberman, harbinger, parrish
        if "|" in b:
            adaylar.append(b.rsplit("|", 1)[1])
        if " - " in b:
            adaylar.append(b.rsplit(" - ", 1)[1])
        if ":" in b:
            adaylar.append(b.split(":", 1)[0])

    for aday in adaylar:
        temiz = _EKLER.sub("", aday).strip(" -–—|:,")
        temiz = re.sub(r",\s*(MD|PhD|MS|RD|DO)\.?$", "", temiz, flags=re.I).strip()
        if _aday_gecerli(temiz):
            return temiz
    return None
