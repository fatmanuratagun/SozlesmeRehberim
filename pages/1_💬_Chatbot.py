import streamlit as st
import google.generativeai as genai

# --- AYARLAR ---
API_KEY = "AIzaSyBRhmbrEb9l8DGMnO4uhzUIlp_D3hRWcIc"
genai.configure(api_key=API_KEY)

dogru_model_adi = "gemini-1.5-flash"
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        dogru_model_adi = m.name
        break
model = genai.GenerativeModel(dogru_model_adi)

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Sözleşme Asistanı", page_icon="💬", layout="wide")
st.title("💬 Sözleşme Asistanı")
st.markdown("Yüklediğiniz sözleşme hakkında her şeyi sorun.")
st.divider()

# --- SESSION STATE KONTROL ---
if "chat_gecmisi" not in st.session_state:
    st.session_state.chat_gecmisi = []

if "analiz_metni" not in st.session_state or not st.session_state.get("sozlesme_yuklendi", False):
    st.warning("⚠️ Önce **Ana Sayfa**'dan bir sözleşme yükleyin.")
    st.page_link("Ana_Sayfa.py", label="← Ana Sayfaya Git", icon="⚖️")
    st.stop()

st.success("✅ Sözleşme yüklendi. Sorularınızı yazın!")
st.caption("💡 Örnek: *'Aboneliği nasıl iptal edebilirim?'* · *'Verilerim kimlerle paylaşılıyor?'* · *'Fiyat artışı yapılabilir mi?'*")

# --- SOHBET GEÇMİŞİNİ GÖSTER ---
if not st.session_state.chat_gecmisi:
    with st.chat_message("assistant"):
        st.markdown("👋 Merhaba! Yüklediğiniz sözleşme hakkında her şeyi sorabilirsiniz.")

for mesaj in st.session_state.chat_gecmisi:
    with st.chat_message(mesaj["rol"]):
        st.markdown(mesaj["icerik"])

# --- CHAT INPUT (ana sayfa seviyesinde, sütun yok) ---
kullanici_sorusu = st.chat_input("Sözleşme hakkında bir soru sorun...")

if kullanici_sorusu:
    with st.chat_message("user"):
        st.markdown(kullanici_sorusu)
    st.session_state.chat_gecmisi.append({"rol": "user", "icerik": kullanici_sorusu})

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                sistem_prompt = f"""Sen bir hukuki sözleşme asistanısın. Kullanıcıya aşağıdaki sözleşme metni hakkında yardım ediyorsun.
Cevaplarını sade, anlaşılır ve Türkçe ver. Resmi avukat olmadığını gerektiğinde belirt.
Yalnızca sözleşmeyle ilgili soruları yanıtla.

--- SÖZLEŞME METNİ ---
{st.session_state.analiz_metni[:12000]}
--- SÖZLEŞME METNİ SONU ---
"""
                gemini_gecmis = []
                for m in st.session_state.chat_gecmisi[:-1]:
                    gemini_gecmis.append({
                        "role": "user" if m["rol"] == "user" else "model",
                        "parts": [m["icerik"]]
                    })

                chat = model.start_chat(history=gemini_gecmis)

                if len(st.session_state.chat_gecmisi) == 1:
                    tam_soru = sistem_prompt + "\n\nKullanıcı sorusu: " + kullanici_sorusu
                else:
                    tam_soru = kullanici_sorusu

                yanit = chat.send_message(tam_soru)
                asistan_yaniti = yanit.text

            except Exception as e:
                asistan_yaniti = f"❌ Hata: {e}"

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
