# libzie UI rehberi

Yeni bir pencere, menü, ayar, kart ya da animasyon eklemeden **önce** bu dosyayı oku. [DESIGN.md](DESIGN.md) sistemin tam tarifidir (renkler, tipografi, bileşenler); bu dosya onun **uygulama rehberi**dir: karakteri özetler, hazır tarifleri verir ve geçmişte yapılan hatalardan çıkan kuralları listeler. Çelişki olursa DESIGN.md geçerlidir. Yeni bir kural öğrenirsen bu dosyayı güncelle.

## 1. Karakter (tek paragraf)

libzie sakin, koyu ya da açık bir "çalışma rafı"dır: her şey bulunduğu yerde durur, düz ve ele yakın. **Düz renk blokları, neredeyse kare köşeler, ince çizgiler, büyük ve normal ağırlıkta serif başlıklar.** Hareket bir şeyi *açıklar* (nereden geldi, nereye gitti), süslemez. Renk tek yerde yoğunlaşır: ders kimliği. Arayüz nötr + tek turuncu vurgudur.

Yeni bir şey tasarlarken kendine sor: *Bunu mevcut bir bileşenin içinden çıkarabilir miyim?* Çoğu zaman cevap evet: yeni bir stil icat etme, olanı kullan.

## 2. Kesin kurallar

**Yap**
- Köşe yarıçapı **2px** (`var(--r)`); yalnızca ana sayfa gösterge kutuları 4px, küçük resim rozeti 3px.
- Bloklar arası boşluk **5px** (`var(--gap)`); aralıklar 4 / 8 / 12 / 16 ölçeğinden, bölümler arası 38.
- Yüzeyleri **bir ton basamağıyla** (zemin → kenar çubuğu → yüzey → hover) ya da **1px çizgiyle** ayır.
- Renk için yalnızca CSS değişkenleri: `var(--bg)`, `--text`, `--muted`, `--accent`… Saydam ton gerekirse `color-mix(in srgb, var(--accent) N%, transparent)`. Sabit renk yazma (temalar bozulur).
- Başlıklar serif (`var(--font-head)`), geri kalan her şey sans. Hiyerarşi **boyuttan** gelir.
- Her tıklanabilir blok klavye odaklanabilir olsun (`tabindex`, rol, görünür odak halkası); işlev yalnızca hover'da gizli kalmasın.
- Her kullanıcıya görünen metin `t('kimlik')` ya da `data-i*` ile (bkz. CLAUDE.md "Diller"); her yeni renk değişkeni tema dosyalarına.
- `prefers-reduced-motion` altında hareket kapanır; doğrudan açılan bir yedek yol her zaman olsun.

**Yapma**
- İkinci bir vurgu rengi, gradyan, kalın/büyük harf vurgusu, "eyebrow" etiketi, emoji ya da unicode ikon.
- Kart/karo/satır/sekme üzerinde **gölge** (gölge yalnızca menü, pencere, toast gibi sayfadan ayrılan katmanlar için).
- Üzerine gelince **dolgu rengi değiştirerek** kart vurgulama; bunun yerine ortaya çıkar/yakınlaş (önizleme %3-7 büyür) ya da çizgi değiştir. (İstisna: `.node` satırları ve düğmeler `--hover` dolgusu alır, sistem böyle.)
- Pill/yuvarlak form, 4px'ten büyük köşe.
- Ekranda duran sonsuz döngü (yalnızca hover/odakta çalışan dekoratif döngüler olur).

## 3. Bileşen tarifleri (hepsi mevcut sınıflar)

| İhtiyaç | Kullan | Notlar |
|---|---|---|
| Bölüm başlığı | `.sec-head` = ikon (`svg.sec-ic`, 22px, çizgi 1.3 köşeli) + `h2` (28px serif) + `.sec-rule` | çizginin ucundaki lehim halkası otomatik; panelde ilk başlık `margin-top: 0` |
| Yan gezinme/sekme listesi | `.node` (+ seçili: `background: var(--hover); color: var(--text)`) | 16px ikon, `padding: 7px 8px; gap: 8px`; yeni "aktif çubuk" icat etme |
| Düğme | `.btn`, birincil `.btn.primary`, tehlike `.btn.danger`, ikon `.icon-btn` (26px) | metin düğmesi 6px 12px |
| Form alanı | `.field` (12px soluk etiket) + `input`/`select` + `.hint` (12.5px soluk açıklama) | alanlar sayfanın yazı tipini devralır (`font: inherit`) |
| Onay kutusu | `label.chk`/`.gen-chk` içinde `input[type=checkbox]` + `span` | `accent-color: var(--accent)` |
| Pencere | `<dialog>`; çerçeve `1px var(--line-strong)`, yüzey `var(--surface)`, gölge `var(--shadow)`, 2px köşe | açılış `pop` (0,96, 250ms) zaten `dialog[open]`'da; bunu **kapatma**, yeniden başlatma |
| Seçim blokları (ör. tema) | düz blok `var(--bg)` + önizleme; seçili = önizleme çerçevesi vurgu rengi + onay işareti | `role="radio"`/`radiogroup`, ←/→ ile gezilir |
| Bildirim | `toast(...)` (+ "Geri al" eylemi) | ilerleme çizgisi 2px vurgu |
| Bağlam menüsü | `menu(anchor, items, pos)` | imleçten 250ms, ölçek 0,97 |

İkonlar: 24 viewBox çizgi ikon; arayüzde 16px/1.6 yuvarlak uç, başlık ve süslerde 1.3 köşeli (`stroke-linejoin: miter; stroke-linecap: square`).

## 4. Hareket

Süreler yalnızca `:root` token'larından: `--duration-quick` 150 (kapanış, metin değişimi), `--duration-fast` 250 (pencere/menü açılışı, ikon değişimi, sekme), `--duration-medium` 350, `--duration-slow` 400 (panel açılışı), `--duration-very-slow` 500 (vurgu anı). Eğri: açılış/kapanış/kayma için `--ease-smooth-out`; mesafe `--distance-*`, ölçek `--scale-*` (pencere 0,96), bulanıklık `--blur-*`.

**Kurallar** (`transitions-polish` becerisiyle aynı)
1. **Açılış kapanıştan yavaş:** pencere açılış 250, kapanış 150; panel 400 / 350.
2. **Hover giriş ≤250ms, çıkışta gecikme yok;** bir şeyi geciktirmek için değil, yalnızca sıralama (stagger 40ms, toplam ≤300ms) ya da kazara tetiklemeyi süzmek için gecikme kullan.
3. **Hareket bir şeyi açıklar:** yeni bir hareket icat etmeden önce mevcut sözlüğe bak: ders karosunun şekli konum yolundaki ikona uçar; Ayarlar simgesi hover'da bir diş (60°) döner; kapanan sekme daralır. Yeni hareket bunlardan birinin devamı olsun.
4. **Paylaşılan öğe geçişi** (View Transitions) en temiz yoldur: tetikleyici öğedeki ikon, açılan yüzeydeki **aynı ikona** uçar. Tarif: `transition(update, nameOld, nameNew, after)` + `vtName(el, 'ad')`; geçiş sırasında `:root`'a bir sınıf ekle (`vt-set-open`) ve sürelerini onunla ayarla. Örnek: Ayarlar dişlisi (kenar çubuğu simgesi → pencere başlığındaki simge, açılış 400ms/kapanış 250ms, 180° dönüş; kök karşılıklı solması açılışta kapalı, kapanışta 150ms).
5. **Yüzeyin kendi açılışını geçiş yeniden yazmasın.** Pencere zaten `pop` ile açılır; geçiş yalnızca paylaşılan öğeyi taşısın.

**Hatalardan çıkan kurallar** (ayarlar penceresi geçişinde yaşandı)
- ❌ **Daire maskesi** (`clip-path: circle`) bir simgenin arkasında "çember" gibi görünür; maske kullanma.
- ❌ **İnce çizgili ikona bulanıklık / büyük ölçekleme:** 16px'lik ikonu 150px'e büyütmek ya da `blur` eklemek çizgiyi parlak bir hâleye çevirir. İkonu kendi boyutunda uçur, bulanıklık ekleme (bulanıklık yalnızca geniş yüzey geçişlerinde, `--blur-small`).
- ❌ **Yüzeyin yerleşik animasyonunu geçiş bitince sınıf kaldırarak geri açma:** `dialog[open]`'ın `pop`'u yeniden başlayıp pencereyi ikinci kez açtı. Yerleşik animasyonu hiç kapatma; geçici sınıfla kapatıp açma.
- ❌ **İki katman aynı anda solarsa** (kök karşılıklı solma + pencere solması) sayfa içeriği pencerenin arkasından "yıkanır". Birini kapat.
- Dönüş gibi hızlı hareketlerde sahne kare hızına göre kararır (dişlinin dişleri titreşir); dönüşü diş aralığının (60°) katlarıyla sınırla ve çok hızlandırma.
- Sekme/gezinme ikonları: parçalar ayrı öğe (`.k`, `.d`, `.doc`, `.dot`), tek seferlik keyframe; hover, `:focus-visible` ve sekme seçilince (`.play`) oynar, `translate`/`scale` bireysel özellikleriyle (`transform-box: fill-box`), bulanıklık yok; sıçrama eğrisi (`--ease-bounce`) yalnızca belirmelerde.
- ❌ **Paylaşılan öğenin hedefi ölçeklenen yüzeyin içindeyse:** geçiş hedef konumu başlangıçta (pencere %96 ölçekliyken) yakalar, animasyon bitince gerçek öğe sola/yukarı sıçrar. Ayarlar penceresi bu yüzden `pop` yerine yalnızca `fade` ile açılır.
- Animasyonu **veri beklemeden** başlat (örn. `fetch` bitmeden pencereyi aç, alanları sonra doldur); gecikme "yavaş" hissettirir.

## 5. Sekmeli/ayar pencereleri için iskelet

```
<dialog id="x" aria-labelledby="x-title">
  <form method="dialog" class="set">
    <nav class="set-nav" role="tablist" aria-orientation="vertical">
      <p class="set-title" id="x-title"><svg/> <span data-i="…">Başlık</span></p>
      <button class="node set-tab" role="tab" aria-controls="pane-…">… <svg/> <span data-i>Ad</span></button>
    </nav>
    <div class="set-main">
      <button class="icon-btn set-x" …>×</button>
      <section class="set-pane" role="tabpanel" aria-labelledby="tab-…">
        <div class="sec-head"><svg class="sec-ic"/><h2>Ad</h2><span class="sec-rule"></span></div>
        …alanlar (.field / .hint / .btn)…
```
Davranış: roving tabindex, ↑/↓ (←/→ dar pencerede), Home/End; Esc, × ve **pencere dışına tıklama** (basış da dışarıda başlamalı) animasyonlu kapatır; seçili sekme oturumda hatırlanır; internete çıkan işlemler yalnızca ilgili sekme açılınca yapılır. Dar pencerede (<700px) sekmeler üstte yatay şeride döner.

## 6. Yeni UI için kontrol listesi

- [ ] Mevcut sınıflarla kuruldu (bölüm 3); yeni stil gerekiyorsa DESIGN.md'deki kurallara uyuyor (2px, 5px, düz blok, gölgesiz).
- [ ] Renkler değişkenden; **koyu ve açık temada** gözle bakıldı (`python tools/tema_kontrol.py` kontrast).
- [ ] Metinler `t()`/`data-i*`; `tr.json` + `en.json` eklendi; `python tools/i18n_kontrol.py` temiz.
- [ ] Klavye: odak sırası, Enter/Space, Esc, odak halkası; roller ve `aria-*`.
- [ ] Hareket token'larla; açılış > kapanış; reduced-motion yedeği; **bulanıklık/maske/gölge yok**.
- [ ] Gerçek Chrome'da (CDP) kare kare izlendi: çift tetiklenme yok, sınıf/ad sızıntısı yok, Esc/dış tıklama/çift tıklama güvenli.
- [ ] Sunucudan gelen her hata `AppError("kimlik")` ile; arayüz `errText()` ile gösteriyor.
- [ ] Bu rehbere yeni öğrenilen kural eklendi.
