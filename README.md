# 📄 Sözleşme Rehberim - AI Risk Analizi
Bu proje, dijital platformların karmaşık hukuki sözleşmelerini Üretken Yapay Zeka (Gemini 1.5 Flash) kullanarak saniyeler içinde analiz eden, son kullanıcı odaklı bir MVP web uygulamasıdır.
## 🚀 Kurulum ve Çalıştırma
1. Gerekli kütüphaneleri yükleyin: pip install streamlit google-generativeai
2. Kodu çalıştırmak için terminale yazın: streamlit run app.py
## 🛠️ Kullanılan Teknolojiler
- *Frontend:* Streamlit
- *Yapay Zeka Motoru:* Google Gemini 1.5 Flash API
- *Backend Dil:* Python

## 👥 Geliştirici Ekip
Hilal, Fatma, Hayrunnisa, Serra
## API Anahtarı Kurulumu

Bu proje Gemini API kullanmaktadır.

Projeyi çalıştırmadan önce `.streamlit` klasörü içinde `secrets.toml` dosyası oluşturun.

Örnek:

```toml
GEMINI_API_KEY = "BURAYA_KENDI_GEMINI_API_KEYINIZI_YAZIN"
