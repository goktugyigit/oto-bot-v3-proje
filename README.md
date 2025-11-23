# Gamermarkt Scraper System

Bu proje, Cloudscraper kullanarak Gamermarkt sitesinden ilanları çeker ve modern bir web arayüzünde listeler.

## Kurulum

1.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```

## Çalıştırma

1.  Uygulamayı başlatın:
    ```bash
    python app.py
    ```
2.  Tarayıcınızda şu adrese gidin:
    `http://localhost:5000`

## Özellikler

*   **Otomatik Veri Çekme**: Arka planda sürekli çalışarak ilanları günceller.
*   **Cloudflare Bypass**: `cloudscraper` kütüphanesi ile korumaları aşmaya çalışır.
*   **Anlık Arayüz**: Sayfa yenilemeye gerek kalmadan ilanları günceller.
*   **Filtreleme**: Kategori ve metin bazlı filtreleme.
*   **Yeni İlan Bildirimi**: Sistem açıldıktan sonra eklenen yeni ilanlar "YENİ!" etiketiyle işaretlenir.
*   **Durdur/Başlat**: Arayüz üzerinden sistemi durdurup başlatabilirsiniz.

## Notlar

*   Sistem ilk açıldığında `listings.json` dosyasını oluşturur/okur.
*   Her 30 saniyede bir tüm kategorileri tarar.
*   Her istek arasında rastgele bekleme süreleri vardır (banlanmamak için).
