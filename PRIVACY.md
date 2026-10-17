# Gizlilik / Privacy

*English below.*

## Türkçe

libzie bilgisayarında yerel çalışır. Geliştirici olarak senden hiçbir veri toplamam; hesap, analiz (telemetri) ya da reklam yoktur.

**Bilgisayarında kalanlar:** ders dosyaların (varsayılan `Belgeler\libzie\materials`), ayarların (`%APPDATA%\libzie`), küçük resim önbelleği ve tarayıcı tarafındaki tercihlerin (tema, dil, açık sekmeler). Sunucu yalnızca `127.0.0.1` adresini dinler, ağdan erişilemez.

**İnternete çıkan iki istek (ikisi de kapatılabilir):**

| Özellik | Kime gider | Ne gider | Nasıl kapatılır |
|---|---|---|---|
| Hava durumu | [Open-Meteo](https://open-meteo.com/) | Seçtiğin şehrin adı ve konumu; ağ gereği IP adresin | Şehir seçme |
| Sürüm denetimi / otomatik güncelleme | GitHub (bu deponun sürümleri) | "Son sürüm nedir?" sorusu; ağ gereği IP adresin | Ayarlar → Hakkında'da otomatik güncelleme kutusunu kaldır (elle denetle düğmesine basmadıkça sorgu yapılmaz; kutu açıksa açılışta bir kez) |

Bu servisler kendi gizlilik politikalarına tabidir. Dosya içeriğin, dosya adların ya da ders adların hiçbir zaman gönderilmez.

Sorular için: bu depoda bir issue aç.

## English

libzie runs locally on your computer. I, as the developer, collect no data from you: no accounts, no analytics (telemetry), no ads.

**Stays on your computer:** your course files (by default `Documents\libzie\materials`), settings (`%APPDATA%\libzie`), the thumbnail cache and browser-side preferences (theme, language, open tabs). The server listens on `127.0.0.1` only and is not reachable from the network.

**Two requests that leave your computer (both optional):**

| Feature | Sent to | What is sent | How to turn off |
|---|---|---|---|
| Weather | [Open-Meteo](https://open-meteo.com/) | The city you chose (name and location); your IP address, as with any network request | Don't pick a city |
| Update check / auto-update | GitHub (this repository's releases) | A "what is the latest version?" request; your IP address | Untick auto-update in Settings → About (no request is made unless you press the check button; if ticked, one check on startup) |

These services are governed by their own privacy policies. Your file contents, file names and course names are never sent.

Questions: open an issue in this repository.
