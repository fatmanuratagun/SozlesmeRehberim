import streamlit as st
import google.generativeai as genai

# 1. Gemini API Ayarları
API_KEY = "BURAYA_API_KEY_GELECEK"
genai.configure(api_key=API_KEY)

# --- YENİ: OTOMATİK MODEL BULUCU ---
dogru_model_adi = "gemini-1.5-flash" # Varsayılan
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        dogru_model_adi = m.name # Çalışan ilk modeli otomatik al
        break 
        
model = genai.GenerativeModel(dogru_model_adi)
# -----------------------------------

# 2. Sayfa Tasarımı
st.set_page_config(page_title="Sözleşme Rehberim", page_icon="📄", layout="wide")

st.title("📄 Sözleşme Rehberim - AI Risk Analizi")
st.markdown("Karmaşık hukuki sözleşmeleri yapıştırın, saniyeler içinde riskleri öğrenin.")
st.divider()

# Kullanıcıdan sözleşme metnini alma
sozlesme_metni = st.text_area("Lütfen analiz edilecek sözleşme metnini buraya yapıştırın:", height=250)

# Butona basıldığında çalışacak analiz süreci
if st.button("Sözleşmeyi Analiz Et 🔍", use_container_width=True):
    if sozlesme_metni.strip() == "":
        st.warning("Lütfen analiz etmek için bir metin girin!")
    else:
        with st.spinner("Yapay Zeka sözleşmeyi okuyor ve riskleri tespit ediyor..."):
            try:
                # Gemini'ye gidecek özel komut (Prompt)
                prompt = f"""
                Sen uzman bir avukatsın. Aşağıdaki sözleşme metnini oku ve sıradan bir vatandaşın anlayacağı dilde şu formatta cevap ver:
                1. Sözleşmenin Genel Özeti (Maksimum 2 cümle)
                2. Kullanıcı İçin Kritik Riskler (Veri paylaşımı, gizli ücretler vb. varsa madde madde yaz)
                3. Genel Güvenlik Skoru (10 üzerinden bir puan ver)
                
                Sözleşme Metni:
                {sozlesme_metni}
                """
                
                # Modeli çağırma ve cevabı alma
                response = model.generate_content(prompt)
                
                # 3. Sonuçları Ekrana Yazdırma
                st.success("Analiz Tamamlandı!")
                st.markdown("### 📊 Yapay Zeka Analiz Raporu")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")