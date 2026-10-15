# libzie

Ders notlarını, slaytları ve PDF'leri derse göre düzenleyen, bilgisayarında yerel çalışan küçük bir arşiv. Dosyalar senin klasörlerinde durur; libzie onları ders karoları, küçük resimler ve sekmeli PDF görüntüleyiciyle gösterir. Hesap, bulut ya da veritabanı yok.

> Arayüz Türkçedir. Şimdilik Windows için yazıldı.

![Ana sayfa: dersler rafta kitaplar olarak](assets/ekran-ana-sayfa.png)

![Ders sayfası: sekmeli dosya kartları ve PDF küçük resimleri](assets/ekran-ders.png)

*Ekran görüntülerindeki dersler ve dosyalar örnek amaçlı uydurma verilerdir.*

## Özellikler

- Klasörler = dersler: Gezgin'e eklediğin dosya kendiliğinden görünür, içe aktarma yok.
- Sürükle-bırakla yükleme (klasör dahil), taşıma, yeniden adlandırma, "Geri al" ile yumuşak silme.
- PDF'ler sayfa içinde sekmelerde açılır; PDF'lerin ilk sayfası küçük resim olur.
- Türkçe karakterden bağımsız arama (`isletim` → "İşletim"), `Ctrl+K` ile tüm derslerde hızlı arama.
- Tam klavye kullanımı (`?` kısayolları gösterir), `F` ile tam ekran, `Ctrl+B` ile kenar çubuğu.
- Tamamen çevrimdışı çalışır. İnternete çıkan tek şey isteğe bağlı hava durumu (Open-Meteo, şehri sen yazarsın).

## Kurulum (Windows uygulaması)

1. [Releases](https://github.com/nopescope0/libzie/releases) sayfasından en son `libzie.exe` dosyasını indir.
2. İstediğin bir klasöre koy (örneğin masaüstü) ve çalıştır. Kurulum gerekmez.

İlk açılışta Windows "bilgisayarınızı korudu" uyarısı verebilir: uygulama imzasız olduğu için normaldir. **Daha fazla bilgi → Yine de çalıştır**'a tıkla.

Dersler `Belgeler\libzie\kaynaklar` klasöründe, ayarlar `%APPDATA%\libzie` içinde tutulur; uygulama klasörünü silsen ya da güncellesen de verilerin kalır. Başka bir klasör kullanmak istersen uygulamada **Ayarlar**'dan seç. Uygulama Windows'taki Edge WebView2 bileşenini kullanır (Windows 10/11'de genellikle hazır gelir).

## Kaynak koddan çalıştırma

[Python 3](https://www.python.org/downloads/) kurulu olmalı. Başka bir şey gerekmez (bağımlılık ve derleme yok).

```
git clone https://github.com/nopescope0/libzie.git
cd libzie
python server.py
```

ya da klasördeki `baslat.bat` dosyasına çift tıkla. Tarayıcıda `http://127.0.0.1:8765` açılır. Sunucu yalnızca kendi bilgisayarına bağlanır, ağdan erişilemez. Bu yolda dersler proje içindeki `kaynaklar/` klasöründe durur.

Seçenekler:

- `python server.py --no-browser`: tarayıcıyı otomatik açma.
- `$env:PORT=9000` (PowerShell) ya da `set PORT=9000` (cmd), sonra `python server.py`: başka bir port kullan.

## Ders klasörün

Kaynak koddan çalıştırırken dosyalar varsayılan olarak `kaynaklar/` klasöründe tutulur (git'e girmez); uygulamada `Belgeler\libzie\kaynaklar`. Başka bir klasör kullanmak istersen uygulamada **Ayarlar**'dan seç, örneğin not aldığın uygulamanın Google Drive yedek klasörü. Bu, `ayarlar.json` dosyasına yazılır (örnek: `ayarlar.ornek.json`). `KAYNAK_KLASORU` ortam değişkeni de aynı işi yapar ve Ayarlar penceresini kilitler.

## Gizlilik

Dosyaların bilgisayarından çıkmaz. Sunucu yalnızca `127.0.0.1`'e bağlıdır. Hava durumu açıksa şehir adın Open-Meteo'ya gider; istemezsen şehir girme.

## Geliştirme

Windows uygulaması `app.py` (pywebview) ve `.github/workflows/windows.yml` ile derlenir. Mimari ve kurallar için [CLAUDE.md](CLAUDE.md), ürün bağlamı için [PRODUCT.md](PRODUCT.md), görsel sistem için [DESIGN.md](DESIGN.md) dosyalarına bak. Sunucu Python standart kütüphanesiyle, arayüz tek bir `static/index.html` dosyasıyla yazılmıştır.

## Lisans

[MIT](LICENSE). pdf.js (Apache-2.0) ve Linux Libertine/Biolinum (SIL OFL 1.1) kendi lisanslarıyla pakete dahildir (`static/vendor/` içinde lisans metinleri var).
