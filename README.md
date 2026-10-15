# libzie

Ders notlarını, slaytları ve PDF'leri derse göre düzenleyen, bilgisayarında yerel çalışan küçük bir arşiv. Dosyalar senin klasörlerinde durur; libzie onları ders karoları, küçük resimler ve sekmeli PDF görüntüleyiciyle gösterir. Hesap, bulut ya da veritabanı yok.

> Arayüz Türkçedir. Şimdilik Windows için yazıldı.

## Özellikler

- Klasörler = dersler: Gezgin'e eklediğin dosya kendiliğinden görünür, içe aktarma yok.
- Sürükle-bırakla yükleme (klasör dahil), taşıma, yeniden adlandırma, "Geri al" ile yumuşak silme.
- PDF'ler sayfa içinde sekmelerde açılır; PDF'lerin ilk sayfası küçük resim olur.
- Türkçe karakterden bağımsız arama (`isletim` → "İşletim"), `Ctrl+K` ile tüm derslerde hızlı arama.
- Tam klavye kullanımı (`?` kısayolları gösterir), `F` ile tam ekran, `Ctrl+B` ile kenar çubuğu.
- Tamamen çevrimdışı çalışır. İnternete çıkan tek şey isteğe bağlı hava durumu (Open-Meteo, şehri sen yazarsın).

## Kurulum

[Python 3](https://www.python.org/downloads/) kurulu olmalı. Başka bir şey gerekmez (bağımlılık ve derleme yok).

```
git clone https://github.com/nopescope0/libzie.git
cd libzie
python server.py
```

ya da klasördeki `baslat.bat` dosyasına çift tıkla. Tarayıcıda `http://127.0.0.1:8765` açılır. Sunucu yalnızca kendi bilgisayarına bağlanır, ağdan erişilemez.

Seçenekler:

- `python server.py --no-browser`: tarayıcıyı otomatik açma.
- `$env:PORT=9000` (PowerShell) ya da `set PORT=9000` (cmd), sonra `python server.py`: başka bir port kullan.

## Ders klasörün

Dosyalar varsayılan olarak `kaynaklar/` klasöründe tutulur (git'e girmez). Başka bir klasör kullanmak istersen uygulamada **Ayarlar**'dan seç, örneğin not aldığın uygulamanın Google Drive yedek klasörü. Bu, `ayarlar.json` dosyasına yazılır (örnek: `ayarlar.ornek.json`). `KAYNAK_KLASORU` ortam değişkeni de aynı işi yapar ve Ayarlar penceresini kilitler.

## Gizlilik

Dosyaların bilgisayarından çıkmaz. Sunucu yalnızca `127.0.0.1`'e bağlıdır. Hava durumu açıksa şehir adın Open-Meteo'ya gider; istemezsen şehir girme.

## Geliştirme

Mimari ve kurallar için [CLAUDE.md](CLAUDE.md), ürün bağlamı için [PRODUCT.md](PRODUCT.md), görsel sistem için [DESIGN.md](DESIGN.md) dosyalarına bak. Sunucu Python standart kütüphanesiyle, arayüz tek bir `static/index.html` dosyasıyla yazılmıştır.

## Lisans

[MIT](LICENSE). pdf.js (Apache-2.0) ve Linux Libertine/Biolinum (SIL OFL 1.1) kendi lisanslarıyla pakete dahildir.
