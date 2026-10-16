# Güvenlik

## Bir açık buldun mu?

Lütfen herkese açık bir issue açma. Bunun yerine bu deponun **Security → Report a vulnerability** (özel güvenlik bildirimi) bölümünü kullan. Mümkünse şunları yaz: etkilenen sürüm, adım adım nasıl yeniden üretileceği ve etkisi. Bildirimlere birkaç gün içinde yanıt vermeye çalışırım.

## libzie güvenlik modeli

libzie tek kullanıcılı, yalnızca kendi bilgisayarında çalışan bir uygulamadır. Sunucu sadece `127.0.0.1` adresini dinler; ağdan erişilemez. Yine de tarayıcıda açık başka bir web sitesinin ya da aynı bilgisayardaki başka bir programın bu yerel sunucuyu kullanamaması için şu önlemler vardır:

- **Oturum anahtarı:** Rastgele bir anahtar yalnızca senin Windows hesabının okuyabildiği `%APPDATA%\libzie\oturum.key` dosyasında durur. Uygulama adresi anahtarla açar, sunucu bunu `HttpOnly` + `SameSite=Strict` çerezde saklar. Anahtarsız hiçbir API isteği işlenmez.
- **Başka sitelerden gelen istekler reddedilir (CSRF / DNS rebinding):** `Host`, `Origin` ve `Sec-Fetch-Site` başlıkları denetlenir, durum değiştiren her istek özel bir başlık (`X-Libzie`) ister.
- **Dosya açma izin listesiyle sınırlıdır:** "Varsayılan uygulamada aç" yalnızca belge, görsel, ses/video ve arşiv türleri için çalışır; `.exe`, `.bat`, `.lnk`, `.ps1`, `.py` vb. hiçbir zaman doğrudan açılmaz.
- **Kullanıcı dosyaları kum havuzunda sunulur:** PDF dışındaki dosyalar `Content-Security-Policy: sandbox` ile gelir; klasörüne düşen zararlı bir SVG/HTML dosyası betik çalıştıramaz ve uygulamanın API'sine erişemez.
- **Sıkı içerik politikası:** Uygulama sayfasında `eval` yoktur, yalnızca kendi dosyaları ve hava durumu servisi yüklenir. pdf.js `isEvalSupported: false` ile çalışır (CVE-2024-4367 gibi saldırılara karşı).
- **Yol güvenliği:** Tüm yollar `kaynaklar` klasörüne kısıtlanır; Windows'un ayrılmış adları (`CON`, `NUL`…) ve geçersiz adlar reddedilir.

## Güncelleme güvenliği

Uygulama içi güncelleme yalnızca bu deponun GitHub sürümlerinden, HTTPS üzerinden indirir; indirilen dosyanın boyutunu ve (GitHub verdiyse) SHA-256 özetini doğrular. Uygulama **kod imzalı değildir**, bu yüzden Windows SmartScreen uyarı verebilir. Her sürümle birlikte `SHA256SUMS.txt` yayınlanır; indirdiğin dosyayı elle doğrulamak için:

```
certutil -hashfile libzie-kurulum.exe SHA256
```

Çıkan değer `SHA256SUMS.txt` içindeki satırla aynı olmalıdır. Güvenilir kaynak yalnızca bu deponun **Releases** sayfasıdır.

## Bilinen sınırlar

- Aynı Windows hesabında çalışan kötü amaçlı bir program zaten senin dosyalarına erişebilir; libzie buna karşı koruma sağlamaz.
- Kod imzası yoktur (bkz. yukarısı).
- pdf.js 3.11.174 sürümü kullanılır (başka bir güncel sürüm ES modülü gerektirir). Bilinen eval tabanlı açığa karşı kapatma önlemleri alınmıştır; PDF işleme kodu yine de tarayıcı/WebView2 kum havuzunda çalışır.
