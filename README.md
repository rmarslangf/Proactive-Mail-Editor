ProactiveMail
ProactiveMail, e-posta bülteni hazırlamayı olması gerektiği kadar sade tutan bir editör. Blokları sürükle-bırak ile sırala, her birinin fontunu, rengini, mesafesini ayarla, önizlemeyi canlı izle — hazır olduğunda tek tuşla gönder.

Dört farklı biçimde çalışır: saf masaüstü editör, SMTP entegrasyonlu masaüstü uygulama, web uygulaması ve Docker ile containerize edilmiş web uygulaması. Hangisi sana uyuyorsa onu çalıştır, geri kalanı şimdilik rafta dursun.

Hangi sürümü kullanmalıyım?
Tek başınasın, internet yokken de çalışsın istiyorsun → BaseApp veya wSMTP

Aynı ağdaki birkaç kişiyle paylaşacaksın → proactivemail_web

Sunucuya kurup herkesin tarayıcıdan erişmesini istiyorsun → proactivemail_web_containerized

Klasör	Ne yapar
BaseApp/	Editör, önizleme, HTML dışa aktarma. Başka bir şey yok, başka bir şey gerekmiyor.
wSMTP/	BaseApp'e SMTP, alıcı yönetimi ve gönderim geçmişi eklendi.
proactivemail_web/	Aynı şeyler, tarayıcıdan. Flask tabanlı, kurulum gerektirmez.
proactivemail_web_containerized/	Yukarıdakinin Docker versiyonu. Tek komutla ayağa kalkar.
Kurulum
Masaüstü
bash
pip install PyQt5 PyQtWebEngine
python main.py
Web
bash
pip install flask flask-cors
python app.py
Tarayıcında http://localhost:5000 adresini aç.

Docker
bash
docker-compose up -d --build
İlk açılışta proactivemail.db otomatik oluşur, veriler ./data/ klasöründe tutulur — container silsen bile bir şey kaybolmaz.

docker-compose.yml içindeki PM_SECRET değerini değiştirmeyi unutma.

Ne yapabilirsin
Editör
Sürükle bırak ile sıralanabilen 16 blok tipi var: başlık, paragraf, alıntı, madde listesi, numaralı liste, ayraç, buton, görsel, boşluk, bölüm, içindekiler tablosu, highlight kutusu, tablo, kişi kartları ve emoji satırı.

Her bloğun kendi font, punto ve renk ayarı var. Paragrafların üst ve alt boşluğunu piksel piksel ayarlayabilirsin. Bölüm kutularının iç dolgusu da aynı şekilde bağımsız.

Bir paragraf metninin içindeki belirli kelimeleri — "Devamını oku", "buraya tıkla", herhangi bir şey — ayrı ayrı hyperlink yapabilirsin. Birden fazla farklı link aynı paragrafta olabilir.

Bölüm (Section) bloğu kendi içinde büyür: istediğin kadar paragraf ve link satırı ekleyebilirsin, her birinin rengi ve puntosu bağımsız.

Header ve footer için PNG yükleyebilirsin. Görsel base64 olarak HTML'e gömülür, harici bağlantıya gerek kalmaz. Canlı önizleme her değişiklikte kendi kendine güncellenir.

SMTP ve Gönderim
Gmail, Outlook, Exim ve özel SMTP sunucu destekleniyor. Sağlayıcıyı seçtiğinde host, port ve bağlantı tipi otomatik dolduruluyor — elle bir şey girmek zorunda değilsin. Bağlantıyı test etmek için ayrı bir buton var.

Gönderim sırasında ilerlemeyi canlı izleyebilirsin. Bir şeyler ters giderse durdurabilirsin. İşlem bittiğinde kaç tane gönderildi, kaç tane başarısız oldu görürsün. Başarısız olanları tek tıkla tekrar gönderebilirsin.

Alıcı Yönetimi
Alıcıları gruplara ayırabilirsin. Grupların renk kodu olur, listedeyken ayırt etmek kolaylaşır. CSV içe aktarma var — sütun adlarını tahmin etmeye çalışır, name, ad, isim hepsi aynı şey olarak kabul edilir. Abonelikten çıkan birini kaydından silmek yerine pasife alabilirsin, istediğinde geri açarsın.

Gmail nasıl bağlanır
Google, doğrudan şifreni SMTP için kullandırtmıyor. Bunun yerine uygulama şifresi oluşturman gerekiyor:

myaccount.google.com/security adresine git
İki adımlı doğrulamayı aç (açık değilse)
Arama kutusuna "Uygulama şifreleri" yaz ve oluştur
Oluşan 16 haneli kodu ProactiveMail'deki şifre alanına gir
Sağlayıcı olarak Gmail'i seç, gerisini uygulama halleder.

Exim nasıl bağlanır
Sağlayıcı olarak Exim (Local Relay) seç. Host localhost, port 25 otomatik gelir, kullanıcı adı ve şifre istenmez. Tek koşul: Exim'in localhost:25 üzerinden relay'e izin vermesi — bu sunucu tarafında bir ayar, Python tarafında yapılacak bir şey yok.

Ortam değişkenleri
Web ve Docker sürümlerinde bunları kullanabilirsin:

Değişken	Varsayılan	Ne işe yarar
PM_HOST	0.0.0.0	Hangi adresi dinleyeceği
PM_PORT	5000	Port numarası
PM_DEBUG	1	Production'da 0 yap
PM_SECRET	(değiştir)	Flask oturum anahtarı
PM_DB_PATH	proactivemail.db	Veritabanının tam yolu
Gereksinimler
Masaüstü: Python 3.10+, PyQt5 ≥ 5.15, PyQtWebEngine ≥ 5.15

Web: Python 3.10+, Flask ≥ 3.0, flask-cors ≥ 4.0

Docker: Docker ve Docker Compose yeterli, başka kurulum gerekmez

