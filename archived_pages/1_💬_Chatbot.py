import streamlit as st
import google.generativeai as genai

# --- AYARLAR ---
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY")
except FileNotFoundError:
    API_KEY = None

if not API_KEY:
    st.error("Gemini API anahtarı bulunamadı. `.streamlit/secrets.toml` içine GEMINI_API_KEY ekleyin.")
    st.stop()

genai.configure(api_key=API_KEY)

dogru_model_adi = "gemini-2.5-flash"
model = genai.GenerativeModel(dogru_model_adi)

def ai_hata_mesaji(e):
    hata = str(e).lower()
    if "429" in hata or "quota" in hata or "rate" in hata:
        return "AI şu anda yoğun. Lütfen birkaç saniye sonra tekrar deneyin."
    return "AI yanıtı alınamadı. Lütfen birkaç saniye sonra tekrar deneyin."

st.set_page_config(page_title="Sözleşme Asistanı", page_icon="💬", layout="wide")
st.title("💬 Sözleşme Asistanı")
st.markdown("Yüklediğiniz sözleşme hakkında her şeyi sorun.")
st.divider()
 
# --- SESSION STATE ---
if "chat_gecmisi" not in st.session_state:
    st.session_state.chat_gecmisi = []
 
if not st.session_state.get("sozlesme_yuklendi", False):
    st.warning("⚠️ Önce **Ana Sayfa**'dan bir sözleşme yükleyin.")
    st.page_link("Ana_Sayfa.py", label="← Ana Sayfaya Git", icon="⚖️")
    st.stop()
 
st.success("✅ Sözleşme yüklendi. Sorularınızı yazın!")
st.caption("💡 Örnek: *'Aboneliği nasıl iptal edebilirim?'* · *'Verilerim kimlerle paylaşılıyor?'* · *'Fiyat artışı yapılabilir mi?'*")
 
# --- SOHBET GEÇMİŞİ ---
if not st.session_state.chat_gecmisi:
    with st.chat_message("assistant"):
        st.markdown("👋 Merhaba! Yüklediğiniz sözleşme hakkında her şeyi sorabilirsiniz.")
 
for mesaj in st.session_state.chat_gecmisi:
    with st.chat_message(mesaj["rol"]):
        st.markdown(mesaj["icerik"])
 
# --- CHAT INPUT ---
# --- CHAT INPUT ---
kullanici_sorusu = st.chat_input("Sözleşme hakkında bir soru sorun...")

if kullanici_sorusu:
    with st.chat_message("user"):
        st.markdown(kullanici_sorusu)
    st.session_state.chat_gecmisi.append({"rol": "user", "icerik": kullanici_sorusu})

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                # Gemini için prompt hazırlığı
                sözlesme_metni = st.session_state.get("analiz_metni", "")
                
                sistem_prompt = f"""Sen bir hukuki sözleşme asistanısın. 
                Sana bir sözleşme metni verilecek. Eğer soru bu metinle ilgiliyse metne sadık kal.
                Eğer soru genel bir konuysa (selamlaşma, genel bilgi vb.), sözleşmeden bağımsız olarak kibarca cevap ver.
                
                --- SÖZLEŞME METNİ ---
                {sözlesme_metni[:15000]} 
                --- SÖZLEŞME METNİ SONU ---"""

                # Mesaj geçmişini Gemini'nin anlayacağı formata çeviriyoruz
                # Gemini flash modelini kullanarak cevap üretiyoruz
                full_prompt = f"{sistem_prompt}\n\nKullanıcı Sorusu: {kullanici_sorusu}"
                
                response = model.generate_content(full_prompt)
                asistan_yaniti = response.text

            except Exception as e:
                asistan_yaniti = ai_hata_mesaji(e)

        st.markdown(asistan_yaniti)
        st.session_state.chat_gecmisi.append({"rol": "assistant", "icerik": asistan_yaniti})
 
# --- BUTONLAR ---
st.divider()
col1, col2 = st.columns(2)
 
with col1:
    if st.session_state.chat_gecmisi:
        if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
            st.session_state.chat_gecmisi = []
            st.rerun()
 
with col2:
    if st.button("🔄 Yeni Sözleşme Yükle", use_container_width=True):
        st.session_state.analiz_metni = ""
        st.session_state.sozlesme_yuklendi = False
        st.session_state.analiz_sonucu = ""
        st.session_state.chat_gecmisi = []
        st.switch_page("Ana_Sayfa.py")
