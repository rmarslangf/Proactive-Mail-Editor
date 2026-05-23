# ProactiveMail

> Koyu temalı, modüler yapıda e-posta bülteni editörü. Blokları sürükle-bırak ile sırala, önizlemeyi canlı izle, tek tuşla gönder.

---

## Genel Bakış

ProactiveMail dört farklı biçimde gelir. Hepsi aynı çekirdeği paylaşır — HTML üretici, blok sistemi, dil desteği — ama farklı ihtiyaçlara hitap eder. Tek kişilik masaüstü kullanımından ekip için sunucu kurulumuna kadar her senaryoda doğru bir seçenek var.

```
Proje/
├── BaseApp/                          Saf editör, SMTP yok
├── wSMTP/                            Editör + SMTP + alıcı yönetimi
├── proactivemail_web/                Flask tabanlı web uygulaması
└── proactivemail_web_containerized/  Docker ile containerize web
```

---

## Sürümler

### BaseApp — Saf Editör

Editörün en sade hali. SMTP yok, veritabanı yok, dışarıya bağımlılık yok. Bülten hazırla, önizle, HTML olarak dışa aktar ya da panoya kopyala. İnternetsiz ortamlarda, CI pipeline'larında veya sadece "bir HTML üretmem lazım" dediğin her durumda çalışır.

**Ne zaman kullanmalı:** Gönderimi kendin yöneteceksen ya da sadece HTML çıktısı istiyorsan.

```bash
pip install PyQt5 PyQtWebEngine
python main.py
```

---

### wSMTP — Masaüstü + SMTP

BaseApp'in üzerine Gmail, Outlook, Exim ve özel SMTP desteği, SQLite tabanlı alıcı yönetimi ve detaylı gönderim geçmişi eklenmiş hali. Her şey local çalışır, sunucu gerekmez. Uygulama kapanırken SMTP ayarlarını veritabanına yazar, bir sonraki açılışta geri yükler.

**Ne zaman kullanmalı:** Tek bilgisayardan toplu mail göndermek istiyorsan.

```bash
pip install PyQt5 PyQtWebEngine
python main.py
```

---

### proactivemail_web — Web Uygulaması

Aynı editör, aynı özellikler — ama tarayıcıdan. Flask REST API üzerinde çalışır, frontend saf JavaScript ile yazılmıştır, derleme adımı yoktur. Aynı ağdaki birden fazla kişi aynı anda kullanabilir, alıcı listesi merkezi bir SQLite veritabanında tutulur. Gönderim sırasında ilerleme SSE (Server-Sent Events) ile canlı olarak tarayıcıya akar.

**Ne zaman kullanmalı:** Birden fazla kişi kullanacaksa veya farklı cihazlardan erişmek istiyorsan.

```bash
pip install flask flask-cors
python app.py
# → http://localhost:5000
```

---

### proactivemail_web_containerized — Docker

Web uygulamasının production-ready hali. `Dockerfile` ve `docker-compose.yml` eklenmiş, veritabanı `./data/` volume'una bağlanmış. Container yeniden başlatılsa, güncellenip yeniden oluşturulsa bile veriler kaybolmaz. Sunucuya kurmak için tek komut yeterli.

**Ne zaman kullanmalı:** Bir sunucuya kurup sürekli çalışır halde bırakmak istiyorsan.

```bash
docker-compose up -d --build
# → http://localhost:5000
```

> `docker-compose.yml` içindeki `PM_SECRET` değerini mutlaka değiştir.

---

## Özellikler

### Editör

ProactiveMail'in merkezinde blok tabanlı bir editör var. Her içerik parçası bağımsız bir blok, her bloğun kendi ayarları var.

**16 blok tipi:**

| Blok | Ne yapar |
|---|---|
| Başlık | Büyük bölüm başlığı |
| Paragraf | Ana metin, inline link desteği var |
| Alıntı | Sol çizgili vurgu kutusu |
| Madde Listesi | Noktalı liste, 2 sütun seçeneği |
| Numaralı Liste | Sıralı liste |
| Ayraç | Yatay çizgi |
| Buton | Tıklanabilir CTA butonu |
| Görsel URL | Harici URL'den görsel |
| Görsel Dosya | Yerel dosyadan görsel, base64 gömülü |
| Boşluk | Ayarlanabilir dikey boşluk |
| Bölüm | Renkli arka planlı içerik kutusu |
| İçindekiler | Izgara tabanlı link listesi |
| Highlight | Başarı / uyarı / bilgi kutusu |
| Tablo | CSV formatında veri tablosu |
| Kişi Kartları | Avatar + ad + unvan + e-posta kartları |
| Emoji Satırı | Yatay emoji dizisi |

**Her blok için bağımsız:**
- Font ailesi ve punto
- Yazı rengi
- Paragraf üst/alt boşluğu
- Bölüm üst/alt iç dolgusu

**Inline Hyperlink**
Paragraf metninin içindeki herhangi bir kelimeyi ya da cümleyi ayrı ayrı linkleme yapabilirsin. "Devamını oku", "buraya tıkla", "kayıt ol" — her biri farklı URL'e gidebilir, aynı paragrafta birden fazla link olabilir.

**Bölüm (Section) Mini Editörü**
Bölüm bloğu kendi içinde büyür. İçine sınırsız paragraf ve link satırı ekleyebilirsin, her birinin rengi ve puntosu bağımsızdır.

**Sürükle-Bırak Sıralama**
Blok kartlarını tutup sürükleyerek sırayı değiştirebilirsin. ▲▼ butonları da çalışmaya devam eder.

**Header & Footer**
PNG veya JPG yükle. Görsel base64 olarak HTML içine gömülür, e-posta istemcilerinde harici bağlantı gerekmez. Ayrıca arka plan rengi ve yazı rengi de ayarlanabilir.

**Canlı Önizleme**
Her değişiklikte önizleme otomatik güncellenir. Masaüstünde PyQt WebEngine ile, web sürümünde iframe ile render edilir.

**TR / EN Dil Desteği**
Tek tıkla arayüz dili değişir. Blok etiketleri, buton metinleri, placeholder'lar — her şey.

---

### SMTP

Dört sağlayıcı desteklenir. Sağlayıcıyı seçtiğinde host, port ve bağlantı tipi otomatik dolduruluyor.

| Sağlayıcı | Host | Port | Bağlantı |
|---|---|---|---|
| Gmail | smtp.gmail.com | 587 | STARTTLS |
| Outlook / Office 365 | smtp.office365.com | 587 | STARTTLS |
| Özel SMTP | Elle gir | Elle gir | Seçilebilir |
| Exim (Local Relay) | localhost | 25 | Düz |

**Ek ayarlar:**
- Bounce / Return-Path adresi — e-posta sunucusuna envelope-from olarak iletilir
- Reply-To adresi — alıcı yanıtlarını farklı bir adrese yönlendir
- Mail arası bekleme (ms) — spam filtrelerine takılmamak için
- Batch boyutu — N mailden sonra belirli süre bekle

Ayarlar kaydedil butonuna basınca SQLite'a yazılır, uygulama bir sonraki açılışında geri yüklenir.

---

### Alıcı Yönetimi

**Gruplar**
Alıcıları renk kodlu gruplara ayır. VIP, Standart, Test — istediğin kadar grup oluşturabilirsin. Gönderim sırasında belirli bir gruba ya da tüm aktif alıcılara gönderebilirsin.

**Alıcı CRUD**
Ad, e-posta, şirket, grup, notlar. Silme işlemi soft delete — alıcı silinmez, pasife alınır, istediğinde geri açılır.

**Abonelik Yönetimi**
Abonelikten çıkmak isteyen birini deaktive edebilirsin. Yeniden abone olduğunda tek tıkla aktife alırsın.

**CSV İçe Aktarma**
Sütun adlarını tahmin eder. `name`, `ad`, `isim`, `full_name` hepsini aynı kabul eder. `email`, `mail`, `e-posta` da aynı şekilde. Zaten kayıtlı e-postalar atlanır, sonunda özet gösterilir.

---

### Gönderim ve Takip

**Gönderim**
- Test modu: gönderimi başlatmadan önce sadece kendi adresine gönder, HTML'in doğru görünüp görünmediğini kontrol et
- Canlı ilerleme: kaç tane gönderildi, kaç tane başarısız, hangisi hata verdi — anlık görürsün
- Durdur butonu: gönderim sırasında istediğin an durdurabilirsin

**Log**
Her gönderim kayıt altına alınır. Kampanya adı, alıcı, durum, hata mesajı, tarih. Filtreleyebilirsin — sadece başarısızları göster, sadece belirli bir kampanyayı göster.

**Tekrar Gönder**
Başarısız olan gönderimler için tek tıkla tekrar gönderim başlatabilirsin. Başarılı olanlar yeniden gönderilmez.

**CSV Dışa Aktar**
Log tablosunu CSV olarak indirebilirsin.

---

## Gmail Kurulumu

Google doğrudan hesap şifreni SMTP için kullandırtmıyor. Uygulama şifresi oluşturman gerekiyor:

1. [myaccount.google.com/security](https://myaccount.google.com/security) adresine git
2. **İki adımlı doğrulamayı** aç — açık değilse uygulama şifresi oluşturulamıyor
3. Arama kutusuna **"Uygulama şifreleri"** yaz
4. Yeni bir şifre oluştur, oluşan **16 haneli kodu** ProactiveMail'deki şifre alanına yaz

Sağlayıcı: Gmail → host ve port otomatik gelir, başka bir şey yapman gerekmiyor.

---

## Exim Kurulumu

Sağlayıcı olarak **Exim (Local Relay)** seç. Host `localhost`, port `25` otomatik gelir, kullanıcı adı ve şifre istenmez — local relay kimlik doğrulama gerektirmez.

Tek ön koşul: Exim'in `localhost:25` üzerinden relay'e izin vermesi. Bu Python tarafında değil, sunucu konfigürasyonunda yapılır:

```bash
# Debian/Ubuntu
sudo dpkg-reconfigure exim4-config
# → "internet site" veya "mail sent by smarthost" seç
# → dc_relay_nets'e 127.0.0.1 ekle
```

---

## Ortam Değişkenleri

Web ve Docker sürümlerinde geçerli:

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `PM_HOST` | `0.0.0.0` | Dinlenecek adres |
| `PM_PORT` | `5000` | Port numarası |
| `PM_DEBUG` | `1` | Production'da `0` yap |
| `PM_SECRET` | *(değiştir)* | Flask session şifreleme anahtarı |
| `PM_DB_PATH` | `proactivemail.db` | SQLite dosyasının tam yolu |

---

## Proje Yapısı

Her sürüm aynı çekirdeği paylaşır:

```
proactivemail/
├── config.py           Platform tespiti, yollar, sabitler
├── lang.py             TR / EN dil paketleri
├── style.py            PyQt5 koyu tema CSS
├── utils.py            img_to_b64, make_color_btn
├── html_builder.py     Tüm blok tiplerini HTML'e çevirir
├── block_widget.py     Tek bir içerik bloğunun PyQt widget'ı
├── main_window.py      Ana uygulama penceresi
├── db.py               SQLite — alıcılar, gruplar, log, ayarlar, kampanyalar
├── smtp_sender.py      SmtpConfig, SmtpSender, SendWorker (QThread)
└── tabs/
    ├── recipients_tab.py
    ├── send_tab.py
    └── logs_tab.py
```

Web sürümünde ek olarak:

```
api/
├── campaigns.py    Kampanya kaydet / yükle / önizle
├── recipients.py   Alıcı & grup CRUD
├── send.py         Toplu gönderim + SSE stream
├── settings.py     SMTP kaydet / yükle / test
└── logs.py         Geçmiş, özet, tekrar gönder

static/
├── index.html
├── css/app.css
└── js/
    ├── app.js          Altyapı, dil sistemi, önizleme, kampanya kayıt
    ├── editor.js       Blok editörü, drag & drop
    ├── recipients.js   Alıcı & grup yönetimi
    ├── send.js         Gönderim + SSE ilerleme
    ├── logs.js         Geçmiş tablosu
    └── settings.js     SMTP form
```

---

## Gereksinimler

**Masaüstü (BaseApp / wSMTP)**
```
Python    >= 3.10
PyQt5     >= 5.15
PyQtWebEngine >= 5.15
```

**Web**
```
Python    >= 3.10
Flask     >= 3.0
flask-cors >= 4.0
```

**Docker**
```
Docker + Docker Compose
```
Başka kurulum gerekmez.

---

## Lisans

MIT
