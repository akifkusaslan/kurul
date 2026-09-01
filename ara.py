#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KURUL arama araci. Kulliyat kulliyat/ altinda parcali .zip olarak durur."""
import sys, os, re, glob, zipfile, argparse

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kulliyat")

def docs(koltuk):
    kaynaklar = sorted(glob.glob(os.path.join(BASE, koltuk + "*.zip")))
    klasor = os.path.join(BASE, koltuk)
    if os.path.isdir(klasor):
        kaynaklar += [os.path.join(klasor, f) for f in sorted(os.listdir(klasor))]
    if not kaynaklar:
        sys.exit("Koltuk bulunamadi: %s  (kulliyat/ icinde %s*.zip yok)" % (koltuk, koltuk))
    for p in kaynaklar:
        if p.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                for n in sorted(z.namelist()):
                    b = os.path.basename(n)
                    if n.endswith(".txt") and not b.startswith("_"):
                        yield b, z.read(n).decode("utf-8", "ignore")
        elif p.endswith(".txt") and not os.path.basename(p).startswith("_"):
            with open(p, encoding="utf-8", errors="ignore") as f:
                yield os.path.basename(p), f.read()

def main():
    ap = argparse.ArgumentParser(description="Kurul kulliyat arama araci")
    ap.add_argument("koltuk", help="huberman | parrish | williamson")
    ap.add_argument("kelimeler", nargs="*", help="aranacak kelimeler (Ingilizce)")
    ap.add_argument("--liste", action="store_true", help="pasaj basma; bolum + eslesme sayisi")
    ap.add_argument("--n", type=int, default=3, help="bolum basina pasaj (varsayilan 3)")
    ap.add_argument("--pencere", type=int, default=500, help="pasaj genisligi, karakter")
    ap.add_argument("--bolum", default=None, help="sadece adinda bu gecen bolumlerde ara")
    ap.add_argument("--oku", default=None, help="bu bolumu bastan sona bas")
    a = ap.parse_args()

    if a.oku:
        for ad, metin in docs(a.koltuk):
            if a.oku.lower() in ad.lower():
                print("=" * 90); print(ad); print("=" * 90); print(metin); return
        print("Bolum bulunamadi:", a.oku); return

    if not a.kelimeler:
        ap.error("en az bir kelime ver, ya da --oku kullan")

    pat = re.compile("|".join(re.escape(k) for k in a.kelimeler), re.I)
    toplam = bolum_sayisi = 0
    for ad, metin in docs(a.koltuk):
        if a.bolum and a.bolum.lower() not in ad.lower():
            continue
        ms = list(pat.finditer(metin))
        if not ms:
            continue
        toplam += len(ms); bolum_sayisi += 1
        if a.liste:
            print("%5d  %s" % (len(ms), ad)); continue
        print("=" * 90); print(ad); print("=" * 90)
        kullanilan = []
        for m in ms:
            s = max(0, m.start() - a.pencere // 2)
            e = min(len(metin), m.end() + a.pencere // 2)
            if any(s < ue and us < e for us, ue in kullanilan):
                continue
            kullanilan.append((s, e))
            print("...", metin[s:e].replace("\n", " "), "...\n")
            if len(kullanilan) >= a.n:
                break
    if a.liste:
        print("\nTOPLAM: %d eslesme / %d bolum" % (toplam, bolum_sayisi))

if __name__ == "__main__":
    main()
