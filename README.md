# Shape Words: Learn English

Word Hunt oyununun mağaza sürümü (Capacitor 8 · iOS + Android).
Paket kimliği (bundle id / application id): **com.muratkassasgames.shapewords**

| Klasör | İçerik |
|---|---|
| `www/` | Oyunun kendisi (tek sayfa, yazı tipleri dahil, internetsiz çalışır) |
| `ios/`, `android/` | Yerel projeler (Codemagic bunları derler) |
| `assets/` | İkon ve açılış ekranı kaynakları |
| `store/ios/` | App Store ekran görüntüleri 1320×2868 (iPhone 6.9") |
| `store/android/` | Google Play ekran görüntüleri 1080×1920 |
| `store/listing.md` | 7 dilde mağaza metinleri |
| `docs/` | Gizlilik politikası + destek sayfası (GitHub Pages) |
| `codemagic.yaml` | Otomatik derleme ayarları |

---

## Yükleme adımları (Pati Pals ile aynı yol)

### 1) GitHub
1. github.com → **New repository** → ad: `shape-words` → **Public** (GitHub Pages ücretsiz hesapta public ister) → Create.
2. **En kolayı:** repoyu boş oluşturup Claude'a "repo hazır" de; Claude doğrudan yükler.
   Kendin yükleyeceksen: GitHub tarayıcıdan tek seferde en çok 100 dosya alır, bu yüzden 4 parti yap
   (repo → **Add file → Upload files** → sürükle → Commit):
   1. `android` klasörü · 2. `ios` klasörü · 3. `www` + `docs` + `store` · 4. kalan tüm dosyalar (`assets`, `tools`, `codemagic.yaml`, `package.json`, `package-lock.json`, `capacitor.config.json`, `.gitignore`, `README.md`).
3. Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch: `main`, klasör: `/docs` → Save.
   Birkaç dakika sonra şu adresler açılmalı:
   - https://muratkassasgames.github.io/shape-words/privacy.html
   - https://muratkassasgames.github.io/shape-words/

### 2) Apple tarafı
1. developer.apple.com → Certificates, IDs & Profiles → **Identifiers → +** → App IDs → App →
   Bundle ID (Explicit): `com.muratkassasgames.shapewords`, açıklama: Shape Words. Ek yetenek seçme.
2. App Store Connect → **Uygulamalar → + → Yeni Uygulama**
   - Platform: iOS · Ad: **Shape Words: Learn English** · Ana dil: English (U.S.)
   - Bundle ID: yukarıdaki · SKU: `shapewords001`
3. **Uygulama Gizliliği** → Gizlilik politikası URL'si: privacy.html adresi → Veri toplama: **"Veri toplamıyoruz"**.
4. **Fiyat ve Bulunabilirlik** → Ücretsiz.
5. **Yaş derecesi** anketi: her şeye "Yok/Hayır" → 4+.
6. Kategori: Eğitim, ikinci: Bulmaca (Word).
7. Metinler `store/listing.md` içinde. Diller: English (U.S.) + Türkçe, Portekizce (Brezilya), İspanyolca (İspanya/Meksika), Almanca, Fransızca, Çince (Basitleştirilmiş). Her dile aynı ekran görüntüleri yüklenebilir.
8. Ekran görüntüleri: `store/ios/1.png … 6.png` → **iPhone 6.9" ekran** bölümüne. Oyun yalnızca iPhone için (iPad yok), o yüzden iPad görseli istenmez.

### 3) Codemagic
1. codemagic.io → **Add application** → GitHub → `shape-words` reposu → *codemagic.yaml* kullan.
2. **iOS:** Team settings → Integrations → App Store Connect'te Pati Pals için eklediğin API anahtarının **adını** bul.
   `codemagic.yaml` içinde `APP_STORE_KEY_NAME` yazan yeri o adla değiştir (GitHub'da dosyayı kalem simgesiyle düzenleyebilirsin).
3. Code signing identities → **iOS provisioning profiles → Fetch profiles** → `com.muratkassasgames.shapewords` için App Store profilini getir (sertifika Pati Pals'tan zaten var; yoksa *Generate certificate*).
4. **Android:** Code signing identities → **Android keystores → Generate keystore** (veya yükle)
   → Reference name: `shape_words_keystore`. Keystore dosyasını ve şifrelerini **indir ve sakla** — kaybolursa uygulama güncellenemez.
5. **Start new build** → önce *Shape Words – iOS (TestFlight)*, sonra *Shape Words – Android (.aab)*.
   - iOS derlemesi bitince TestFlight'a kendiliğinden gider (~15-30 dk işlenir). Kendi iPhone'unda TestFlight'tan dene.
   - Android derlemesi bitince Artifacts'tan `app-release.aab` dosyasını indir.

### 4) Google Play
1. Play Console → **Uygulama oluştur** → ad: Shape Words: Learn English · Varsayılan dil: English (US) · Oyun · Ücretsiz.
2. **Uygulama içeriği**: Gizlilik politikası URL'si · Reklam yok · Veri güvenliği: **veri toplanmıyor / paylaşılmıyor** · Hedef kitle: 13+ (çocuklara özel değil, ama herkes oynayabilir — 13 altı seçilirse "Aileler" kuralları ve ek inceleme gelir) · İçerik derecelendirmesi anketi: şiddet/küfür vb. hepsi "Hayır".
3. **Ana mağaza girişi**: metinler `store/listing.md`, ekran görüntüleri `store/android/`, ikon 512×512 (`store/play-icon-512.png`), öne çıkan görsel 1024×500 (`store/play-feature-1024x500.png`).
4. **Kapalı test** → yeni sürüm → `app-release.aab` yükle → test kullanıcıları (e-posta listesi). Kişisel hesapta üretime çıkmak için **12 test kullanıcısı, 14 gün** şart (Pati Pals için topladığın liste burada da kullanılabilir; 1 kişi daha lazım).
5. 14 gün dolunca **Üretim erişimi için başvur**.

### Sonraki sürümler
Oyunda değişiklik olunca `www/` güncellenir, GitHub'a yüklenir, Codemagic'te yeniden derlenir.
Derleme numarası otomatik artar. Görünen sürüm `android/app/build.gradle` → `versionName` ve iOS'ta Xcode `MARKETING_VERSION` (şu an 1.0 / 1.0.0).

---

## Teknik notlar
- `npm ci && npx cap sync` → `www/` iki yerel projeye kopyalanır.
- `tools/build_www.py` → Word Hunt kaynağından `www/index.html` üretir (yazı tipleri yerel, ilerleme cihazda Capacitor Preferences ile saklanır).
- `tools/test_app.py` → çevrimdışı tarayıcı testi.
- Ses: Kokoro (Apache 2.0) · Okunuş: CMU Pronouncing Dictionary · Kelime filtresi: LDNOOBW (CC BY 4.0).
