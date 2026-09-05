# -*- coding: utf-8 -*-
"""KURUL Search API testleri. Calistirma:  KURUL_VERI_DIZINI=<repo> pytest -q"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("KURUL_API_KEY", "test-anahtari")

import main  # noqa: E402
from indeks import indeks_yukle, konuk_cikar  # noqa: E402

VERI = os.environ.get("KURUL_VERI_DIZINI", "/data")
BASLIK = {"X-API-Key": os.environ["KURUL_API_KEY"]}


@pytest.fixture(scope="session")
def c():
    with TestClient(main.app) as client:
        yield client


# 1 — saglik
def test_saglik(c):
    r = c.get("/saglik")
    assert r.status_code == 200
    assert r.json()["durum"] == "ayakta"
    assert r.json()["auth_yapilandirildi"] is True


# 2 — koltuklarin tamami yuklendi mi
def test_koltuklar_yuklendi(c):
    say = c.get("/saglik").json()["bolum_sayisi"]
    # 06 (sinancanan) kayitli olmali; kulliyati depoda yoksa 0 bolum dondurur
    assert set(say) == {"huberman", "parrish", "harbinger",
                        "richroll", "sinancanan", "williamson"}
    assert say["huberman"] == 330
    assert say["parrish"] == 116
    assert say["harbinger"] == 194
    assert say["richroll"] == 672
    assert say["williamson"] == 1102


# 3 — API anahtarsiz erisim reddedilir
def test_anahtarsiz_reddedilir(c):
    assert c.get("/koltuklar").status_code == 401
    assert c.post("/ara", json={"koltuk": "huberman", "kelimeler": ["shame"]}).status_code == 401
    assert c.get("/koltuklar", headers={"X-API-Key": "yanlis"}).status_code == 401


# 4 — basit kelime aramasi
def test_basit_arama(c):
    r = c.post("/ara", json={"koltuk": "huberman", "kelimeler": ["self-esteem"]}, headers=BASLIK)
    d = r.json()
    assert d["found"] is True and d["bolumler"]
    assert any("Terry Real" in b["baslik"] for b in d["bolumler"])


# 5 — cok kelimeli ifade (phrase) aramasi
def test_phrase_arama(c):
    r = c.post("/ara", json={"koltuk": "harbinger", "kelimeler": ["tactical empathy"]}, headers=BASLIK)
    d = r.json()
    assert d["found"] is True
    assert all(b["eslesen_terimler"] == ["tactical empathy"] for b in d["bolumler"])


# 6 — --liste esdegeri: pasaj DONMEZ, sayim doner
def test_liste_pasaj_dondurmez(c):
    d = c.post("/ara", json={"koltuk": "parrish", "kelimeler": ["negotiation"]}, headers=BASLIK).json()
    for b in d["bolumler"]:
        assert "pasaj" not in b
        assert b["eslesme_sayisi"] >= 1
    sayilar = [b["eslesme_sayisi"] for b in d["bolumler"]]
    assert sayilar == sorted(sayilar, reverse=True)


# 7 — pasaj cikarma
def test_pasaj_cikarma(c):
    d = c.post("/pasajlar", json={"koltuk": "richroll", "kelimeler": ["addiction"],
                                  "n": 2, "pencere": 600, "limit": 10}, headers=BASLIK).json()
    assert d["found"] is True and 0 < len(d["pasajlar"]) <= 10
    for p in d["pasajlar"]:
        assert "addiction" in p["pasaj"].lower()
        assert len(p["pasaj"]) <= 600 + 40
        for alan in ("koltuk", "tip", "podcast", "tarih", "baslik", "url", "eslesen_terimler"):
            assert alan in p


# 8 — cakisan pasajlar elenir (ara.py davranisi)
def test_cakisan_pasajlar_elenir():
    import re
    from kurul_arama import Kulliyat
    k = main.kulliyat
    b = next(x for x in k.bolumler["huberman"] if "Terry Real" in (x.baslik or ""))
    pat = re.compile("shame", re.I)
    pencere, n = 800, 5
    kullanilan = []
    for m in pat.finditer(b.metin):
        if len(kullanilan) >= n:
            break
        s = max(0, m.start() - pencere // 2)
        e = min(len(b.metin), m.end() + pencere // 2)
        if any(s < ue and us < e for us, ue in kullanilan):
            continue
        kullanilan.append((s, e))
    for i in range(len(kullanilan) - 1):
        assert kullanilan[i][1] <= kullanilan[i + 1][0]


# 9 — tarih -> indeks eslestirmesi
def test_tarih_indeks_eslesmesi():
    k = main.kulliyat
    for koltuk in ("huberman", "parrish", "harbinger", "richroll", "williamson"):
        kayitlar = indeks_yukle(VERI, koltuk)
        bolumler = k.bolumler[koltuk]
        eslesen = sum(1 for b in bolumler if b.tarih in kayitlar)
        assert eslesen == len(bolumler), f"{koltuk}: {eslesen}/{len(bolumler)}"
        # Rich Roll'da iki bolumun indekste video linki yok (link alani "-")
        beklenen_urlsiz = 2 if koltuk == "richroll" else 0
        urlsiz = [b.dosya for b in bolumler if not b.url]
        assert len(urlsiz) == beklenen_urlsiz, urlsiz[:3]


# 10 — indeks SAGDAN ayristirilmali (baslik icinde '|' olabilir)
def test_indeks_sagdan_ayristirma():
    kayitlar = indeks_yukle(VERI, "harbinger")
    k = kayitlar["20180420"][0]
    assert k.url.startswith("https://www.youtube.com/")
    assert k.kelime == 10200
    assert "Vanessa Van Edwards" in k.baslik  # baslik icindeki '|' korunmus


# 11 — Williamson konuk cikarma
def test_williamson_konuk_cikar():
    assert konuk_cikar("williamson", "How Men Keep Sabotaging Themselves - Dr Robert Glover") == "Dr Robert Glover"
    assert konuk_cikar("williamson", "Why Fathers Matter - Dr Anna Machin") == "Dr Anna Machin"
    assert konuk_cikar("williamson", "44 Harsh Truths About The Game Of Life - Naval Ravikant (4K)") == "Naval Ravikant"


# 12 — konuk bulunamayinca None (asla uydurma)
def test_konuk_bulunamazsa_none():
    assert konuk_cikar("williamson", "500k Q&A - Casual Sex, Political Idiots & Depression") is None
    assert konuk_cikar("williamson", "14 Lessons from 5 Years Of Modern Wisdom") is None
    assert konuk_cikar("huberman", "Welcome to the Huberman Lab Podcast") is None


# 13 — Williamson kutuphane olarak isaretli
def test_williamson_kutuphane(c):
    d = c.get("/koltuklar", headers=BASLIK).json()
    tipler = {x["koltuk"]: x["tip"] for x in d["koltuklar"]}
    assert tipler["williamson"] == "kutuphane"
    assert all(tipler[x] == "koltuk" for x in ("huberman", "parrish", "harbinger", "richroll"))
    p = c.post("/pasajlar", json={"koltuk": "williamson", "kelimeler": ["nice guy"],
                                  "limit": 3}, headers=BASLIK).json()
    assert all(x["tip"] == "kutuphane" for x in p["pasajlar"])


# 14 — found=false
def test_found_false(c):
    saçma = "zzqxwvkurulyokboyle"
    for uc, govde in (("/ara", {"koltuk": "huberman", "kelimeler": [saçma]}),
                      ("/pasajlar", {"koltuk": "huberman", "kelimeler": [saçma]})):
        d = c.post(uc, json=govde, headers=BASLIK).json()
        assert d["found"] is False and "mesaj" in d
    d = c.get("/bolum", params={"koltuk": "huberman", "tarih": "19000101"}, headers=BASLIK).json()
    assert d["found"] is False


# 15 — /bolum sayfali
def test_bolum_sayfali(c):
    d = c.get("/bolum", params={"koltuk": "huberman", "tarih": "20251229",
                                "sayfa": 1, "sayfa_boyutu": 12000}, headers=BASLIK).json()
    assert d["found"] is True
    assert len(d["metin"]) <= 12000
    assert d["toplam_sayfa"] > 1
    d2 = c.get("/bolum", params={"koltuk": "huberman", "tarih": "20251229",
                                 "sayfa": 2, "sayfa_boyutu": 12000}, headers=BASLIK).json()
    assert d2["metin"] != d["metin"]


# 16 — limit tavanlari zorlanamaz
def test_limit_tavani(c):
    r = c.post("/pasajlar", json={"koltuk": "huberman", "kelimeler": ["the"], "limit": 999},
               headers=BASLIK)
    assert r.status_code == 422
