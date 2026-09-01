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


def indeks_yukle(veri_dizini: str, koltuk: str) -> Dict[str, List[IndeksKaydi]]:
    yol = os.path.join(veri_dizini, "kulliyat", f"{koltuk}_INDEKS.txt")
    kayitlar: Dict[str, List[IndeksKaydi]] = {}
    if not os.path.exists(yol):
        return kayitlar
    with open(yol, encoding="utf-8", errors="ignore") as f:
        satirlar = f.read().splitlines()
    basladi = False
    for ln in satirlar:
        s = ln.strip()
        if not basladi:
            # ayirici cizgiden sonra basla (williamson'da fazladan baslik satiri var)
            if s and set(s) == {"-"}:
                basladi = True
            continue
        if not s:
            continue
        parcalar = [p.strip() for p in s.split("|")]
        if len(parcalar) < 4:
            continue
        tarih = parcalar[0]
        if not (len(tarih) == 8 and tarih.isdigit()):
            continue
        kelime_ham = parcalar[-1]
        url = parcalar[-2] or None
        baslik = " | ".join(parcalar[1:-2]).strip()
        try:
            kelime = int(kelime_ham.replace(",", "").replace(".", ""))
        except ValueError:
            kelime = None
        kayitlar.setdefault(tarih, []).append(IndeksKaydi(tarih, baslik, url, kelime))
    return kayitlar


# ---------------- konuk adi ----------------

_GECERSIZ = re.compile(r"[?!\"]|^\d|episode|podcast|q&a|lessons|part\s*\d|toolkit|ama\s*#",
                       re.I)
_EKLER = re.compile(r"\s*\((4K|Audio|Members Only|Replay|Rerun)\)\s*$", re.I)


def _aday_gecerli(aday: str) -> bool:
    """Konuk adi gibi gorunuyor mu? Emin degilsek None doneriz - asla uydurmayiz."""
    if not aday:
        return False
    aday = aday.strip(" -–—|:")
    if len(aday) < 3 or len(aday) > 60:
        return False
    if _GECERSIZ.search(aday):
        return False
    kelime = aday.split()
    if not (1 <= len(kelime) <= 5):
        return False
    # en az bir kelime buyuk harfle baslamali
    return any(k[:1].isupper() for k in kelime if k)


def konuk_cikar(koltuk: str, baslik: Optional[str]) -> Optional[str]:
    """Basliktan konuk adi cikarir. Cikaramazsa None - uydurmaz."""
    if not baslik:
        return None
    b = _EKLER.sub("", baslik).strip()

    adaylar: List[str] = []
    if koltuk == "williamson":
        # "Konu - Konuk"  (1102 bolumun 861'i bu kalipta; kalani Q&A/solo/derleme)
        if " - " in b:
            adaylar.append(b.rsplit(" - ", 1)[1])
    elif koltuk in ("huberman", "harbinger", "parrish", "richroll"):
        if "|" in b:
            adaylar.append(b.rsplit("|", 1)[1])
        if " - " in b:
            adaylar.append(b.rsplit(" - ", 1)[1])
        if ":" in b:
            adaylar.append(b.split(":", 1)[0])

    for aday in adaylar:
        temiz = _EKLER.sub("", aday).strip(" -–—|:")
        if _aday_gecerli(temiz):
            return temiz
    return None
