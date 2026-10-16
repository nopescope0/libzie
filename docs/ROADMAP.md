# libzie yol haritası

Son güncelleme: 2026-10-15. Önceliklendirme kesin değildir; kullanıcı geri bildirimine göre değişir.
Boyut tahmini: **S** (birkaç saat), **M** (bir iki gün), **L** (bir haftadan uzun).

## İlkeler (yol haritası bunlara uymayanı eklemez)

1. **Dosyaya ulaşmak her şeyden önemli:** ders → doğru sayfaya giden yolu kısaltmayan özellik eklenmez.
2. **Tek arşiv, çift defter yok:** kullanıcıyı klasörlerin dışında veri tutmaya zorlayan özellik yok. Klasör yapısı gerçek kaynaktır.
3. **Yerel ve özel:** çevrimdışı çalışır; internete çıkan her şey isteğe bağlı ve açıkça belli olur. Hesap, bulut, izleme yok.
4. **Uzun oturumlara uygun:** sakin arayüz; hareket durumu açıklar, süslemez.
5. **Kolay ayakta tutulur:** kaynak koddan çalışırken bağımlılık ve derleme adımı yok (paketleme yalnızca Windows uygulaması için).

## 1. Yayına hazırlık (şimdi)

- [ ] GitHub Actions'ta kurulum sihirbazı derlemesini doğrula; `libzie-kurulum.exe` ve taşınabilir sürümü temiz bir hesapta dene **(S)**
- [ ] `v0.2.0` sürümü: Release açıklaması (Türkçe), kurulum yönergesi **(S)**
- [ ] GitHub hesabında e-posta gizleme ve komut satırı push korumasını aç **(S)**
- [ ] Repoyu public yap; ilk geri bildirim için birkaç kişiye ver **(S)**
- [ ] README'ye kısa ekran kaydı (GIF): ders ekleme, sekmeli PDF, ikon seçme **(S)**
- [ ] Actions sürüm uyarıları (Node 20 → güncel eylem sürümleri) **(S)**
- [ ] `SmartScreen` uyarısı notu zaten README'de; ilerleyen sürümde kod imzalama seçeneklerini araştır (ücretsiz/ucuz yollar) **(M)**

## 2. Yakın vadeli (v0.2 – v0.4): günlük kullanımı rahatlatanlar

Kaynak: ilk eleştiri turu (`.impeccable/critique/`) ve kendi kullanım notları.

- [ ] **Çok dosyalı derslerde düzen:** 30–40 dosyalı derslerde türe göre gruplama (slayt, not, sınav), sıralama ve süzgeç; sınav haftasında "hepsini bir bakışta gör" **(M)**
- [ ] **Silinenler görünümü:** `.silinenler` şu an yalnızca "Geri al" bildirimi ve Gezgin ile ulaşılabiliyor; uygulama içinde listeleme, geri yükleme, kalıcı silme **(M)**
- [ ] **Sekmeler arası klavye:** `Ctrl+Tab`, `Ctrl+W`, `Ctrl+1..9` **(S)**
- [ ] **Klavye odağı:** ders açılınca odak içeriğe taşınsın, sayfanın başına dönmesin **(S)**
- [ ] **İlk açılış karşılaması:** boş arşivde 3 adımlık yönlendirme (ders ekle, dosya sürükle, ikon/renk seç) ve örnek ders **(S)**
- [ ] **Dersi özelleştir:** renk ve ikon seçimini tek pencerede birleştir **(S)**
- [ ] **Güncelleme bildirimi (isteğe bağlı):** GitHub Releases'e bakıp "yeni sürüm var" de; varsayılan kapalı, Ayarlar'dan açılır **(M)**
- [ ] **Yedek dışa aktarma:** dersi `.zip` olarak dışa aktar **(S)**
- [ ] **Ayarlar penceresi:** klasör seçme penceresi (yolu elle yazmak yerine) **(S)**

## 3. Orta vadeli (v0.5 – v1.0): kullanıcı tabanını genişletenler

- [ ] **İngilizce arayüz:** metinleri sözlüğe taşı (`tr`/`en`), dil Ayarlar'dan seçilir; yabancı kullanıcılar ve açık kaynak katkıcılar için **(M)**
- [ ] **Açık tema:** `:root` değişkenleri zaten ayrı; koyu/açık/sistem seçimi, kontrastlar yeniden doğrulanır **(M)**
- [ ] **macOS ve Linux:** sunucu zaten platform bağımsız (`open`/`reveal`); pywebview paketleri ve GitHub Actions'ta üç platformlu derleme **(L)**
- [ ] **PDF içinde metin arama:** dosya adı yerine içerikte ara (indeks yerelde, `.silinenler` gibi gizli klasörde); büyük arşivlerde yavaşlamamalı **(L)**
- [ ] **PDF'te kaldığın sayfayı hatırla:** şu an tarayıcının gömülü görüntüleyicisi sayfa bilgisi vermiyor; pdf.js ile kendi görüntüleyicimiz gerekir, kısayol tuşları da (Esc, F, Ctrl+K) PDF odaktayken çalışmaz sorununu çözer **(L)**
- [ ] **Etiketler / dönem düzeni:** "2026 Güz" gibi gruplama; klasör yapısını bozmadan yalnızca görünüm katmanı **(M)**
- [ ] **Sınav modu:** bir dersin tüm vize/final/ödev dosyalarını tek sayfada topla **(M)**

## 4. Teknik borç ve kalite

- [ ] **Otomatik testler:** `server.py` API'si için (yükleme, taşıma, silme, geri yükleme, ikon, güvenlik: yol dışına çıkma) standart kütüphane `unittest` ile; CI'da her push'ta çalışsın **(M)**
- [ ] **Satır sonu ve kodlama tutarlılığı:** `.gitattributes` var; CI'da CRLF/LF denetimi **(S)**
- [ ] **`index.html` büyüklüğü (~2500+ satır):** derleme adımı eklemeden ES modülleriyle bölmeyi değerlendir (`static/js/*.js`); önce ölçü: bölmek gerçekten bakım kolaylığı sağlıyor mu **(L)**
- [ ] **Hata günlüğü:** uygulamada sorun olunca "günlüğü kopyala" düğmesi (GitHub issue açmayı kolaylaştırır) **(S)**
- [ ] **Python sürümü uyumu:** 3.10–3.14 arası CI matrisi **(S)**
- [ ] **Erişilebilirlik gözden geçirmesi:** ekran okuyucuyla gerçek deneme, yüksek kontrast, `prefers-reduced-motion` testleri **(M)**
- [ ] **Performans:** 5000+ dosyalı arşivde `/api/tree` ve küçük resimler; artımlı yükleme ve daha akıllı küçük resim önbelleği **(M)**

## 5. Fikirler (karar verilmedi)

- Dosya başına kısa not / yer imi (klasör dışında veri tutmama ilkesi nedeniyle yanında `.libzie` yan dosyası gerekir; tartışılmalı)
- Ders başına haftalık program / sınav tarihi geri sayımı
- Tarayıcı eklentisi ya da "buraya kaydet" kısayolu (indirilen PDF'i doğru derse atmak)
- Notability / GoodNotes yedek klasörleri için hazır ayar şablonları
- Hava durumu yerine isteğe bağlı başka bir küçük araç (Pomodoro sayacı)
- Mobil/tablet düzeni (şu an hedef değil; ilke: tek masaüstü bilgisayar)

## Yapılanlar (özet)

- **0.0.1:** ilk Windows sürümü (yerel sunucu, ders karoları, sekmeli PDF, küçük resimler, arama, Geri al, klavye erişimi)
- **0.1.0:** masaüstü uygulaması (pywebview + PyInstaller), Belgeler/APPDATA veri yeri, tek örnek, GitHub Actions derlemesi, MIT lisansı
- **0.1.1:** genel ders ikonları ve ikon seçici
- **0.2.0 (hazırlanıyor):** kurulum sihirbazı ve taşınabilir sürüm
