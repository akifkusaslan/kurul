# -*- coding: utf-8 -*-
"""
KURUL arama cekirdegi.

Bu dosya ara.py'nin arama mantiginin BIREBIR tasinmis halidir.
Degisen tek sey: print yerine veri dondurmesi.

Korunan davranislar:
  * kulliyat/<koltuk>*.zip kaliboyla parcali zip okuma, zip ACILMADAN
  * terimlerin re.escape edilip OR'lanmasi, buyuk/kucuk harf duyarsiz
  * "--liste" = bolum basina eslesme sayisi, pasaj yok
  * pasaj = eslesmenin etrafindan pencere//2 karakter, cakisanlar elenir,
    bolum basina en fazla n pasaj
  * "--bolum" = dosya adinda alt-dize filtresi
  * "--oku" = tek bolumu bastan sona
Eklenmeyenler (bilerek): tokenizasyon, govdeleme, ters indeks,
embedding, semantik arama. Ilk surum duz regex/alt-dize aramasidir.
"""
from __future__ import annotations

import glob
import os
import re
import zipfile
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from indeks import IndeksKaydi, indeks_yukle, konuk_cikar

KOLTUKLAR: Dict[str, Dict[str, str]] = {
    "huberman":   {"ad": "Andrew Huberman",  "podcast": "Huberman Lab",           "tip": "koltuk"},
    "parrish":    {"ad": "Shane Parrish",    "podcast": "The Knowledge Project",  "tip": "koltuk"},
    "harbinger":  {"ad": "Jordan Harbinger", "podcast": "The Jordan Harbinger Show", "tip": "koltuk"},
    "richroll":   {"ad": "Rich Roll",        "podcast": "The Rich Roll Podcast",  "tip": "koltuk"},
    "sinancanan": {"ad": "Sinan Canan",      "podcast": "Acik Beyin (TURKCE)",    "tip": "koltuk"},
    "williamson": {"ad": "Chris Williamson", "podcast": "Modern Wisdom",          "tip": "kutuphane"},
}


@dataclass
class Bolum:
    koltuk: str
    dosya: str
    tarih: str
    metin: str
    baslik: Optional[str] = None
    url: Optional[str] = None
    konuk: Optional[str] = None
    kelime: Optional[int] = None


@dataclass
class Kulliyat:
    veri_dizini: str
    bolumler: Dict[str, List[Bolum]] = field(default_factory=dict)
    koltuk_tanimlari: Dict[str, str] = field(default_factory=dict)

    # ---------- yukleme ----------

    def _zip_kaynaklari(self, koltuk: str) -> List[str]:
        base = os.path.join(self.veri_dizini, "kulliyat")
        kaynaklar = sorted(glob.glob(os.path.join(base, koltuk + "*.zip")))
        klasor = os.path.join(base, koltuk)
        if os.path.isdir(klasor):
            kaynaklar += [os.path.join(klasor, f) for f in sorted(os.listdir(klasor))]
        return kaynaklar

    def _ham_belgeler(self, koltuk: str) -> Iterable[Tuple[str, str]]:
        """ara.py docs() ile ayni: zip icini acmadan .txt oku, '_' ile baslayanlari atla."""
        for p in self._zip_kaynaklari(koltuk):
            if p.endswith(".zip"):
                with zipfile.ZipFile(p) as z:
                    for n in sorted(z.namelist()):
                        b = os.path.basename(n)
                        if n.endswith(".txt") and not b.startswith("_"):
                            yield b, z.read(n).decode("utf-8", "ignore")
            elif p.endswith(".txt") and not os.path.basename(p).startswith("_"):
                with open(p, encoding="utf-8", errors="ignore") as f:
                    yield os.path.basename(p), f.read()

    def yukle(self) -> None:
        for koltuk in KOLTUKLAR:
            kayitlar = indeks_yukle(self.veri_dizini, koltuk)
            liste: List[Bolum] = []
            for dosya, metin in self._ham_belgeler(koltuk):
                tarih = dosya[:8] if dosya[:8].isdigit() else ""
                kayit = _kayit_sec(kayitlar.get(tarih, []), dosya)
                baslik = kayit.baslik if kayit else None
                liste.append(Bolum(
                    koltuk=koltuk,
                    dosya=dosya,
                    tarih=tarih,
                    metin=metin,
                    baslik=baslik,
                    url=kayit.url if kayit else None,
                    konuk=konuk_cikar(koltuk, baslik) if baslik else None,
                    kelime=kayit.kelime if kayit else None,
                ))
            self.bolumler[koltuk] = liste
            self.koltuk_tanimlari[koltuk] = _tanim_oku(self.veri_dizini, koltuk)

    # ---------- arama ----------

    @staticmethod
    def _desen(kelimeler: List[str]) -> re.Pattern:
        return re.compile("|".join(re.escape(k) for k in kelimeler), re.I)

    def _bolum_havuzu(self, koltuk: str, bolum: Optional[str]) -> List[Bolum]:
        havuz = self.bolumler.get(koltuk, [])
        if bolum:
            alt = bolum.lower()
            havuz = [b for b in havuz if alt in b.dosya.lower()
                     or (b.baslik and alt in b.baslik.lower())]
        return havuz

    def ara(self, koltuk: str, kelimeler: List[str],
            bolum: Optional[str] = None, limit: int = 25) -> List[dict]:
        """ara.py --liste karsiligi: bolum basina eslesme sayisi, pasaj yok."""
        pat = self._desen(kelimeler)
        sonuc = []
        for b in self._bolum_havuzu(koltuk, bolum):
            eslesmeler = pat.findall(b.metin)
            if not eslesmeler:
                continue
            sonuc.append({
                **self._kaynak(b),
                "eslesme_sayisi": len(eslesmeler),
                "eslesen_terimler": _bulunan_terimler(kelimeler, b.metin),
            })
        sonuc.sort(key=lambda r: r["eslesme_sayisi"], reverse=True)
        return sonuc[:limit]

    def pasajlar(self, koltuk: str, kelimeler: List[str], bolum: Optional[str] = None,
                 n: int = 3, pencere: int = 500, limit: int = 20) -> List[dict]:
        """ara.py pasaj mantigi: pencere//2 sag/sol, cakisanlar elenir, bolum basina n."""
        pat = self._desen(kelimeler)
        cikti: List[dict] = []
        havuz = self._bolum_havuzu(koltuk, bolum)
        havuz = sorted(havuz, key=lambda b: len(pat.findall(b.metin)), reverse=True)
        for b in havuz:
            if len(cikti) >= limit:
                break
            metin = b.metin
            kullanilan: List[Tuple[int, int]] = []
            for m in pat.finditer(metin):
                if len(kullanilan) >= n or len(cikti) >= limit:
                    break
                s = max(0, m.start() - pencere // 2)
                e = min(len(metin), m.end() + pencere // 2)
                if any(s < ue and us < e for us, ue in kullanilan):
                    continue
                kullanilan.append((s, e))
                cikti.append({
                    **self._kaynak(b),
                    "pasaj": metin[s:e].replace("\n", " ").strip(),
                    "eslesen_terimler": _bulunan_terimler(kelimeler, metin[s:e]),
                })
        return cikti

    def bolum_metni(self, koltuk: str, tarih: str, sayfa: int, sayfa_boyutu: int):
        for b in self.bolumler.get(koltuk, []):
            if b.tarih == tarih:
                toplam = max(1, -(-len(b.metin) // sayfa_boyutu))
                sayfa = max(1, min(sayfa, toplam))
                bas = (sayfa - 1) * sayfa_boyutu
                return {
                    **self._kaynak(b),
                    "sayfa": sayfa,
                    "toplam_sayfa": toplam,
                    "karakter": len(b.metin),
                    "metin": b.metin[bas:bas + sayfa_boyutu],
                }
        return None

    def _kaynak(self, b: Bolum) -> dict:
        meta = KOLTUKLAR[b.koltuk]
        return {
            "koltuk": b.koltuk,
            "tip": meta["tip"],
            "podcast": meta["podcast"],
            "tarih": b.tarih,
            "baslik": b.baslik or b.dosya[11:-4],
            "konuk": b.konuk,
            "url": b.url,
        }


def _bulunan_terimler(kelimeler: List[str], metin: str) -> List[str]:
    alt = metin.lower()
    return [k for k in kelimeler if k.lower() in alt]


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _kayit_sec(kayitlar: List[IndeksKaydi], dosya: str) -> Optional[IndeksKaydi]:
    """Ayni tarihte birden fazla bolum varsa baslik benzerligiyle ayir."""
    if not kayitlar:
        return None
    if len(kayitlar) == 1:
        return kayitlar[0]
    hedef = _normalize(dosya[11:-4])
    en_iyi, en_skor = kayitlar[0], -1.0
    for k in kayitlar:
        aday = _normalize(k.baslik)
        ortak = sum(1 for i in range(0, len(aday), 4) if aday[i:i + 4] and aday[i:i + 4] in hedef)
        skor = ortak / max(1, len(aday) // 4)
        if skor > en_skor:
            en_iyi, en_skor = k, skor
    return en_iyi


def _tanim_oku(veri_dizini: str, koltuk: str) -> str:
    for p in sorted(glob.glob(os.path.join(veri_dizini, "koltuklar", "*.md"))):
        if koltuk in os.path.basename(p).lower():
            with open(p, encoding="utf-8", errors="ignore") as f:
                return f.read()
    return ""
