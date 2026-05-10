from html import escape

import google.generativeai as genai
import streamlit as st

from shared_theme import load_shared_theme, render_icon_sidebar


def api_anahtari_al():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except FileNotFoundError:
        api_key = None

    if not api_key:
        st.error("Gemini API anahtarı bulunamadı. `.streamlit/secrets.toml` içine GEMINI_API_KEY ekleyin.")
        st.stop()
    return api_key


@st.cache_resource(show_spinner=False)
def model_olustur():
    genai.configure(api_key=api_anahtari_al())
    dogru_model_adi = "gemini-1.5-flash"
    for model_bilgisi in genai.list_models():
        if "generateContent" in model_bilgisi.supported_generation_methods:
            dogru_model_adi = model_bilgisi.name
            break
    return genai.GenerativeModel(dogru_model_adi)


def sidebar_menu():
    render_icon_sidebar("chatbot")


def stil_yukle():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(37, 99, 235, 0.18), transparent 28%),
                radial-gradient(circle at 88% 18%, rgba(20, 184, 166, 0.12), transparent 26%),
                linear-gradient(135deg, #070a12 0%, #0b1220 48%, #020617 100%);
            color: #eef2ff;
        }
        .main .block-container {
            max-width: 1160px;
            padding-top: 2.2rem;
            padding-bottom: 7.5rem;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        section[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.92);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 18px 0 55px rgba(0, 0, 0, 0.22);
        }
        section[data-testid="stSidebar"] a {
            border-radius: 12px;
            transition: all 180ms ease;
        }
        section[data-testid="stSidebar"] a:hover {
            background: rgba(37, 99, 235, 0.16);
            transform: translateX(3px);
        }
        .chat-hero {
            max-width: 1120px;
            min-height: 330px;
            position: relative;
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(250px, 360px);
            align-items: center;
            gap: clamp(1.5rem, 4vw, 3.5rem);
            border: 1px solid rgba(148, 163, 184, 0.18);
            background:
                radial-gradient(circle at 82% 48%, rgba(56, 189, 248, 0.16), transparent 30%),
                radial-gradient(circle at 18% 0%, rgba(37, 99, 235, 0.12), transparent 34%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.78), rgba(8, 13, 26, 0.66));
            border-radius: 22px;
            padding: clamp(2.4rem, 5vw, 4.3rem) clamp(2.2rem, 5vw, 4.6rem);
            box-shadow: 0 22px 62px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.045);
            margin: 0 auto 42px;
            backdrop-filter: blur(18px);
            overflow: hidden;
        }
        .chat-hero-content {
            position: relative;
            z-index: 2;
        }
        .chat-title {
            max-width: 820px;
            font-size: clamp(2.9rem, 5vw, 4.6rem);
            line-height: 0.98;
            font-weight: 900;
            letter-spacing: 0;
            margin: 0;
            color: #f8fafc;
            text-shadow: 0 8px 34px rgba(37, 99, 235, 0.10);
        }
        .chat-subtitle {
            color: rgba(203, 213, 225, 0.84);
            font-size: 1.08rem;
            margin-top: 18px;
            max-width: 650px;
            line-height: 1.7;
        }
        .chat-feature-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
        }
        .status-pill,
        .chat-feature-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            min-height: 36px;
            border: 1px solid rgba(125, 211, 252, 0.18);
            background:
                linear-gradient(135deg, rgba(14, 165, 233, 0.085), rgba(37, 99, 235, 0.05)),
                rgba(15, 23, 42, 0.42);
            color: rgba(219, 234, 254, 0.92);
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.88rem;
            font-weight: 720;
            line-height: 1.25;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 8px 20px rgba(2, 6, 23, 0.14);
            transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
        }
        .status-pill:hover,
        .chat-feature-chip:hover {
            transform: translateY(-1px);
            border-color: rgba(125, 211, 252, 0.34);
            background:
                linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(37, 99, 235, 0.07)),
                rgba(15, 23, 42, 0.50);
        }
        .chat-hero-visual {
            position: relative;
            z-index: 1;
            min-height: 230px;
            display: grid;
            place-items: center;
            opacity: 0.78;
        }
        .chat-hero-visual::before {
            content: "";
            position: absolute;
            width: min(320px, 32vw);
            aspect-ratio: 1;
            border-radius: 999px;
            background:
                radial-gradient(circle, rgba(56, 189, 248, 0.20), rgba(37, 99, 235, 0.08) 42%, transparent 68%);
            filter: blur(16px);
        }
        .chat-scale-mark {
            position: relative;
            width: min(270px, 30vw);
            aspect-ratio: 1;
            display: grid;
            place-items: center;
            border-radius: 999px;
            border: 1px solid rgba(125, 211, 252, 0.16);
            background:
                radial-gradient(circle at 50% 42%, rgba(56, 189, 248, 0.10), transparent 46%),
                rgba(15, 23, 42, 0.22);
            color: rgba(191, 219, 254, 0.34);
            font-size: clamp(7rem, 14vw, 10rem);
            line-height: 1;
            text-shadow: 0 0 36px rgba(56, 189, 248, 0.22);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035), 0 0 42px rgba(37, 99, 235, 0.08);
        }
        .chat-scale-mark::after {
            content: "";
            position: absolute;
            inset: 16%;
            border-radius: 999px;
            border: 1px solid rgba(125, 211, 252, 0.08);
        }
        .chat-panel {
            max-width: 1120px;
            margin: 0 auto 22px;
            padding: 20px;
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 22px;
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.50), rgba(8, 13, 26, 0.36));
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
        }
        .messages {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .message-row {
            display: flex;
            width: 100%;
        }
        .message-row.user {
            justify-content: flex-end;
        }
        .message-row.assistant {
            justify-content: flex-start;
        }
        .message-card {
            max-width: min(760px, 86%);
            border-radius: 20px;
            padding: 17px 19px;
            box-shadow: 0 14px 38px rgba(0, 0, 0, 0.22);
            border: 1px solid rgba(148, 163, 184, 0.18);
            line-height: 1.62;
            font-size: 0.98rem;
            overflow-wrap: anywhere;
        }
        .message-card.user {
            background:
                linear-gradient(135deg, rgba(37, 99, 235, 0.96), rgba(8, 145, 178, 0.88));
            color: white;
            border-color: rgba(125, 211, 252, 0.22);
            border-bottom-right-radius: 7px;
            box-shadow: 0 16px 34px rgba(37, 99, 235, 0.20);
        }
        .message-card.assistant {
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.82), rgba(8, 13, 26, 0.72));
            color: #e5e7eb;
            border-color: rgba(125, 211, 252, 0.16);
            border-bottom-left-radius: 7px;
            box-shadow: 0 15px 36px rgba(0, 0, 0, 0.22), 0 0 24px rgba(56, 189, 248, 0.045);
        }
        .message-card h3 {
            color: #bfdbfe;
            margin: 0.6rem 0 0.35rem;
            font-size: 1rem;
        }
        .message-card ul {
            margin: 0.35rem 0 0.65rem 1.1rem;
            padding: 0;
        }
        .message-card li {
            margin-bottom: 0.25rem;
        }
        .empty-state {
            border: 1px dashed rgba(125, 211, 252, 0.26);
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.64), rgba(8, 13, 26, 0.50));
            border-radius: 18px;
            padding: 28px;
            color: #cbd5e1;
            box-shadow: 0 14px 38px rgba(0, 0, 0, 0.18);
        }
        .chat-warning-card {
            max-width: 1120px;
            margin: 0 auto 18px;
            padding: 18px 20px;
            border: 1px solid rgba(251, 191, 36, 0.24);
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(251, 191, 36, 0.10), rgba(37, 99, 235, 0.045)),
                rgba(15, 23, 42, 0.62);
            color: #fde68a;
            box-shadow: 0 14px 34px rgba(0, 0, 0, 0.20), inset 0 1px 0 rgba(255, 255, 255, 0.035);
            font-weight: 730;
        }
        .typing {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: #cbd5e1;
        }
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #60a5fa;
            animation: typingPulse 1.2s infinite ease-in-out;
        }
        .typing-dot:nth-child(2) {
            animation-delay: 0.16s;
        }
        .typing-dot:nth-child(3) {
            animation-delay: 0.32s;
        }
        @keyframes typingPulse {
            0%, 80%, 100% {
                transform: translateY(0);
                opacity: 0.35;
            }
            40% {
                transform: translateY(-5px);
                opacity: 1;
            }
        }
        div[data-testid="stChatInput"] {
            max-width: 1120px;
            margin: 0 auto 18px;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 1rem !important;
        }
        div[data-testid="stChatInput"] > div {
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
            border-radius: 22px !important;
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.74), rgba(8, 13, 26, 0.62)) !important;
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
            padding: 14px !important;
            backdrop-filter: blur(18px);
            overflow: visible !important;
        }
        div[data-testid="stChatInput"] > div > div,
        div[data-testid="stChatInput"] [data-baseweb="textarea"],
        div[data-testid="stChatInput"] [data-baseweb="base-input"] {
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            border-radius: 16px !important;
            overflow: visible !important;
        }
        div[data-testid="stChatInput"] [data-baseweb="textarea"]::before,
        div[data-testid="stChatInput"] [data-baseweb="textarea"]::after,
        div[data-testid="stChatInput"] [data-baseweb="base-input"]::before,
        div[data-testid="stChatInput"] [data-baseweb="base-input"]::after {
            content: none !important;
            display: none !important;
        }
        div[data-testid="stChatInput"] textarea {
            min-height: 44px !important;
            border-radius: 16px !important;
            border: 1px solid rgba(103, 232, 249, 0.38) !important;
            background: linear-gradient(180deg, rgba(8, 18, 38, 0.96), rgba(10, 24, 50, 0.86)) !important;
            color: #f8fafc !important;
            box-shadow:
                inset 0 2px 9px rgba(0, 0, 0, 0.24),
                inset 0 1px 0 rgba(255, 255, 255, 0.045),
                0 0 0 1px rgba(56, 189, 248, 0.03) !important;
            padding: 12px 14px !important;
            line-height: 1.45 !important;
        }
        div[data-testid="stChatInput"] textarea:focus {
            border-color: rgba(103, 232, 249, 0.70) !important;
            box-shadow:
                0 0 0 3px rgba(34, 211, 238, 0.09),
                0 0 18px rgba(34, 211, 238, 0.08),
                inset 0 2px 9px rgba(0, 0, 0, 0.24) !important;
            outline: none !important;
        }
        div[data-testid="stChatInput"] button {
            border-radius: 13px !important;
            border: 1px solid rgba(125, 211, 252, 0.22) !important;
            background: rgba(37, 99, 235, 0.18) !important;
            color: #dbeafe !important;
            box-shadow: none !important;
        }
        div[data-testid="stChatInput"] button:hover {
            border-color: rgba(125, 211, 252, 0.46) !important;
            background: rgba(37, 99, 235, 0.30) !important;
        }
        .stButton > button {
            border-radius: 14px !important;
            border: 1px solid rgba(96, 165, 250, 0.28) !important;
            background: rgba(15, 23, 42, 0.84) !important;
            color: #f8fafc !important;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
            font-weight: 750 !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            border-color: rgba(34, 211, 238, 0.76) !important;
            box-shadow: 0 18px 44px rgba(37, 99, 235, 0.22);
        }
        @media (max-width: 720px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .message-card {
                max-width: 94%;
            }
            .chat-hero {
                min-height: auto;
                grid-template-columns: 1fr;
                gap: 1.3rem;
                padding: 24px;
            }
            .chat-title {
                font-size: clamp(2.25rem, 14vw, 3.2rem);
            }
            .chat-hero-visual {
                min-height: 120px;
                opacity: 0.42;
                margin-top: -0.4rem;
            }
            .chat-scale-mark {
                width: min(180px, 56vw);
                font-size: clamp(5rem, 24vw, 7rem);
            }
            .chat-panel {
                padding: 14px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mesaj_html(metin):
    html_satirlari = []
    liste_acik = False

    for ham_satir in metin.splitlines():
        satir = ham_satir.strip()
        if not satir:
            if liste_acik:
                html_satirlari.append("</ul>")
                liste_acik = False
            continue

        if satir.startswith(("- ", "* ")):
            if not liste_acik:
                html_satirlari.append("<ul>")
                liste_acik = True
            html_satirlari.append(f"<li>{escape(satir[2:])}</li>")
            continue

        if liste_acik:
            html_satirlari.append("</ul>")
            liste_acik = False

        temiz = escape(satir).strip("*")
        if satir.startswith(("### ", "## ", "# ")):
            temiz = escape(satir.lstrip("#").strip())
            html_satirlari.append(f"<h3>{temiz}</h3>")
        elif satir.endswith(":") and len(satir) < 80:
            html_satirlari.append(f"<h3>{temiz}</h3>")
        else:
            html_satirlari.append(f"<p>{temiz}</p>")

    if liste_acik:
        html_satirlari.append("</ul>")

    return "\n".join(html_satirlari)


def mesaj_goster(rol, icerik):
    kart_rolu = "user" if rol == "user" else "assistant"
    st.markdown(
        f"""
        <div class="message-row {kart_rolu}">
            <div class="message-card {kart_rolu}">
                {mesaj_html(icerik)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def typing_goster():
    st.markdown(
        """
        <div class="message-row assistant">
            <div class="message-card assistant">
                <div class="typing">
                    <span>AI yanıt hazırlıyor</span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chatbot_yaniti_uret(model, kullanici_sorusu):
    sozlesme_metni = st.session_state.get("analiz_metni", "")
    gecmis = "\n".join(
        f"{mesaj['rol']}: {mesaj['icerik']}"
        for mesaj in st.session_state.chat_gecmisi[-8:]
    )

    sistem_prompt = f"""Sen Sözleşme Analizi AI adlı premium bir hukuki sözleşme asistanısın.
Resmi avukat gibi davranma; açık, sade ve dikkatli açıklama yap.
Soru sözleşmeyle ilgiliyse sadece verilen sözleşme metnine dayan. Metinde yoksa bunu açıkça belirt.
Cevaplarını mümkün olduğunda şu başlıklarla düzenle:

### Riskler
### Kritik Maddeler
### Veri Paylaşımı
### Kullanıcı Hakları
### İptal ve Cayma Koşulları

Her başlık altında kısa, taranabilir maddeler kullan. Gereksiz başlığı boş bırakma; ilgili değilse "Bu konuda metinde açık bilgi yok." yaz.

--- SÖZLEŞME METNİ ---
{sozlesme_metni[:18000]}
--- SÖZLEŞME METNİ SONU ---

--- SOHBET GEÇMİŞİ ---
{gecmis}
--- SOHBET GEÇMİŞİ SONU ---"""

    response = model.generate_content(f"{sistem_prompt}\n\nKullanıcı sorusu: {kullanici_sorusu}")
    return response.text


st.set_page_config(page_title="Sözleşme Analizi AI", page_icon="💬", layout="wide")
load_shared_theme()
stil_yukle()
sidebar_menu()

if "chat_gecmisi" not in st.session_state:
    st.session_state.chat_gecmisi = []

st.markdown(
    """
    <section class="chat-hero">
        <div class="chat-hero-content">
            <h1 class="chat-title">Sözleşme Analizi AI</h1>
            <div class="chat-subtitle">
                Sözleşmenizdeki riskleri, kritik maddeleri, veri paylaşımı koşullarını ve kullanıcı haklarını sade bir dille sorun.
            </div>
            <div class="chat-feature-row">
                <span class="chat-feature-chip">🔒 Güvenli Sohbet</span>
                <span class="chat-feature-chip">⚖️ Hukuki Risk Analizi</span>
                <span class="chat-feature-chip">🤖 AI Destekli Yanıtlar</span>
            </div>
        </div>
        <div class="chat-hero-visual" aria-hidden="true">
            <div class="chat-scale-mark">⚖️</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.get("sozlesme_yuklendi", False):
    st.markdown(
        """
        <div class="chat-warning-card">
            Önce Ana Sayfa'dan bir sözleşme yükleyin.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("Ana_Sayfa.py", label="Ana Sayfaya Git", icon="🏠")
    st.stop()

model = model_olustur()

st.markdown('<section class="chat-panel"><div class="messages">', unsafe_allow_html=True)

if not st.session_state.chat_gecmisi:
    st.markdown(
        """
        <div class="empty-state">
            Merhaba. Sözleşmenizi okuyorum; riskler, kritik maddeler, veri paylaşımı, kullanıcı hakları veya iptal koşulları hakkında soru sorabilirsiniz.
        </div>
        """,
        unsafe_allow_html=True,
    )

for mesaj in st.session_state.chat_gecmisi:
    mesaj_goster(mesaj["rol"], mesaj["icerik"])

st.markdown("</div></section>", unsafe_allow_html=True)

if st.session_state.chat_gecmisi:
    if st.button("Sohbeti Temizle", use_container_width=False):
        st.session_state.chat_gecmisi = []
        st.rerun()

kullanici_sorusu = st.chat_input("Sözleşme hakkında bir soru sorun...")

if kullanici_sorusu:
    st.session_state.chat_gecmisi.append({"rol": "user", "icerik": kullanici_sorusu})
    mesaj_goster("user", kullanici_sorusu)
    typing_placeholder = st.empty()

    with typing_placeholder:
        typing_goster()

    try:
        asistan_yaniti = chatbot_yaniti_uret(model, kullanici_sorusu)
    except Exception as e:
        asistan_yaniti = f"Bir hata oluştu: {e}"

    typing_placeholder.empty()
    st.session_state.chat_gecmisi.append({"rol": "assistant", "icerik": asistan_yaniti})
    st.rerun()
