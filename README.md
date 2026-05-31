📄 Sözleşme Rehberim - AI Risk Analizi
Bu proje, dijital platformların karmaşık hukuki sözleşmelerini Üretken Yapay Zeka (Gemini 1.5 Flash) kullanarak saniyeler içinde analiz eden, son kullanıcı odaklı bir MVP web uygulamasıdır. İstanbul Gedik Üniversitesi CS Honors '26 etkinliği kapsamında geliştirilmiştir.

🔗 Canlı Uygulama: [Sözleşme Rehberim'i Deneyin](https://sozlesme-rehberim.streamlit.app/)

🎬 Proje Tanıtım Videosu: [YouTube Üzerinden İzleyin](https://www.youtube.com/watch?v=tkpqRrxR8sw)

🚀 Kurulum ve Çalıştırma (Yerelde Denemek İsteyenler İçin)
Gerekli kütüphaneleri yükleyin:

```bash
pip install streamlit google-generativeai
```

Kodu çalıştırmak için terminale yazın:
```bash
streamlit run Ana_Sayfa.py
```

🛠️ Kullanılan Teknolojiler
Frontend: Streamlit

Yapay Zeka Motoru: Google Gemini 1.5 Flash API

Web Scraping: BeautifulSoup & Requests

Backend Dil: Python

🔑 API Anahtarı Kurulumu
Bu proje sözleşme analizi için Google Gemini API kullanmaktadır. 
Projeyi kendi bilgisayarınızda çalıştırmadan önce .streamlit klasörü içinde secrets.toml dosyası oluşturun:
```bash
GEMINI_API_KEY = "BURAYA_KENDI_GEMINI_API_KEYINIZI_YAZIN"
```
👥 Geliştirici Ekip (X Team)
Fatma Nur Atagün

Hayrunnisa Kaya

Serra Çolak

Hilal Nur Okur
