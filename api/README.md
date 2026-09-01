# KURUL Search API

ChatGPT (Custom GPT Action) ve baska istemcilerin KURUL kulliyatinda arama
yapabilmesi icin FastAPI servisi. 2.414 bolum, ~45,2 milyon kelime.

**Bu servis yalnizca kendi yukledigi KURUL verisini tarar. Internete cikmaz,
disariya hicbir HTTP cagrisi yapmaz. Zip dosyalarini istemciye acmaz.**

## Tasarim ilkesi

`../ara.py` icindeki arama mantigi **birebir** tasinmistir:

* `kulliyat/<koltuk>*.zip` parcali zip'leri, zip **acilmadan** okunur
* terimler `re.escape` edilip OR'lanir, buyuk/kucuk harf duyarsiz
* `/ara` = `--liste` (bolum basina eslesme sayisi, pasaj yok)
* `/pasajlar` = pasaj mantigi (pencere//2 sag/sol, **cakisanlar elenir**,
  bolum basina en fazla `n` pasaj)
* `/bolum` = `--oku`, ama **sayfali**

Bilerek eklenmeyenler: tokenizasyon, govdeleme, ters indeks, embedding,
vektor veritabani, semantik arama. Ilk surum duz regex/alt-dize aramasidir.
Bu sayede `"tactical empathy"` gibi cok kelimeli ifadeler dogal calisir.

## Endpoint'ler

| Metot | Yol | Ne yapar |
|---|---|---|
| GET | `/saglik` | Servis durumu, yuklu bolum sayilari. **Anahtar gerektirmez.** |
| GET | `/koltuklar` | 5 koltuk + tip + bolum sayisi (`?tanim=true` ile tanim metni) |
| POST | `/ara` | Bolum daraltma. Pasaj DONDURMEZ. |
| POST | `/pasajlar` | Asil kaynak okuma. En fazla 30 pasaj. |
| GET | `/bolum` | Tek bolumu sayfali oku (`koltuk`, `tarih=YYYYAAGG`, `sayfa`) |

`/saglik` disindaki her uc `X-API-Key` basligi ister.

### Onerilen akis (iki asama)

```
1) POST /ara        -> hangi bolumler ilgili, kac kez geciyor
2) POST /pasajlar   -> sadece o bolumlerden pasaj cek  (bolum: "Terry Real")
3) GET  /bolum      -> gerekirse tek bolumu bastan sona (sayfali)
```

### Sonuc alanlari

Her sonuc: `koltuk`, `tip` (koltuk/kutuphane), `podcast`, `tarih`, `baslik`,
`konuk`, `url`, `eslesen_terimler`, ayrica `/ara`'da `eslesme_sayisi`,
`/pasajlar`'da `pasaj`.

Sonuc yoksa `{"found": false, "mesaj": "..."}` doner.

### Konuk alani

Konuk adi bolum basligindan cikarilir. Cikarilamayan bolumlerde **`null`**
doner — asla uydurulmaz. Gercek oranlar:

| koltuk | konuk cikarilan |
|---|---|
| harbinger | %91 |
| parrish | %71 |
| huberman | %64 |
| williamson | %61 |
| richroll | %41 |

Dusuk oranlar bir hata degil: Q&A, solo bolum ve yillik derlemelerin konugu
yoktur. `konuk: null` gelen bir sonuca "X sunu dedi" diye atif yapilmamalidir.

## Guvenlik

* `KURUL_API_KEY` **environment/secret** olarak okunur. Kodda, depoda ve bu
  dosyada **yoktur**.
* Secret tanimli degilse `/saglik` disindaki tum uclar `503` doner.
* Yanlis/eksik anahtar `401` doner.
* Zip dosyalarina veya dosya sistemine dogrudan erisim ucu yoktur.

## Yerel calistirma

```bash
pip install -r requirements.txt
export KURUL_VERI_DIZINI=/depo/kok/dizini     # kulliyat/ ve koltuklar/ burada
export KURUL_API_KEY=kendi-anahtarin
uvicorn main:app --port 7860
```

## Testler

```bash
KURUL_VERI_DIZINI=/depo/kok KURUL_API_KEY=test pytest -q
```

16 test: saglik, 5 koltugun yuklenmesi, anahtarsiz erisim reddi, basit arama,
phrase arama, --liste esdegeri, pasaj cikarma, cakisan pasajlarin elenmesi,
tarih->indeks eslestirmesi, indeksin sagdan ayristirilmasi, Williamson konuk
cikarma, konuk yoksa null, Williamson'in kutuphane olarak isaretlenmesi,
found=false, /bolum sayfalama, limit tavanlari.

## Deploy — Hugging Face Spaces (Docker)

1. huggingface.co uzerinde **New Space** -> SDK: **Docker** -> Blank
2. Bu klasordeki dosyalari Space'e yukle (`Dockerfile` kokte olmali)
3. Space **Settings -> Variables and secrets** -> **New secret**:
   `KURUL_API_KEY` = kendi urettigin uzun rastgele dize
4. Build bitince `https://<kullanici>-<space>.hf.space/saglik` adresini ac;
   `auth_yapilandirildi: true` ve 2.414 bolum gorunmeli
5. `openapi.json` icindeki `servers[0].url` alanini gercek adresle degistir
6. ChatGPT -> Custom GPT -> Actions -> `openapi.json` icerigini yapistir;
   Authentication: **API Key**, Auth Type: **Custom**, Header: `X-API-Key`

Dockerfile kulliyati build sirasinda public GitHub deposundan ceker; kulliyat
guncellendiginde Space'i yeniden build etmek yeterlidir.

## Performans (olculdu)

| | |
|---|---|
| Acilista yukleme | ~3,3 sn (13 zip -> bellek) |
| Bellek | ~254 MB |
| Tum kulliyatta arama | 1,3–2,2 sn |
| Tek koltukta arama | 0,3–0,9 sn |
