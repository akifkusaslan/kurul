# -*- coding: utf-8 -*-
"""
KURUL Search API — ChatGPT Custom GPT Action icin.

Bu servis SADECE kendi yukledigi KURUL kulliyatini tarar.
Disariya (internete, arama motorlarina) hicbir HTTP cagrisi yapmaz.
Zip dosyalari istemciye acilmaz veya indirtilmez.
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from kurul_arama import KOLTUKLAR, Kulliyat

SURUM = "1.0.0"
VERI_DIZINI = os.environ.get("KURUL_VERI_DIZINI", "/data")
API_ANAHTARI = os.environ.get("KURUL_API_KEY")  # secret'tan okunur, kodda YOK

kulliyat: Optional[Kulliyat] = None
_yukleme_sn = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global kulliyat, _yukleme_sn
    t = time.time()
    k = Kulliyat(VERI_DIZINI)
    k.yukle()
    kulliyat = k
    _yukleme_sn = round(time.time() - t, 2)
    yield


app = FastAPI(
    title="KURUL Search API",
    version=SURUM,
    description=(
        "Mehmet'in danisma kurulu — 5 podcast kulliyatinda (2.414 bolum, ~45,2M kelime) "
        "duz metin aramasi. Yalnizca kulliyattan sonuc doner; internete cikmaz."
    ),
    lifespan=lifespan,
)


def yetki(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    if not API_ANAHTARI:
        raise HTTPException(503, "Servis yapilandirilmamis: KURUL_API_KEY secret'i tanimli degil.")
    if x_api_key != API_ANAHTARI:
        raise HTTPException(401, "Gecersiz veya eksik X-API-Key.")


def _hazir() -> Kulliyat:
    if kulliyat is None:
        raise HTTPException(503, "Kulliyat henuz yuklenmedi.")
    return kulliyat


def _koltuk_dogrula(koltuk: str) -> str:
    k = koltuk.strip().lower()
    if k not in KOLTUKLAR:
        raise HTTPException(400, f"Bilinmeyen koltuk: {koltuk}. Gecerli: {', '.join(KOLTUKLAR)}")
    return k


# ---------------- semalar ----------------

class AraIstek(BaseModel):
    koltuk: str = Field(..., description="huberman | parrish | harbinger | richroll | williamson")
    kelimeler: List[str] = Field(..., min_length=1, max_length=8,
                                 description="Aranacak terimler (INGILIZCE). OR'lanir. Cok kelimeli ifade desteklenir.")
    bolum: Optional[str] = Field(None, description="Sadece adinda bu gecen bolumlerde ara")
    limit: int = Field(25, ge=1, le=100)


class PasajIstek(BaseModel):
    koltuk: str
    kelimeler: List[str] = Field(..., min_length=1, max_length=8)
    bolum: Optional[str] = None
    n: int = Field(3, ge=1, le=10, description="Bolum basina pasaj sayisi")
    pencere: int = Field(500, ge=200, le=2000, description="Pasaj genisligi, karakter")
    limit: int = Field(20, ge=1, le=30, description="Toplam pasaj tavani")


# ---------------- uclar ----------------

@app.get("/saglik", summary="Servis durumu", operation_id="saglik")
def saglik():
    k = kulliyat
    return {
        "durum": "ayakta" if k else "yukleniyor",
        "surum": SURUM,
        "auth_yapilandirildi": bool(API_ANAHTARI),
        "yukleme_sn": _yukleme_sn,
        "bolum_sayisi": {ad: len(k.bolumler.get(ad, [])) for ad in KOLTUKLAR} if k else {},
    }


@app.get("/koltuklar", summary="Koltuklari ve tanimlarini listele",
         operation_id="koltuklar", dependencies=[Depends(yetki)])
def koltuklar(tanim: bool = Query(False, description="Koltuk tanim metnini de dondur")):
    k = _hazir()
    cikti = []
    for ad, meta in KOLTUKLAR.items():
        satir = {
            "koltuk": ad,
            "ad": meta["ad"],
            "podcast": meta["podcast"],
            "tip": meta["tip"],
            "bolum_sayisi": len(k.bolumler.get(ad, [])),
        }
        if tanim:
            satir["tanim"] = k.koltuk_tanimlari.get(ad, "")
        cikti.append(satir)
    return {"koltuklar": cikti,
            "not": "williamson bir koltuk degil KUTUPHANEDIR; cevap vermez, kim ne demis onu gosterir."}


@app.post("/ara", summary="Bolum daraltma (ara.py --liste karsiligi)",
          operation_id="ara", dependencies=[Depends(yetki)])
def ara(istek: AraIstek):
    k = _hazir()
    koltuk = _koltuk_dogrula(istek.koltuk)
    sonuc = k.ara(koltuk, istek.kelimeler, istek.bolum, istek.limit)
    if not sonuc:
        return {"found": False, "koltuk": koltuk, "aranan": istek.kelimeler,
                "mesaj": "Bu terimler bu koltukta gecmiyor. Kulliyat disindan cevap uretme."}
    return {"found": True, "koltuk": koltuk, "aranan": istek.kelimeler,
            "bolum_sayisi": len(sonuc), "bolumler": sonuc}


@app.post("/pasajlar", summary="Pasaj getir (ara.py pasaj mantigi)",
          operation_id="pasajlar", dependencies=[Depends(yetki)])
def pasajlar(istek: PasajIstek):
    k = _hazir()
    koltuk = _koltuk_dogrula(istek.koltuk)
    sonuc = k.pasajlar(koltuk, istek.kelimeler, istek.bolum,
                       istek.n, istek.pencere, istek.limit)
    if not sonuc:
        return {"found": False, "koltuk": koltuk, "aranan": istek.kelimeler,
                "mesaj": "Bu terimler bu koltukta gecmiyor. Kulliyat disindan cevap uretme."}
    return {"found": True, "koltuk": koltuk, "aranan": istek.kelimeler,
            "pasaj_sayisi": len(sonuc), "pasajlar": sonuc}


@app.get("/bolum", summary="Tek bolumu sayfali oku (ara.py --oku karsiligi)",
         operation_id="bolum", dependencies=[Depends(yetki)])
def bolum(koltuk: str = Query(...), tarih: str = Query(..., description="YYYYAAGG"),
          sayfa: int = Query(1, ge=1),
          sayfa_boyutu: int = Query(12000, ge=2000, le=20000)):
    k = _hazir()
    kol = _koltuk_dogrula(koltuk)
    sonuc = k.bolum_metni(kol, tarih.strip(), sayfa, sayfa_boyutu)
    if sonuc is None:
        return {"found": False, "koltuk": kol, "tarih": tarih,
                "mesaj": "Bu tarihte bolum yok."}
    return {"found": True, **sonuc}
