import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import docx
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from pathlib import Path
import re
from html import unescape as html_unescape
from xml.sax.saxutils import escape

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

# --- YARDIMCI FONKSİYONLAR ---
def dokuman_okuyucu(yuklenen_dosya):
    metin = ""
    try:
        dosya_adi = yuklenen_dosya.name.lower()
        if dosya_adi.endswith('.pdf'):
            pdf_nesnesi = PdfReader(yuklenen_dosya)
            for sayfa in pdf_nesnesi.pages:
                sayfa_metni = sayfa.extract_text()
                if sayfa_metni:
                    metin += sayfa_metni + "\n"
        elif dosya_adi.endswith('.docx'):
            doc = docx.Document(yuklenen_dosya)
            for paragraf in doc.paragraphs:
                metin += paragraf.text + "\n"
        elif dosya_adi.endswith('.txt'):
            metin = yuklenen_dosya.getvalue().decode("utf-8")
        return metin
    except Exception as e:
        st.error(f"Doküman okunurken hata: {e}")
        return None

def url_okuyucu(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        st.error(f"Bağlantıdan metin çekilemedi. Hata: {e}")
        return None

def pdf_fontlarini_hazirla():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    normal_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    font_klasoru = Path("C:/Windows/Fonts")
    normal_yol = font_klasoru / "arial.ttf"
    bold_yol = font_klasoru / "arialbd.ttf"

    if normal_yol.exists():
        pdfmetrics.registerFont(TTFont("ArialTR", str(normal_yol)))
        normal_font = "ArialTR"

    if bold_yol.exists():
        pdfmetrics.registerFont(TTFont("ArialTR-Bold", str(bold_yol)))
        bold_font = "ArialTR-Bold"

    return normal_font, bold_font

def analiz_pdf_olustur(analiz_metni):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = BytesIO()
    normal_font, bold_font = pdf_fontlarini_hazirla()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Sözleşme Analizi",
    )

    styles = getSampleStyleSheet()
    baslik = ParagraphStyle(
        "Baslik",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )
    meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName=normal_font,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=16,
    )
    govde = ParagraphStyle(
        "Govde",
        parent=styles["BodyText"],
        fontName=normal_font,
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceAfter=7,
    )
    madde = ParagraphStyle(
        "Madde",
        parent=govde,
        leftIndent=14,
        firstLineIndent=-8,
    )

    icerik = [
        Paragraph("Sözleşme Analizi", baslik),
        Paragraph(f"Oluşturulma tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", meta),
    ]

    for satir in analiz_metni.splitlines():
        temiz_satir = satir.strip()
        if not temiz_satir:
            icerik.append(Spacer(1, 6))
            continue

        temiz_satir = temiz_satir.replace("**", "").replace("###", "").replace("##", "").replace("#", "").strip()
        paragraf_stili = madde if temiz_satir.startswith(("-", "*", "•")) else govde
        icerik.append(Paragraph(escape(temiz_satir), paragraf_stili))

    doc.build(icerik)
    buffer.seek(0)
    return buffer.getvalue()

def html_taglerini_temizle(metin):
    temiz = html_unescape(str(metin or ""))
    temiz = re.sub(r"```(?:html)?|```", "", temiz, flags=re.IGNORECASE)
    temiz = re.sub(r"</(article|div|section|p|h[1-6]|li|ul|ol)>", "\n", temiz, flags=re.IGNORECASE)
    temiz = re.sub(r"<br\s*/?>", "\n", temiz, flags=re.IGNORECASE)
    temiz = re.sub(r"<[^>]+>", "", temiz)
    temiz = re.sub(r"\b(class|style|id)=\"[^\"]*\"", "", temiz, flags=re.IGNORECASE)
    temiz = re.sub(r"[ \t]+\n", "\n", temiz)
    temiz = re.sub(r"\n{3,}", "\n\n", temiz)
    return temiz.strip()


def analiz_bolumu_bul(analiz_metni, anahtarlar, fallback="Bu başlık için analiz metninde ayrı bir bölüm bulunamadı."):
    analiz_metni = html_taglerini_temizle(analiz_metni)
    satirlar = [satir.strip() for satir in analiz_metni.splitlines() if satir.strip()]
    baslangic = None

    for index, satir in enumerate(satirlar):
        kucuk_satir = satir.lower()
        if any(anahtar.lower() in kucuk_satir for anahtar in anahtarlar):
            baslangic = index
            break

    if baslangic is None:
        return fallback

    secilenler = []
    for satir in satirlar[baslangic:]:
        yeni_baslik = re.match(r"^[#*\s]*(\d+[\).\s-]+|[📋📝🚨🇹🇷🛡️]).{3,}", satir)
        if secilenler and yeni_baslik:
            break
        secilenler.append(satir.replace("**", "").replace("###", "").replace("##", "").replace("#", "").strip())
        if len(secilenler) >= 5:
            break

    return "\n".join(secilenler) if secilenler else fallback

def analiz_sonuc_kartlari(analiz_metni):
    analiz_metni = html_taglerini_temizle(analiz_metni)
    kartlar = [
        ("Risk Skoru", "🛡️", analiz_bolumu_bul(analiz_metni, ["güvenlik skoru", "risk skoru", "puan"])),
        ("Kritik Maddeler", "⚠️", analiz_bolumu_bul(analiz_metni, ["kritik risk", "kritik madde", "riskler"])),
        ("Veri Paylaşımı", "🔐", analiz_bolumu_bul(analiz_metni, ["kvkk", "veri", "kişisel", "aktar"])),
        ("Kullanıcı Hakları", "👤", analiz_bolumu_bul(analiz_metni, ["kullanıcı hak", "taraflar", "cayma", "iptal"])),
        ("Abonelik Riskleri", "↻", analiz_bolumu_bul(analiz_metni, ["abonelik", "ücret", "fiyat", "fesih", "cayma"])),
    ]

    kart_html = []
    for baslik, ikon, metin in kartlar:
        satirlar = "".join(f"<p>{escape(satir)}</p>" for satir in metin.splitlines() if satir.strip())
        kart_html.append(
            f"""
            <article class="result-card">
                <div class="result-card-icon">{ikon}</div>
                <div>
                    <h3>{escape(baslik)}</h3>
                    {satirlar}
                </div>
            </article>
            """
        )

    return '<section class="result-grid">' + "\n".join(kart_html) + "</section>"

# --- SESSION STATE ---
if "analiz_metni" not in st.session_state:
    st.session_state.analiz_metni = ""
if "sozlesme_yuklendi" not in st.session_state:
    st.session_state.sozlesme_yuklendi = False
if "analiz_sonucu" not in st.session_state:
    st.session_state.analiz_sonucu = ""
if "chat_gecmisi" not in st.session_state:
    st.session_state.chat_gecmisi = []
if "son_url" not in st.session_state:
    st.session_state.son_url = ""
# widget_key: sıfırla butonuna basınca artar → tüm widget'lar temizlenir
if "widget_key" not in st.session_state:
    st.session_state.widget_key = 0
if "metin_aktarildi" not in st.session_state:
    st.session_state.metin_aktarildi = False
if "link_aktarildi" not in st.session_state:
    st.session_state.link_aktarildi = False
if "analiz_yapiliyor" not in st.session_state:
    st.session_state.analiz_yapiliyor = False
if "analiz_tetikle" not in st.session_state:
    st.session_state.analiz_tetikle = False
if "analiz_hatasi" not in st.session_state:
    st.session_state.analiz_hatasi = ""

# --- SAYFA ---
st.set_page_config(page_title="Sözleşme Rehberim", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")
load_shared_theme()

st.markdown(
    """
    <style>
    /* Non-invasive UI polish: backend and Streamlit flow stay unchanged. */
    :root {
        --panel-bg: rgba(15, 23, 42, 0.68);
        --panel-border: rgba(148, 163, 184, 0.18);
        --accent: #38bdf8;
        --accent-strong: #2563eb;
        --text-soft: #94a3b8;
    }
    .stApp {
        background:
            radial-gradient(circle at 14% 5%, rgba(37, 99, 235, 0.20), transparent 28%),
            radial-gradient(circle at 88% 16%, rgba(45, 212, 191, 0.12), transparent 24%),
            linear-gradient(135deg, #070a12 0%, #0b1220 48%, #020617 100%) !important;
    }
    .main .block-container {
        max-width: 1120px;
        padding-top: 2.2rem;
        padding-bottom: 4.2rem;
    }
    .hero-shell,
    div[data-testid="stTabs"],
    .result-card,
    .legal-note,
    div[data-testid="stExpander"],
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--panel-border) !important;
        background: var(--panel-bg) !important;
        border-radius: 18px !important;
        box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
        backdrop-filter: blur(18px);
    }
    .hero-shell {
        padding: 26px 28px;
        margin-bottom: 24px;
    }
    .hero-title {
        font-size: clamp(2.25rem, 4vw, 3.6rem) !important;
        font-weight: 850 !important;
        letter-spacing: 0 !important;
    }
    .hero-copy {
        color: rgba(203, 213, 225, 0.82) !important;
    }
    .hero-kicker {
        border-color: rgba(45, 212, 191, 0.32) !important;
        background: rgba(20, 184, 166, 0.10) !important;
        color: #99f6e4 !important;
    }
    div[data-testid="stTabs"] [role="tablist"] {
        border: 1px solid rgba(148, 163, 184, 0.14) !important;
        border-radius: 999px !important;
        padding: 7px !important;
        background: rgba(2, 6, 23, 0.42) !important;
    }
    div[data-testid="stTabs"] [role="tab"] {
        border-radius: 999px !important;
        transition: transform 180ms ease, background 180ms ease, box-shadow 180ms ease !important;
    }
    div[data-testid="stTabs"] [role="tab"]:hover {
        transform: translateY(-1px);
        background: rgba(37, 99, 235, 0.18) !important;
    }
    div[data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #0891b2) !important;
        color: #ffffff !important;
        box-shadow: 0 14px 34px rgba(37, 99, 235, 0.28), 0 0 24px rgba(56, 189, 248, 0.16) !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed rgba(125, 211, 252, 0.42) !important;
        border-radius: 18px !important;
        background: rgba(15, 23, 42, 0.72) !important;
        transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease !important;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.78) !important;
        box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.08), 0 18px 48px rgba(37, 99, 235, 0.18) !important;
    }
    textarea,
    input {
        border-radius: 16px !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        background: rgba(15, 23, 42, 0.82) !important;
        color: #f8fafc !important;
    }
    textarea:focus,
    input:focus {
        border-color: rgba(56, 189, 248, 0.76) !important;
        box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.12), 0 18px 44px rgba(0, 0, 0, 0.28) !important;
    }
    .stButton > button[kind="primary"],
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 14px !important;
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease !important;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
    }
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
        border: 1px solid rgba(125, 211, 252, 0.42) !important;
        color: #ffffff !important;
        box-shadow: 0 18px 48px rgba(37, 99, 235, 0.26) !important;
    }
    section[data-testid="stSidebar"] a {
        border-radius: 12px !important;
        transition: transform 180ms ease, background 180ms ease, border-color 180ms ease !important;
    }
    section[data-testid="stSidebar"] a:hover {
        transform: translateX(3px);
        background: rgba(37, 99, 235, 0.16) !important;
    }
    .result-grid {
        gap: 14px;
    }
    .result-card h3 {
        color: #bfdbfe;
    }
    .result-card p {
        color: #dbeafe;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 12% 10%, rgba(37, 99, 235, 0.26), transparent 30%),
            radial-gradient(circle at 84% 14%, rgba(20, 184, 166, 0.18), transparent 28%),
            linear-gradient(135deg, #070a12 0%, #0f172a 46%, #111827 100%);
        color: #f8fafc;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .main .block-container {
        max-width: 1160px;
        padding-top: 2.1rem;
        padding-bottom: 3.4rem;
    }
    section[data-testid="stSidebar"] {
        background: rgba(8, 13, 26, 0.94);
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }
    .hero-shell {
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 24px;
        padding: clamp(28px, 5vw, 56px);
        margin-bottom: 26px;
        background:
            linear-gradient(135deg, rgba(37, 99, 235, 0.30), rgba(20, 184, 166, 0.14) 44%, rgba(15, 23, 42, 0.82)),
            rgba(15, 23, 42, 0.72);
        box-shadow: 0 28px 90px rgba(0, 0, 0, 0.38);
    }
    .hero-kicker {
        width: fit-content;
        border: 1px solid rgba(45, 212, 191, 0.36);
        border-radius: 999px;
        padding: 7px 12px;
        margin-bottom: 18px;
        background: rgba(20, 184, 166, 0.12);
        color: #99f6e4;
        font-size: 0.86rem;
        font-weight: 700;
    }
    .hero-title {
        max-width: 780px;
        margin: 0;
        color: #f8fafc;
        font-size: clamp(2.4rem, 5vw, 4.8rem);
        line-height: 1.01;
        letter-spacing: 0;
        font-weight: 850;
    }
    .hero-copy {
        max-width: 680px;
        margin-top: 18px;
        color: #cbd5e1;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    .hero-metrics {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-top: 28px;
        max-width: 760px;
    }
    .metric {
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 14px;
        padding: 14px 16px;
        background: rgba(15, 23, 42, 0.58);
        backdrop-filter: blur(18px);
    }
    .metric strong {
        display: block;
        color: #f8fafc;
        font-size: 1.15rem;
        line-height: 1.2;
    }
    .metric span {
        display: block;
        margin-top: 4px;
        color: #94a3b8;
        font-size: 0.86rem;
    }
    div[data-testid="stTabs"] {
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 20px;
        padding: 18px;
        background: rgba(15, 23, 42, 0.66);
        box-shadow: 0 20px 70px rgba(0, 0, 0, 0.26);
        backdrop-filter: blur(18px);
    }
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 10px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.16);
        padding-bottom: 12px;
    }
    div[data-testid="stTabs"] [role="tab"] {
        min-height: 44px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 999px;
        padding: 0 18px;
        background: rgba(15, 23, 42, 0.76);
        color: #cbd5e1;
        font-weight: 760;
    }
    div[data-testid="stTabs"] [aria-selected="true"] {
        border-color: rgba(34, 211, 238, 0.72);
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.42), rgba(20, 184, 166, 0.24));
        color: #ffffff;
        box-shadow: 0 12px 34px rgba(37, 99, 235, 0.26);
    }
    div[data-testid="stFileUploaderDropzone"],
    textarea,
    input {
        border-radius: 16px !important;
        border: 1px solid rgba(148, 163, 184, 0.30) !important;
        background: rgba(8, 13, 26, 0.70) !important;
        color: #f8fafc !important;
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.22);
        backdrop-filter: blur(18px);
    }
    textarea:focus,
    input:focus {
        border-color: rgba(34, 211, 238, 0.78) !important;
        box-shadow: 0 0 0 4px rgba(34, 211, 238, 0.12), 0 18px 46px rgba(0, 0, 0, 0.26) !important;
    }
    textarea::placeholder,
    input::placeholder {
        color: #64748b !important;
    }
    .stAlert {
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: rgba(15, 23, 42, 0.72);
        color: #e5e7eb;
    }
    .stButton > button {
        min-height: 48px;
        border: 1px solid rgba(34, 211, 238, 0.46) !important;
        border-radius: 15px !important;
        background: linear-gradient(135deg, #2563eb 0%, #0891b2 100%) !important;
        color: #ffffff !important;
        font-weight: 850 !important;
        letter-spacing: 0;
        box-shadow: 0 18px 46px rgba(37, 99, 235, 0.28);
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(125, 211, 252, 0.86) !important;
        box-shadow: 0 24px 58px rgba(8, 145, 178, 0.34);
    }
    div[data-testid="stExpander"],
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(148, 163, 184, 0.18) !important;
        border-radius: 18px !important;
        background: rgba(15, 23, 42, 0.58) !important;
    }
    .section-title {
        margin: 28px 0 12px;
        color: #f8fafc;
        font-size: 1.35rem;
        font-weight: 850;
    }
    .legal-note {
        margin-top: 18px;
        color: #94a3b8;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    @media (max-width: 760px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .hero-metrics {
            grid-template-columns: 1fr;
        }
        div[data-testid="stTabs"] {
            padding: 12px;
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(18px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    @keyframes glowPulse {
        0%, 100% {
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.28), 0 0 46px rgba(37, 99, 235, 0.20);
        }
        50% {
            box-shadow: 0 0 28px rgba(56, 189, 248, 0.42), 0 0 68px rgba(37, 99, 235, 0.28);
        }
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background:
            linear-gradient(rgba(148, 163, 184, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.028) 1px, transparent 1px);
        background-size: 42px 42px;
        mask-image: radial-gradient(circle at 50% 18%, black, transparent 72%);
        z-index: 0;
    }
    .main .block-container {
        animation: fadeInUp 700ms ease both;
    }
    #MainMenu,
    footer,
    .stDeployButton {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 24% 10%, rgba(59, 130, 246, 0.28), transparent 34%),
            linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.96)) !important;
        border-right: 1px solid rgba(96, 165, 250, 0.24);
        box-shadow: 18px 0 70px rgba(0, 0, 0, 0.34);
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1.8rem;
    }
    .sidebar-brand {
        padding: 0 0.8rem 1.4rem;
        margin-bottom: 0.6rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.16);
    }
    .sidebar-logo {
        width: 50px;
        height: 50px;
        display: grid;
        place-items: center;
        border-radius: 16px;
        margin-bottom: 12px;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.92), rgba(34, 211, 238, 0.72));
        color: white;
        font-size: 1.75rem;
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.34);
    }
    .sidebar-title {
        color: #f8fafc;
        font-size: 1.02rem;
        font-weight: 850;
        line-height: 1.2;
        text-shadow: 0 0 18px rgba(125, 211, 252, 0.36);
    }
    .sidebar-subtitle {
        margin-top: 4px;
        color: #94a3b8;
        font-size: 0.78rem;
    }
    [data-testid="stSidebarNav"] {
        padding-top: 0.4rem;
    }
    [data-testid="stSidebarNav"] a {
        margin: 0.28rem 0.55rem;
        border: 1px solid transparent;
        border-radius: 14px;
        background: transparent;
        color: #dbeafe;
        transition: transform 180ms ease, background 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
    }
    [data-testid="stSidebarNav"] a:hover {
        transform: translateX(4px);
        border-color: rgba(96, 165, 250, 0.28);
        background: rgba(30, 64, 175, 0.26);
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.18);
    }
    [data-testid="stSidebarNav"] a[aria-current="page"],
    [data-testid="stSidebarNav"] a[aria-selected="true"] {
        border-color: rgba(125, 211, 252, 0.54);
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.76), rgba(14, 165, 233, 0.46));
        box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.16), 0 0 32px rgba(56, 189, 248, 0.34);
    }
    .hero-shell {
        text-align: center;
        border: 0;
        border-radius: 0;
        padding: 18px 24px 30px;
        margin: 0 auto 28px;
        background: transparent;
        box-shadow: none;
        animation: fadeInUp 760ms ease both;
    }
    .hero-logo {
        width: 88px;
        height: 88px;
        display: grid;
        place-items: center;
        margin: 0 auto 14px;
        border-radius: 28px;
        background:
            radial-gradient(circle at 35% 25%, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.10) 28%, transparent 52%),
            linear-gradient(135deg, rgba(29, 78, 216, 0.98), rgba(6, 182, 212, 0.88));
        color: #ffffff;
        font-size: 3.1rem;
        text-shadow: 0 0 18px rgba(255, 255, 255, 0.72);
        animation: glowPulse 3.2s ease-in-out infinite;
    }
    .hero-title {
        max-width: 980px;
        margin: 0 auto;
        font-size: clamp(3.3rem, 7vw, 6.4rem);
        line-height: 0.95;
        font-weight: 950;
        color: #ffffff;
        text-shadow:
            0 0 16px rgba(255, 255, 255, 0.50),
            0 0 42px rgba(56, 189, 248, 0.36),
            0 0 86px rgba(37, 99, 235, 0.26);
    }
    .hero-kicker {
        margin: 18px auto 0;
        padding: 10px 18px;
        border-color: rgba(56, 189, 248, 0.62);
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.46), rgba(8, 145, 178, 0.30));
        color: #e0f2fe;
        box-shadow: 0 0 26px rgba(56, 189, 248, 0.26), inset 0 1px 0 rgba(255, 255, 255, 0.16);
        backdrop-filter: blur(18px);
    }
    .hero-copy {
        margin: 20px auto 0;
        max-width: 780px;
        color: #e2e8f0;
        font-size: 1.06rem;
        font-weight: 650;
        text-shadow: 0 0 18px rgba(15, 23, 42, 0.86);
    }
    .hero-metrics {
        display: none;
    }
    div[data-testid="stTabs"] {
        max-width: 980px;
        margin: 0 auto;
        padding: 12px;
        border-radius: 22px;
        border-color: rgba(125, 211, 252, 0.25);
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.72), rgba(15, 23, 42, 0.46));
        box-shadow: 0 22px 90px rgba(0, 0, 0, 0.34), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    div[data-testid="stTabs"] [role="tablist"] {
        padding: 7px;
        gap: 8px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
        background: rgba(2, 6, 23, 0.36);
    }
    div[data-testid="stTabs"] [role="tab"] {
        min-height: 42px;
        border-radius: 999px;
        color: #dbeafe;
        transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
    }
    div[data-testid="stTabs"] [role="tab"]:hover {
        transform: translateY(-1px);
        background: rgba(37, 99, 235, 0.22);
        box-shadow: 0 12px 28px rgba(37, 99, 235, 0.18);
    }
    div[data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #06b6d4 100%);
        border-color: rgba(191, 219, 254, 0.78);
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.46), 0 12px 38px rgba(37, 99, 235, 0.34);
    }
    div[data-testid="stFileUploaderDropzone"] {
        min-height: 150px;
    }
    textarea {
        min-height: 260px !important;
        padding: 20px !important;
        background:
            radial-gradient(circle at 12% 8%, rgba(56, 189, 248, 0.12), transparent 32%),
            rgba(15, 23, 42, 0.64) !important;
        box-shadow:
            0 22px 70px rgba(0, 0, 0, 0.32),
            inset 0 0 38px rgba(56, 189, 248, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.10);
        transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
    }
    textarea:focus {
        transform: translateY(-1px);
        border-color: rgba(125, 211, 252, 0.86) !important;
        box-shadow:
            0 0 0 4px rgba(14, 165, 233, 0.13),
            0 0 46px rgba(56, 189, 248, 0.18),
            0 24px 76px rgba(0, 0, 0, 0.36),
            inset 0 0 44px rgba(56, 189, 248, 0.08) !important;
    }
    textarea::placeholder {
        color: #bfdbfe !important;
        font-weight: 650;
    }
    .stButton > button {
        border-radius: 999px !important;
        background: linear-gradient(135deg, #2563eb 0%, #06b6d4 52%, #38bdf8 100%) !important;
        box-shadow: 0 0 28px rgba(56, 189, 248, 0.26), 0 18px 50px rgba(37, 99, 235, 0.28);
    }
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.005);
        box-shadow: 0 0 42px rgba(56, 189, 248, 0.46), 0 24px 70px rgba(37, 99, 235, 0.38);
    }
    .stAlert {
        max-width: 980px;
        margin-left: auto;
        margin-right: auto;
        border-color: rgba(56, 189, 248, 0.24);
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.18), rgba(37, 99, 235, 0.18));
        box-shadow: 0 18px 46px rgba(0, 0, 0, 0.22);
    }
    .section-title {
        max-width: 980px;
        margin-left: auto;
        margin-right: auto;
        text-shadow: 0 0 22px rgba(56, 189, 248, 0.22);
    }
    .legal-note {
        max-width: 980px;
        margin-left: auto;
        margin-right: auto;
        padding: 16px 18px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 16px;
        background: rgba(15, 23, 42, 0.42);
        backdrop-filter: blur(18px);
    }
    /* Chatbot sayfasi ile ayni sakin premium dil */
    .stApp {
        background:
            radial-gradient(circle at 12% 8%, rgba(37, 99, 235, 0.18), transparent 28%),
            radial-gradient(circle at 88% 18%, rgba(20, 184, 166, 0.12), transparent 26%),
            #080b12;
        color: #eef2ff;
    }
    .stApp::before {
        display: none;
    }
    .main .block-container {
        max-width: 1120px;
        padding-top: 2.2rem;
        padding-bottom: 7.5rem;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.92) !important;
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
    .sidebar-brand,
    .hero-logo {
        display: none;
    }
    .hero-shell {
        text-align: left;
        border: 1px solid rgba(148, 163, 184, 0.22);
        background: rgba(15, 23, 42, 0.72);
        border-radius: 18px;
        padding: 22px 24px;
        box-shadow: 0 18px 55px rgba(0, 0, 0, 0.32);
        margin-bottom: 22px;
        animation: none;
    }
    .hero-title {
        max-width: none;
        font-size: clamp(2rem, 4vw, 3.3rem);
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: 0;
        margin: 0;
        color: #f8fafc;
        text-shadow: none;
    }
    .hero-copy {
        color: #94a3b8;
        font-size: 1rem;
        margin: 10px 0 0;
        max-width: 740px;
        line-height: 1.6;
        font-weight: 400;
        text-shadow: none;
    }
    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid rgba(45, 212, 191, 0.32);
        background: rgba(20, 184, 166, 0.10);
        color: #99f6e4;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 0.88rem;
        margin: 16px 0 0;
        box-shadow: none;
        backdrop-filter: none;
    }
    div[data-testid="stTabs"] {
        max-width: none;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 18px;
        background: rgba(15, 23, 42, 0.58);
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.18);
        backdrop-filter: none;
    }
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 10px;
        border: 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 0;
        padding: 0 0 12px;
        background: transparent;
    }
    div[data-testid="stTabs"] [role="tab"] {
        min-height: 42px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.76);
        color: #cbd5e1;
        font-weight: 760;
        transition: all 180ms ease;
    }
    div[data-testid="stTabs"] [role="tab"]:hover {
        transform: translateY(-1px);
        background: rgba(37, 99, 235, 0.16);
        box-shadow: 0 12px 28px rgba(37, 99, 235, 0.14);
    }
    div[data-testid="stTabs"] [aria-selected="true"] {
        border-color: rgba(34, 211, 238, 0.76);
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #ffffff;
        box-shadow: 0 18px 44px rgba(37, 99, 235, 0.22);
    }
    div[data-testid="stFileUploaderDropzone"],
    textarea,
    input {
        border-radius: 18px !important;
        border: 1px solid rgba(148, 163, 184, 0.32) !important;
        background: rgba(15, 23, 42, 0.88) !important;
        color: #f8fafc !important;
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.32);
        backdrop-filter: none;
    }
    textarea {
        min-height: 220px !important;
        padding: 16px 18px !important;
        transition: border-color 180ms ease, box-shadow 180ms ease;
    }
    textarea:focus,
    input:focus {
        transform: none;
        border-color: rgba(34, 211, 238, 0.76) !important;
        box-shadow: 0 0 0 4px rgba(34, 211, 238, 0.12), 0 18px 48px rgba(0, 0, 0, 0.34) !important;
    }
    textarea::placeholder,
    input::placeholder {
        color: #94a3b8 !important;
        font-weight: 500;
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
    .stDownloadButton > button {
        border-radius: 14px !important;
        border: 1px solid rgba(96, 165, 250, 0.28) !important;
        background: rgba(15, 23, 42, 0.84) !important;
        color: #f8fafc !important;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
        font-weight: 750 !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(34, 211, 238, 0.76) !important;
        box-shadow: 0 18px 44px rgba(37, 99, 235, 0.22);
    }
    .stAlert {
        max-width: none;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: rgba(15, 23, 42, 0.58);
        color: #cbd5e1;
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.18);
    }
    .section-title {
        max-width: none;
        margin: 24px 0 12px;
        font-size: 1.2rem;
        color: #f8fafc;
        text-shadow: none;
    }
    .legal-note {
        max-width: none;
        color: #94a3b8;
        border-radius: 18px;
        background: rgba(15, 23, 42, 0.58);
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.18);
    }
    /* Final premium SaaS dashboard pass */
    .stApp {
        background:
            radial-gradient(circle at 18% 4%, rgba(37, 99, 235, 0.22), transparent 30%),
            radial-gradient(circle at 84% 20%, rgba(20, 184, 166, 0.14), transparent 24%),
            linear-gradient(135deg, #050816 0%, #08111f 44%, #020617 100%);
        color: #eef2ff;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    #MainMenu,
    footer,
    .stDeployButton,
    [data-testid="stDecoration"] {
        display: none !important;
    }
    .main .block-container {
        max-width: 1180px;
        margin-top: 1.2rem;
        padding: clamp(1.2rem, 2vw, 2rem);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 26px;
        background:
            linear-gradient(180deg, rgba(15, 23, 42, 0.78), rgba(15, 23, 42, 0.48)),
            rgba(2, 6, 23, 0.46);
        box-shadow: 0 28px 95px rgba(0, 0, 0, 0.40), inset 0 1px 0 rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(22px);
    }
    section[data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 22% 8%, rgba(37, 99, 235, 0.22), transparent 34%),
            rgba(8, 13, 26, 0.94) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: 18px 0 55px rgba(0, 0, 0, 0.24);
    }
    .sidebar-brand {
        display: block;
        margin: 0.2rem 0.55rem 1.1rem;
        padding: 14px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
        background: rgba(15, 23, 42, 0.58);
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.22);
    }
    .sidebar-logo {
        display: grid;
        width: 42px;
        height: 42px;
        place-items: center;
        border-radius: 14px;
        margin-bottom: 10px;
        background: linear-gradient(135deg, #2563eb, #0891b2);
        box-shadow: 0 0 22px rgba(34, 211, 238, 0.22);
    }
    .sidebar-title {
        color: #f8fafc;
        font-size: 1rem;
        font-weight: 850;
    }
    .sidebar-subtitle {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 3px;
    }
    section[data-testid="stSidebar"] a {
        border-radius: 14px;
        border: 1px solid transparent;
        margin: 0.25rem 0.55rem;
        transition: transform 180ms ease, background 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
    }
    section[data-testid="stSidebar"] a:hover,
    section[data-testid="stSidebar"] a[aria-current="page"] {
        transform: translateX(3px);
        border-color: rgba(34, 211, 238, 0.38);
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.30), rgba(8, 145, 178, 0.16));
        box-shadow: 0 12px 34px rgba(37, 99, 235, 0.18);
    }
    .hero-shell {
        position: relative;
        overflow: hidden;
        text-align: left;
        border: 1px solid rgba(125, 211, 252, 0.20);
        border-radius: 24px;
        padding: clamp(26px, 4vw, 46px);
        margin-bottom: 26px;
        background:
            radial-gradient(circle at 88% 10%, rgba(56, 189, 248, 0.18), transparent 28%),
            linear-gradient(135deg, rgba(37, 99, 235, 0.24), rgba(20, 184, 166, 0.10) 44%, rgba(15, 23, 42, 0.88));
        box-shadow: 0 22px 70px rgba(0, 0, 0, 0.34);
    }
    .hero-shell::after {
        content: "";
        position: absolute;
        inset: auto 28px 0 28px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.60), transparent);
    }
    .hero-logo {
        display: none;
    }
    .hero-title {
        max-width: 860px;
        margin: 0;
        color: #f8fafc;
        font-size: clamp(2.6rem, 5vw, 5rem);
        line-height: 1;
        letter-spacing: 0;
        font-weight: 900;
        text-shadow: 0 0 32px rgba(56, 189, 248, 0.18);
    }
    .hero-copy {
        max-width: 760px;
        margin-top: 14px;
        color: rgba(203, 213, 225, 0.86);
        font-size: 1.04rem;
        line-height: 1.7;
    }
    .hero-kicker {
        display: inline-flex;
        align-items: center;
        border: 1px solid rgba(45, 212, 191, 0.34);
        border-radius: 999px;
        padding: 8px 13px;
        margin-top: 18px;
        color: #99f6e4;
        background: rgba(20, 184, 166, 0.10);
    }
    div[data-testid="stTabs"] {
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 22px;
        padding: 18px;
        background: rgba(15, 23, 42, 0.58);
        box-shadow: 0 18px 55px rgba(0, 0, 0, 0.24);
        backdrop-filter: blur(18px);
    }
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 10px;
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 999px;
        padding: 7px;
        background: rgba(2, 6, 23, 0.40);
        margin-bottom: 14px;
    }
    div[data-testid="stTabs"] [role="tab"] {
        min-height: 42px;
        border: 1px solid transparent;
        border-radius: 999px;
        padding: 0 18px;
        background: transparent;
        color: #cbd5e1;
        font-weight: 760;
        transition: transform 180ms ease, background 180ms ease, box-shadow 180ms ease;
    }
    div[data-testid="stTabs"] [role="tab"]:hover {
        transform: translateY(-1px);
        background: rgba(37, 99, 235, 0.18);
    }
    div[data-testid="stTabs"] [aria-selected="true"] {
        border-color: rgba(125, 211, 252, 0.58);
        background: linear-gradient(135deg, #2563eb, #0891b2);
        color: #ffffff;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.30), 0 0 24px rgba(34, 211, 238, 0.18);
    }
    div[data-testid="stFileUploaderDropzone"] {
        min-height: 172px;
        border-style: dashed !important;
        border-width: 1.5px !important;
        border-color: rgba(125, 211, 252, 0.38) !important;
        background:
            radial-gradient(circle at 12% 12%, rgba(56, 189, 248, 0.12), transparent 32%),
            rgba(15, 23, 42, 0.70) !important;
        transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        transform: translateY(-2px);
        border-color: rgba(34, 211, 238, 0.70) !important;
        box-shadow: 0 0 0 4px rgba(34, 211, 238, 0.08), 0 18px 52px rgba(37, 99, 235, 0.18);
        background: rgba(15, 23, 42, 0.88) !important;
    }
    textarea,
    input {
        border-radius: 18px !important;
        border: 1px solid rgba(148, 163, 184, 0.30) !important;
        background: rgba(15, 23, 42, 0.78) !important;
        color: #f8fafc !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 14px 38px rgba(0, 0, 0, 0.24);
        backdrop-filter: blur(18px);
    }
    textarea {
        min-height: 260px !important;
        padding: 18px !important;
    }
    textarea:focus,
    input:focus {
        border-color: rgba(34, 211, 238, 0.76) !important;
        box-shadow: 0 0 0 4px rgba(34, 211, 238, 0.12), 0 18px 48px rgba(0, 0, 0, 0.34) !important;
    }
    textarea::placeholder,
    input::placeholder {
        color: rgba(191, 219, 254, 0.70) !important;
    }
    .stButton > button {
        min-height: 54px;
        border: 1px solid rgba(125, 211, 252, 0.42) !important;
        border-radius: 16px !important;
        background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
        color: #ffffff !important;
        font-weight: 850 !important;
        box-shadow: 0 18px 48px rgba(37, 99, 235, 0.28), 0 0 28px rgba(34, 211, 238, 0.12);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 24px 64px rgba(37, 99, 235, 0.36), 0 0 36px rgba(34, 211, 238, 0.24);
    }
    .stDownloadButton > button {
        min-height: 48px;
        border-radius: 16px !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        background: rgba(15, 23, 42, 0.84) !important;
        color: #f8fafc !important;
    }
    .result-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin: 16px 0;
    }
    .result-card {
        display: grid;
        grid-template-columns: 42px 1fr;
        gap: 14px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 16px;
        background: rgba(15, 23, 42, 0.66);
        box-shadow: 0 16px 42px rgba(0, 0, 0, 0.22);
    }
    .result-card-icon {
        width: 42px;
        height: 42px;
        display: grid;
        place-items: center;
        border-radius: 14px;
        background: rgba(37, 99, 235, 0.18);
        border: 1px solid rgba(96, 165, 250, 0.22);
    }
    .result-card h3 {
        margin: 0 0 8px;
        color: #bfdbfe;
        font-size: 1rem;
    }
    .result-card p {
        margin: 0 0 6px;
        color: #dbeafe;
        line-height: 1.55;
        font-size: 0.94rem;
    }
    .upload-note {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 4px 0 12px;
        padding: 14px 16px;
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 16px;
        background: rgba(2, 6, 23, 0.28);
        color: #cbd5e1;
    }
    .upload-note-icon {
        width: 40px;
        height: 40px;
        display: grid;
        place-items: center;
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.42), rgba(8, 145, 178, 0.28));
        border: 1px solid rgba(125, 211, 252, 0.22);
    }
    .upload-note strong {
        display: block;
        color: #f8fafc;
        margin-bottom: 2px;
    }
    .text-transfer-success {
        display: none;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
        padding: 9px 12px;
        border: 1px solid rgba(34, 197, 94, 0.34);
        border-radius: 999px;
        background: rgba(22, 163, 74, 0.12);
        color: #bbf7d0;
        font-size: 0.92rem;
        font-weight: 750;
        box-shadow: 0 0 28px rgba(34, 197, 94, 0.12);
        animation: successFadeIn 360ms ease both;
    }
    @keyframes successFadeIn {
        from {
            opacity: 0;
            transform: translateY(6px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .stTextArea textarea {
        transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease, transform 180ms ease !important;
    }
    .stTextArea textarea:hover {
        border-color: rgba(125, 211, 252, 0.48) !important;
        box-shadow: 0 16px 42px rgba(0, 0, 0, 0.26), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
    }
    .stTextArea textarea:focus {
        transform: translateY(-1px);
        border-color: rgba(56, 189, 248, 0.86) !important;
        box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.13), 0 20px 52px rgba(0, 0, 0, 0.34) !important;
    }
    .sidebar-brand {
        display: flex !important;
        justify-content: center;
        align-items: center;
        width: 46px;
        height: 46px;
        margin: 0.6rem auto 1.1rem;
        padding: 0 !important;
        border: 1px solid rgba(125, 211, 252, 0.24);
        border-radius: 16px;
        background: rgba(15, 23, 42, 0.62);
        box-shadow: 0 12px 32px rgba(37, 99, 235, 0.16);
    }
    .sidebar-logo {
        display: grid !important;
        place-items: center;
        width: 34px !important;
        height: 34px !important;
        margin: 0 !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, #2563eb, #0891b2) !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.18) !important;
    }
    .sidebar-title,
    .sidebar-subtitle {
        display: none !important;
    }
    .sidebar-menu-group {
        margin: 0 0.45rem;
        padding: 0.45rem 0;
        border-top: 1px solid rgba(148, 163, 184, 0.12);
        border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    }
    .sidebar-menu-label {
        margin: 0 0.9rem 0.35rem;
        color: #64748b;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .stButton > button:has(div),
    .stButton > button {
        position: relative;
    }
    /* Softer professional pass: reduce neon/glow intensity without changing layout. */
    .stApp {
        background:
            radial-gradient(circle at 16% 7%, rgba(37, 99, 235, 0.10), transparent 30%),
            radial-gradient(circle at 88% 18%, rgba(20, 184, 166, 0.055), transparent 26%),
            linear-gradient(135deg, #070b14 0%, #0a1020 48%, #050814 100%) !important;
    }
    .main .block-container {
        box-shadow: 0 18px 58px rgba(0, 0, 0, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.035) !important;
    }
    .hero-shell,
    div[data-testid="stTabs"],
    .result-card,
    .legal-note,
    div[data-testid="stExpander"],
    div[data-testid="stVerticalBlockBorderWrapper"],
    .upload-note {
        border-color: rgba(148, 163, 184, 0.135) !important;
        background: rgba(15, 23, 42, 0.58) !important;
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.24) !important;
    }
    .hero-shell {
        background:
            radial-gradient(circle at 88% 12%, rgba(56, 189, 248, 0.075), transparent 30%),
            rgba(15, 23, 42, 0.60) !important;
    }
    .hero-title {
        text-shadow: 0 0 18px rgba(56, 189, 248, 0.08) !important;
    }
    .hero-kicker,
    .status-pill {
        border-color: rgba(45, 212, 191, 0.22) !important;
        background: rgba(20, 184, 166, 0.07) !important;
        box-shadow: none !important;
    }
    div[data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.86), rgba(8, 145, 178, 0.76)) !important;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.16) !important;
        border-color: rgba(125, 211, 252, 0.34) !important;
    }
    div[data-testid="stTabs"] [role="tab"]:hover {
        background: rgba(37, 99, 235, 0.10) !important;
        box-shadow: none !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        border-color: rgba(125, 211, 252, 0.24) !important;
        background: rgba(15, 23, 42, 0.60) !important;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18) !important;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: rgba(56, 189, 248, 0.42) !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.045), 0 14px 34px rgba(0, 0, 0, 0.22) !important;
    }
    textarea,
    input {
        border-color: rgba(148, 163, 184, 0.22) !important;
        background: rgba(15, 23, 42, 0.66) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035), 0 10px 28px rgba(0, 0, 0, 0.18) !important;
    }
    textarea:focus,
    input:focus,
    .stTextArea textarea:focus {
        border-color: rgba(56, 189, 248, 0.48) !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.075), 0 12px 32px rgba(0, 0, 0, 0.22) !important;
    }
    .stTextArea textarea:hover {
        border-color: rgba(125, 211, 252, 0.30) !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.20), inset 0 1px 0 rgba(255, 255, 255, 0.035) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1d4ed8, #0891b2) !important;
        border-color: rgba(125, 211, 252, 0.26) !important;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.16) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 16px 36px rgba(37, 99, 235, 0.20) !important;
    }
    .stDownloadButton > button {
        box-shadow: 0 10px 26px rgba(0, 0, 0, 0.18) !important;
    }
    .sidebar-brand,
    .sidebar-logo {
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.10) !important;
    }
    section[data-testid="stSidebar"] a:hover {
        background: rgba(37, 99, 235, 0.10) !important;
        box-shadow: none !important;
    }
    .result-card-icon,
    .upload-note-icon {
        background: rgba(37, 99, 235, 0.12) !important;
        border-color: rgba(96, 165, 250, 0.16) !important;
        box-shadow: none !important;
    }
    .element-container:has(.metin-success-style) + div .stButton > button {
        background: linear-gradient(135deg, #15803d, #16a34a) !important;
        border-color: rgba(134, 239, 172, 0.30) !important;
        box-shadow: 0 12px 30px rgba(22, 163, 74, 0.14) !important;
    }
    @media (max-width: 760px) {
        .main .block-container {
            margin-top: 0;
            border-radius: 0;
        }
        .result-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero-shell">
        <div class="hero-content">
            <h1 class="hero-title">Sözleşme Rehberim</h1>
            <div class="hero-kicker">✨ AI Destekli Sözleşme Analizi</div>
            <p class="hero-copy">
                Uzun hukuki sözleşmeleri saniyeler içinde analiz edin ve gizli riskleri öğrenin.
            </p>
            <div class="hero-feature-row">
                <span class="hero-feature-chip">⚖️ KVKK Analizi</span>
                <span class="hero-feature-chip">🛡️ Risk Analizi</span>
                <span class="hero-feature-chip">📄 PDF & DOCX Desteği</span>
            </div>
        </div>
        <div class="hero-visual" aria-hidden="true">
            <div class="hero-scale-mark">⚖️</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* Home layout alignment: reference-style SaaS dashboard cards. */
    .main .block-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding-top: clamp(3rem, 6vh, 5.2rem) !important;
        padding-bottom: 4.5rem !important;
        border: 0 !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }
    .hero-shell {
        max-width: 1180px !important;
        min-height: 330px;
        position: relative;
        display: grid;
        grid-template-columns: minmax(0, 1.12fr) minmax(240px, 330px);
        align-items: center;
        gap: clamp(1.5rem, 4vw, 3.5rem);
        margin: 0 auto 42px !important;
        padding: clamp(2.4rem, 5vw, 4.3rem) clamp(2.2rem, 5vw, 4.6rem) !important;
        border: 1px solid rgba(148, 163, 184, 0.16) !important;
        border-radius: 22px !important;
        background:
            radial-gradient(circle at 82% 48%, rgba(56, 189, 248, 0.12), transparent 30%),
            radial-gradient(circle at 18% 0%, rgba(37, 99, 235, 0.12), transparent 34%),
            linear-gradient(135deg, rgba(15, 23, 42, 0.78), rgba(8, 13, 26, 0.66)) !important;
        box-shadow: 0 22px 62px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.045) !important;
        overflow: hidden;
    }
    .hero-content {
        position: relative;
        z-index: 2;
    }
    .hero-title {
        max-width: 880px !important;
        font-size: clamp(2.85rem, 5.1vw, 4.75rem) !important;
        line-height: 0.98 !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
        color: #f8fafc !important;
        text-shadow: 0 8px 34px rgba(37, 99, 235, 0.10) !important;
    }
    .hero-kicker {
        order: 2;
        width: fit-content !important;
        margin: 28px 0 0 !important;
        padding: 9px 15px !important;
        border-radius: 999px !important;
        border: 1px solid rgba(45, 212, 191, 0.22) !important;
        background: rgba(20, 184, 166, 0.08) !important;
        color: #99f6e4 !important;
        font-weight: 800 !important;
        box-shadow: none !important;
    }
    .hero-copy {
        order: 3;
        max-width: 650px !important;
        margin: 18px 0 0 !important;
        color: rgba(203, 213, 225, 0.82) !important;
        font-size: 1.08rem !important;
        line-height: 1.7 !important;
    }
    .hero-feature-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 22px;
    }
    .hero-feature-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        min-height: 36px;
        padding: 8px 12px;
        border: 1px solid rgba(125, 211, 252, 0.18);
        border-radius: 999px;
        background:
            linear-gradient(135deg, rgba(14, 165, 233, 0.085), rgba(37, 99, 235, 0.05)),
            rgba(15, 23, 42, 0.42);
        color: rgba(219, 234, 254, 0.92);
        font-size: 0.88rem;
        font-weight: 720;
        line-height: 1.25;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 8px 20px rgba(2, 6, 23, 0.14);
        transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
    }
    .hero-feature-chip:hover {
        transform: translateY(-2px);
        border-color: rgba(125, 211, 252, 0.38);
        background:
            linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(37, 99, 235, 0.07)),
            rgba(15, 23, 42, 0.50);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.045), 0 10px 24px rgba(2, 6, 23, 0.16), 0 0 18px rgba(34, 211, 238, 0.075);
    }
    .hero-visual {
        position: relative;
        z-index: 1;
        min-height: 230px;
        display: grid;
        place-items: center;
        opacity: 0.62;
    }
    .hero-visual::before {
        content: "";
        position: absolute;
        width: min(320px, 32vw);
        aspect-ratio: 1;
        border-radius: 999px;
        background:
            radial-gradient(circle, rgba(56, 189, 248, 0.14), rgba(37, 99, 235, 0.055) 42%, transparent 68%);
        filter: blur(18px);
    }
    .hero-scale-mark {
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
        color: rgba(191, 219, 254, 0.26);
        font-size: clamp(7rem, 14vw, 10rem);
        line-height: 1;
        text-shadow: 0 0 28px rgba(56, 189, 248, 0.15);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03), 0 0 34px rgba(37, 99, 235, 0.055);
    }
    .hero-scale-mark::after {
        content: "";
        position: absolute;
        inset: 16%;
        border-radius: 999px;
        border: 1px solid rgba(125, 211, 252, 0.08);
    }
    div[data-testid="stTabs"] {
        max-width: 1120px !important;
        margin: 0 auto 28px !important;
        padding: 26px 28px 30px !important;
        border: 1px solid rgba(148, 163, 184, 0.15) !important;
        border-radius: 22px !important;
        background:
            linear-gradient(180deg, rgba(15, 23, 42, 0.70), rgba(8, 13, 26, 0.58)) !important;
        box-shadow: 0 22px 62px rgba(0, 0, 0, 0.24) !important;
        backdrop-filter: blur(18px) !important;
    }
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 18px !important;
        border: 0 !important;
        border-bottom: 1px solid rgba(148, 163, 184, 0.12) !important;
        border-radius: 0 !important;
        padding: 0 0 13px !important;
        margin-bottom: 24px !important;
        background: transparent !important;
        overflow: hidden !important;
    }
    div[data-testid="stTabs"] [role="tablist"] button::after,
    div[data-testid="stTabs"] [role="tab"]::after {
        background: linear-gradient(90deg, #60a5fa, #22d3ee) !important;
        height: 2px !important;
        border-radius: 999px !important;
        max-height: 2px !important;
    }
    div[data-testid="stTabs"] [role="tab"] {
        min-height: 46px !important;
        padding: 0 20px !important;
        border-radius: 11px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: #cbd5e1 !important;
        font-weight: 780 !important;
        transition: color 180ms ease, background 180ms ease, box-shadow 180ms ease, transform 180ms ease !important;
    }
    div[data-testid="stTabs"] [role="tab"]:hover {
        color: #bfdbfe !important;
        background: rgba(37, 99, 235, 0.10) !important;
        transform: translateY(-1px);
    }
    div[data-testid="stTabs"] [aria-selected="true"] {
        border-color: rgba(125, 211, 252, 0.20) !important;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.45), rgba(91, 33, 182, 0.22)) !important;
        box-shadow: 0 10px 26px rgba(37, 99, 235, 0.14) !important;
        color: #eff6ff !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        min-height: 315px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        position: relative;
        border: 1.5px dashed rgba(148, 163, 184, 0.34) !important;
        border-radius: 20px !important;
        background:
            radial-gradient(circle at 50% 24%, rgba(96, 165, 250, 0.10), transparent 26%),
            linear-gradient(180deg, rgba(15, 23, 42, 0.58), rgba(8, 13, 26, 0.46)) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 16px 46px rgba(0, 0, 0, 0.18) !important;
        backdrop-filter: blur(18px);
        transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease, transform 180ms ease !important;
        cursor: pointer;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        transform: translateY(-1px);
        border-color: rgba(96, 165, 250, 0.52) !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.055), 0 18px 52px rgba(0, 0, 0, 0.22) !important;
    }
    div[data-testid="stFileUploaderDropzone"] > div {
        width: 100%;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 12px !important;
        text-align: center !important;
    }
    div[data-testid="stFileUploader"] > label,
    div[data-testid="stFileUploaderDropzoneInstructions"],
    div[data-testid="stFileUploaderDropzone"] small,
    div[data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] {
        display: none !important;
    }
    div[data-testid="stFileUploaderDropzone"]::before {
        content: "☁";
        width: 66px;
        height: 66px;
        display: grid;
        place-items: center;
        margin-bottom: 16px;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        border: 1px solid rgba(125, 211, 252, 0.20);
        color: #7aa2ff;
        font-size: 2.1rem;
        line-height: 1;
    }
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "PDF, Word (.docx) veya TXT formatında yükleyebilirsiniz.\\A Dosyayı buraya sürükleyip bırakın veya seçmek için tıklayın.";
        position: absolute;
        left: 24px;
        right: 24px;
        top: calc(50% + 28px);
        color: #e5e7eb;
        font-size: 1.04rem;
        font-weight: 760;
        line-height: 1.85;
        text-align: center;
        white-space: pre-line;
        pointer-events: none;
    }
    div[data-testid="stFileUploaderDropzone"] button {
        position: absolute;
        left: 50%;
        bottom: 44px;
        transform: translateX(-50%);
        border-radius: 999px !important;
        border: 1px solid rgba(148, 163, 184, 0.20) !important;
        background: rgba(15, 23, 42, 0.72) !important;
        color: #e5e7eb !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18) !important;
        padding: 0.5rem 1.05rem !important;
        z-index: 2;
    }
    div[data-testid="stFileUploaderDropzone"] button:hover {
        border-color: rgba(125, 211, 252, 0.34) !important;
        background: rgba(30, 41, 59, 0.78) !important;
    }
    .upload-note {
        flex-direction: column !important;
        justify-content: center !important;
        text-align: center !important;
        gap: 12px !important;
        max-width: 760px !important;
        margin: 0 auto 18px !important;
        padding: 6px 16px 10px !important;
        border: 0 !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    .upload-note-icon {
        width: 64px !important;
        height: 64px !important;
        margin: 0 auto 4px;
        border-radius: 999px !important;
        background: rgba(37, 99, 235, 0.12) !important;
        border: 1px solid rgba(125, 211, 252, 0.20) !important;
        color: #7aa2ff;
        font-size: 2rem;
    }
    .upload-note strong {
        font-size: 1.05rem;
        color: #e5e7eb !important;
    }
    .upload-note small {
        display: block;
        margin-top: 8px;
        color: #94a3b8;
        font-size: 0.92rem;
    }
    textarea {
        min-height: 280px !important;
        border-radius: 18px !important;
        background: rgba(15, 23, 42, 0.58) !important;
    }
    .section-title,
    .stAlert,
    .result-grid,
    .legal-note,
    .stDownloadButton,
    div[data-testid="stExpander"] {
        max-width: 1120px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    @media (max-width: 900px) {
        .main .block-container {
            padding-top: 2rem !important;
        }
        .hero-shell {
            min-height: auto;
            grid-template-columns: 1fr;
            gap: 1.4rem;
            margin-bottom: 26px !important;
        }
        .hero-visual {
            min-height: 130px;
            opacity: 0.34;
            margin-top: -0.4rem;
        }
        .hero-scale-mark {
            width: min(190px, 58vw);
            font-size: clamp(5.2rem, 24vw, 7rem);
        }
        div[data-testid="stTabs"] {
            padding: 18px !important;
        }
    }
    /* Single-card uploader: hide Streamlit's compact row and make the real uploader cover the full card. */
    div[data-testid="stFileUploader"] {
        position: relative !important;
        width: 100% !important;
        min-height: 320px !important;
    }
    div[data-testid="stFileUploader"] > label {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        position: relative !important;
        width: 100% !important;
        min-height: 320px !important;
        height: 320px !important;
        overflow: hidden !important;
        display: grid !important;
        place-items: center !important;
        border: 1.5px dashed rgba(148, 163, 184, 0.34) !important;
        border-radius: 22px !important;
        background:
            radial-gradient(circle at 50% 26%, rgba(96, 165, 250, 0.11), transparent 28%),
            linear-gradient(180deg, rgba(15, 23, 42, 0.62), rgba(8, 13, 26, 0.50)) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 16px 46px rgba(0, 0, 0, 0.18) !important;
        backdrop-filter: blur(18px) !important;
        cursor: pointer !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: rgba(96, 165, 250, 0.52) !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.055), 0 18px 52px rgba(0, 0, 0, 0.22) !important;
    }
    [data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"],
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] svg,
    [data-testid="stFileUploaderDropzone"] p {
        visibility: hidden !important;
    }
    [data-testid="stFileUploaderDropzone"]::before {
        content: "☁";
        position: absolute;
        top: 70px;
        left: 50%;
        transform: translateX(-50%);
        width: 66px;
        height: 66px;
        display: grid;
        place-items: center;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        border: 1px solid rgba(125, 211, 252, 0.20);
        color: #7aa2ff;
        font-size: 2.1rem;
        line-height: 1;
        pointer-events: none;
        z-index: 2;
    }
    [data-testid="stFileUploaderDropzone"]::after {
        content: "PDF, Word (.docx) veya TXT formatında yükleyebilirsiniz.\\A Dosyayı buraya sürükleyip bırakın veya seçmek için tıklayın.";
        position: absolute;
        top: 150px;
        left: 24px;
        right: 24px;
        color: #e5e7eb;
        font-size: 1.05rem;
        font-weight: 760;
        line-height: 1.85;
        text-align: center;
        white-space: pre-line;
        pointer-events: none;
        z-index: 2;
    }
    [data-testid="stFileUploaderDropzone"] > div {
        position: static !important;
        width: 100% !important;
        height: 100% !important;
        display: block !important;
    }
    [data-testid="stFileUploaderDropzone"] > div::after {
        content: "Dosya Seç";
        position: absolute;
        left: 50%;
        bottom: 48px;
        transform: translateX(-50%);
        padding: 0.58rem 1.15rem;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        background: rgba(15, 23, 42, 0.78);
        color: #e5e7eb;
        font-weight: 760;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
        pointer-events: none;
        z-index: 2;
    }
    [data-testid="stFileUploaderDropzone"] button {
        position: absolute !important;
        inset: 0 !important;
        width: 100% !important;
        height: 100% !important;
        min-height: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        border-radius: 22px !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 5 !important;
    }
    .uploaded-file-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        margin-top: 14px;
        padding: 12px 14px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 16px;
        background: rgba(15, 23, 42, 0.58);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
    }
    .uploaded-file-meta {
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
        color: #dbeafe;
        font-weight: 760;
    }
    .uploaded-file-icon {
        width: 34px;
        height: 34px;
        display: grid;
        place-items: center;
        flex: 0 0 auto;
        border-radius: 11px;
        background: rgba(37, 99, 235, 0.14);
        border: 1px solid rgba(125, 211, 252, 0.16);
    }
    .uploaded-file-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .analysis-full-card {
        margin-top: 14px;
        padding: 22px 24px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
        background:
            linear-gradient(180deg, rgba(15, 23, 42, 0.72), rgba(8, 13, 26, 0.58));
        color: #dbeafe;
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.04);
        line-height: 1.72;
        font-size: 0.98rem;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }
    .paste-card-anchor,
    .paste-button-anchor,
    .link-card-anchor,
    .link-button-anchor {
        display: none;
    }
    .paste-glass-card {
        position: relative;
        margin: 0 0 2px;
        padding: 4px 0 2px;
    }
    .paste-glass-card::after {
        content: none;
    }
    .paste-info-compact {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        width: fit-content;
        max-width: 100%;
        min-height: 36px;
        margin-bottom: 9px;
        padding: 7px 10px;
        border: 1px solid rgba(125, 211, 252, 0.20);
        border-radius: 999px;
        background:
            linear-gradient(135deg, rgba(14, 165, 233, 0.09), rgba(37, 99, 235, 0.045)),
            rgba(15, 23, 42, 0.36);
        color: rgba(207, 232, 255, 0.90);
        font-size: 0.94rem;
        font-weight: 730;
        line-height: 1.35;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 8px 18px rgba(2, 6, 23, 0.10);
    }
    .paste-info-dot {
        width: 20px;
        height: 20px;
        display: grid;
        place-items: center;
        border-radius: 999px;
        border: 1px solid rgba(125, 211, 252, 0.24);
        background: rgba(56, 189, 248, 0.095);
        color: rgba(147, 231, 255, 0.88);
        font-size: 0.78rem;
        font-weight: 850;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.16);
        flex: 0 0 auto;
    }
    .paste-counter {
        margin: 3px 3px 7px auto;
        color: rgba(147, 169, 199, 0.66);
        font-size: 0.72rem;
        font-weight: 640;
        text-align: right;
        letter-spacing: 0;
    }
    .element-container:has(.paste-card-anchor) ~ div .stTextArea label {
        display: inline-flex !important;
        align-items: center !important;
        gap: 7px !important;
        width: fit-content !important;
        margin: 0 0 7px !important;
        padding: 0 !important;
        color: rgba(191, 219, 254, 0.76) !important;
        font-size: 0.76rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.055em !important;
        text-transform: uppercase !important;
    }
    .element-container:has(.paste-card-anchor) ~ div .stTextArea label::before {
        content: "✦";
        width: 19px;
        height: 19px;
        display: inline-grid;
        place-items: center;
        border-radius: 7px;
        border: 1px solid rgba(125, 211, 252, 0.20);
        background: rgba(56, 189, 248, 0.085);
        color: rgba(147, 231, 255, 0.88);
        font-size: 0.67rem;
        line-height: 1;
    }
    .element-container:has(.paste-card-anchor) ~ div .stTextArea textarea {
        height: 252px !important;
        min-height: 252px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(103, 232, 249, 0.28) !important;
        background:
            linear-gradient(180deg, rgba(8, 18, 38, 0.90), rgba(10, 24, 50, 0.80)) !important;
        color: #f8fafc !important;
        box-shadow:
            inset 0 2px 9px rgba(0, 0, 0, 0.26),
            inset 0 1px 0 rgba(255, 255, 255, 0.045),
            0 12px 30px rgba(0, 0, 0, 0.18) !important;
        line-height: 1.68 !important;
        padding: 17px 18px !important;
        font-size: 0.98rem !important;
        caret-color: #67e8f9 !important;
        transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
    }
    .element-container:has(.paste-card-anchor) ~ div .stTextArea textarea::placeholder {
        color: rgba(191, 219, 254, 0.58) !important;
        font-weight: 520 !important;
    }
    .element-container:has(.paste-card-anchor) ~ div .stTextArea textarea:hover {
        border-color: rgba(125, 211, 252, 0.36) !important;
        box-shadow:
            inset 0 2px 10px rgba(0, 0, 0, 0.26),
            inset 0 1px 0 rgba(255, 255, 255, 0.05),
            0 14px 34px rgba(0, 0, 0, 0.22) !important;
    }
    .element-container:has(.paste-card-anchor) ~ div .stTextArea textarea:focus {
        border-color: rgba(103, 232, 249, 0.64) !important;
        box-shadow:
            0 0 0 3px rgba(34, 211, 238, 0.085),
            0 0 24px rgba(34, 211, 238, 0.09),
            inset 0 2px 10px rgba(0, 0, 0, 0.28),
            0 15px 38px rgba(0, 0, 0, 0.24) !important;
        outline: none !important;
    }
    .element-container:has(.paste-button-anchor) + div .stButton > button {
        width: min(100%, 224px) !important;
        min-height: 42px !important;
        padding: 0.45rem 0.95rem !important;
        border-radius: 13px !important;
        border: 1px solid rgba(125, 211, 252, 0.34) !important;
        background: linear-gradient(135deg, #2563eb 0%, #0891b2 100%) !important;
        color: #f8fafc !important;
        font-weight: 800 !important;
        box-shadow: 0 11px 24px rgba(37, 99, 235, 0.19), 0 0 0 rgba(34, 211, 238, 0) !important;
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, filter 180ms ease !important;
    }
    .element-container:has(.paste-button-anchor) + div .stButton {
        display: flex !important;
        justify-content: flex-end !important;
        margin-top: 0 !important;
    }
    .element-container:has(.paste-button-anchor) + div .stButton > button:hover {
        transform: translateY(-1px) !important;
        border-color: rgba(165, 243, 252, 0.52) !important;
        filter: saturate(1.04) brightness(1.03);
        box-shadow: 0 14px 28px rgba(37, 99, 235, 0.23), 0 0 18px rgba(34, 211, 238, 0.09) !important;
    }
    .element-container:has(.paste-button-success) + div .stButton > button {
        background: linear-gradient(135deg, #16a34a, #22c55e) !important;
        border-color: rgba(134, 239, 172, 0.55) !important;
        color: #f0fdf4 !important;
        box-shadow: 0 0 18px rgba(34, 197, 94, 0.20), 0 12px 28px rgba(22, 163, 74, 0.18) !important;
    }
    .link-glass-card {
        position: relative;
        margin: 0 0 2px;
        padding: 4px 0 2px;
    }
    .link-glass-card::after {
        content: none;
    }
    .link-info-compact {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        width: fit-content;
        max-width: 100%;
        min-height: 36px;
        margin-bottom: 9px;
        padding: 7px 10px;
        border: 1px solid rgba(125, 211, 252, 0.20);
        border-radius: 999px;
        background:
            linear-gradient(135deg, rgba(14, 165, 233, 0.09), rgba(37, 99, 235, 0.045)),
            rgba(15, 23, 42, 0.36);
        color: rgba(207, 232, 255, 0.90);
        font-size: 0.92rem;
        font-weight: 710;
        line-height: 1.35;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 8px 18px rgba(2, 6, 23, 0.10);
    }
    .link-info-icon {
        width: 20px;
        height: 20px;
        display: grid;
        place-items: center;
        border-radius: 999px;
        border: 1px solid rgba(125, 211, 252, 0.24);
        background: rgba(56, 189, 248, 0.095);
        color: rgba(147, 231, 255, 0.88);
        font-size: 0.78rem;
        font-weight: 850;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.16);
        flex: 0 0 auto;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput label {
        display: inline-flex !important;
        align-items: center !important;
        gap: 7px !important;
        width: fit-content !important;
        margin: 0 0 7px !important;
        padding: 0 !important;
        color: rgba(191, 219, 254, 0.76) !important;
        font-size: 0.76rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.055em !important;
        text-transform: uppercase !important;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput label::before {
        content: "↗";
        width: 19px;
        height: 19px;
        display: inline-grid;
        place-items: center;
        border-radius: 7px;
        border: 1px solid rgba(125, 211, 252, 0.20);
        background: rgba(56, 189, 248, 0.085);
        color: rgba(147, 231, 255, 0.88);
        font-size: 0.72rem;
        line-height: 1;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput > div {
        position: relative !important;
        width: 100% !important;
        overflow: visible !important;
        border-radius: 20px !important;
        padding: 2px !important;
        border: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput,
    .element-container:has(.link-card-anchor) ~ div .stTextInput div,
    .element-container:has(.link-card-anchor) ~ div .stTextInput div::after {
        border-color: transparent !important;
        border-bottom-color: transparent !important;
        box-shadow: none !important;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput div::after {
        content: none !important;
        display: none !important;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput > div::before {
        content: "↗";
        position: absolute;
        left: 21px;
        top: 50%;
        transform: translateY(-50%);
        z-index: 2;
        color: rgba(147, 231, 255, 0.70);
        font-size: 0.94rem;
        line-height: 1;
        pointer-events: none;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput input {
        width: 100% !important;
        min-height: 60px !important;
        box-sizing: border-box !important;
        border-radius: 18px !important;
        border: 1px solid rgba(103, 232, 249, 0.42) !important;
        background:
            linear-gradient(180deg, rgba(8, 18, 38, 0.96), rgba(10, 24, 50, 0.88)) !important;
        color: #f8fafc !important;
        box-shadow:
            inset 0 2px 10px rgba(0, 0, 0, 0.28),
            inset 0 1px 0 rgba(255, 255, 255, 0.05),
            0 0 0 1px rgba(56, 189, 248, 0.035),
            0 12px 28px rgba(0, 0, 0, 0.20) !important;
        padding: 0 18px 0 46px !important;
        font-size: 0.98rem !important;
        line-height: 60px !important;
        caret-color: #67e8f9 !important;
        overflow: visible !important;
        transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput input::placeholder {
        color: rgba(191, 219, 254, 0.54) !important;
        font-weight: 520 !important;
    }
    .element-container:has(.link-card-anchor) ~ div .stTextInput input:focus {
        border-color: rgba(103, 232, 249, 0.70) !important;
        box-shadow:
            0 0 0 3px rgba(34, 211, 238, 0.09),
            0 0 20px rgba(34, 211, 238, 0.08),
            inset 0 2px 10px rgba(0, 0, 0, 0.27),
            0 14px 32px rgba(0, 0, 0, 0.24) !important;
        outline: none !important;
    }
    .element-container:has(.link-button-anchor) + div .stButton {
        display: flex !important;
        justify-content: flex-end !important;
        margin-top: 10px !important;
    }
    .element-container:has(.link-button-anchor) + div .stButton > button {
        width: min(100%, 258px) !important;
        min-height: 44px !important;
        padding: 0.48rem 1rem !important;
        border-radius: 13px !important;
        border: 1px solid rgba(125, 211, 252, 0.34) !important;
        background: linear-gradient(135deg, #2563eb 0%, #0891b2 100%) !important;
        color: #f8fafc !important;
        font-weight: 800 !important;
        box-shadow: 0 11px 24px rgba(37, 99, 235, 0.19), 0 0 0 rgba(34, 211, 238, 0) !important;
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, filter 180ms ease !important;
    }
    .element-container:has(.link-button-anchor) + div .stButton > button:hover {
        transform: translateY(-1px) !important;
        border-color: rgba(165, 243, 252, 0.52) !important;
        filter: saturate(1.04) brightness(1.03);
        box-shadow: 0 14px 28px rgba(37, 99, 235, 0.23), 0 0 18px rgba(34, 211, 238, 0.09) !important;
    }
    .element-container:has(.link-button-success) + div .stButton > button {
        background: linear-gradient(135deg, #16a34a, #22c55e) !important;
        border-color: rgba(134, 239, 172, 0.55) !important;
        color: #f0fdf4 !important;
        box-shadow: 0 0 18px rgba(34, 197, 94, 0.20), 0 12px 28px rgba(22, 163, 74, 0.18) !important;
    }
    @media (max-width: 720px) {
        .paste-glass-card {
            padding: 14px;
            border-radius: 16px;
        }
        .paste-info-compact {
            min-height: 58px;
            border-radius: 14px;
            line-height: 1.45;
        }
        .element-container:has(.paste-card-anchor) ~ div .stTextArea textarea {
            height: 240px !important;
            min-height: 240px !important;
        }
        .element-container:has(.paste-button-anchor) + div .stButton > button {
            width: 100% !important;
        }
        .link-glass-card {
            padding: 14px;
            border-radius: 16px;
        }
        .link-info-compact {
            min-height: 58px;
            border-radius: 14px;
            line-height: 1.45;
        }
        .element-container:has(.link-button-anchor) + div .stButton > button {
            width: 100% !important;
        }
    }
    /* UX polish: visual-only refinements for cards, inputs, and mobile spacing. */
    .hero-shell,
    div[data-testid="stTabs"],
    .result-card,
    .legal-note,
    .uploaded-file-card,
    .analysis-full-card,
    div[data-testid="stExpander"],
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(148, 163, 184, 0.18) !important;
        background:
            linear-gradient(180deg, rgba(15, 23, 42, 0.66), rgba(8, 13, 26, 0.52)) !important;
        box-shadow:
            0 18px 54px rgba(0, 0, 0, 0.26),
            inset 0 1px 0 rgba(255, 255, 255, 0.045) !important;
        backdrop-filter: blur(18px) saturate(1.08) !important;
    }
    .result-card,
    .uploaded-file-card,
    .analysis-full-card {
        transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
    }
    .result-card:hover,
    .uploaded-file-card:hover,
    .analysis-full-card:hover {
        transform: translateY(-2px);
        border-color: rgba(125, 211, 252, 0.30) !important;
        box-shadow:
            0 24px 64px rgba(0, 0, 0, 0.32),
            0 0 28px rgba(56, 189, 248, 0.07),
            inset 0 1px 0 rgba(255, 255, 255, 0.055) !important;
    }
    .stButton > button,
    .stDownloadButton > button {
        min-height: 46px !important;
        border-radius: 14px !important;
        box-shadow:
            0 14px 34px rgba(37, 99, 235, 0.20),
            inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(125, 211, 252, 0.62) !important;
        box-shadow:
            0 20px 46px rgba(37, 99, 235, 0.26),
            0 0 24px rgba(34, 211, 238, 0.09),
            inset 0 1px 0 rgba(255, 255, 255, 0.10) !important;
    }
    textarea,
    input,
    div[data-testid="stFileUploaderDropzone"] {
        border-color: rgba(103, 232, 249, 0.28) !important;
        background:
            linear-gradient(180deg, rgba(8, 18, 38, 0.94), rgba(10, 24, 50, 0.82)) !important;
        box-shadow:
            inset 0 2px 10px rgba(0, 0, 0, 0.28),
            0 12px 30px rgba(0, 0, 0, 0.20) !important;
    }
    textarea:hover,
    input:hover,
    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: rgba(125, 211, 252, 0.44) !important;
    }
    textarea:focus,
    input:focus {
        border-color: rgba(103, 232, 249, 0.72) !important;
        box-shadow:
            0 0 0 3px rgba(34, 211, 238, 0.10),
            0 18px 44px rgba(0, 0, 0, 0.26),
            inset 0 2px 10px rgba(0, 0, 0, 0.30) !important;
    }
    @media (max-width: 720px) {
        .main .block-container {
            padding-top: 1.1rem !important;
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
            padding-bottom: 3.5rem !important;
        }
        .hero-shell {
            padding: 20px !important;
            margin-bottom: 18px !important;
            border-radius: 18px !important;
        }
        div[data-testid="stTabs"] {
            padding: 12px !important;
            border-radius: 16px !important;
        }
        div[data-testid="stTabs"] [role="tablist"] {
            gap: 6px !important;
            overflow-x: auto !important;
            padding-bottom: 8px !important;
        }
        div[data-testid="stTabs"] [role="tab"] {
            min-height: 40px !important;
            padding: 0 12px !important;
            white-space: nowrap !important;
        }
        .result-grid {
            gap: 12px !important;
        }
        .result-card,
        .legal-note,
        .uploaded-file-card,
        .analysis-full-card {
            border-radius: 15px !important;
            padding: 14px !important;
        }
        .section-title {
            margin-top: 20px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
render_icon_sidebar("home")

wk = st.session_state.widget_key  # kısa alias

sekme1, sekme2, sekme3 = st.tabs(["Doküman Yükle", "Metin Yapıştır", "Link Analizi"])

with sekme1:
    yuklenen_dosya = st.file_uploader(
        "Dosyanızı seçin", type=['pdf', 'docx', 'txt'],
        label_visibility="collapsed",
        key=f"uploader_{wk}"
    )
    if yuklenen_dosya:
        st.markdown(
            f"""
            <div class="uploaded-file-card">
                <div class="uploaded-file-meta">
                    <div class="uploaded-file-icon">📄</div>
                    <div class="uploaded-file-name">{yuklenen_dosya.name}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Yüklenen dosyayı kaldır", key=f"dosya_sil_btn_{wk}", use_container_width=True):
            st.session_state.analiz_metni = ""
            st.session_state.sozlesme_yuklendi = False
            st.session_state.analiz_sonucu = ""
            st.session_state.chat_gecmisi = []
            st.session_state.metin_aktarildi = False
            st.session_state.link_aktarildi = False
            st.session_state.widget_key += 1
            st.rerun()

        cikarilan_metin = dokuman_okuyucu(yuklenen_dosya)
        if cikarilan_metin and len(cikarilan_metin.strip()) > 10:
            st.success(f"{yuklenen_dosya.name} başarıyla okundu.")
            with st.expander("Okunan metni gözden geçir"):
                st.write(cikarilan_metin[:1000] + "...")
            if st.session_state.analiz_metni != cikarilan_metin:
                st.session_state.analiz_metni = cikarilan_metin
                st.session_state.sozlesme_yuklendi = True
                st.session_state.chat_gecmisi = []
                st.session_state.analiz_sonucu = ""

with sekme2:
    st.markdown(
        """
        <div class="paste-glass-card">
            <span class="paste-card-anchor"></span>
            <div class="paste-info-compact">
                <span class="paste-info-dot">i</span>
                <span>Sözleşme metninizi buraya yapıştırın; analiz için güvenli şekilde hazırlanacak.</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    yapistirilan_metin = st.text_area(
        "Sözleşme metni", height=252,
        placeholder="Sözleşme metninizi buraya yapıştırın...",
        key=f"textarea_{wk}"
    )
    st.markdown(
        f'<div class="paste-counter">{len(yapistirilan_metin)} / 20000 karakter</div>',
        unsafe_allow_html=True,
    )
    metin_basari_durumu = (
        st.session_state.metin_aktarildi
        and yapistirilan_metin.strip()
        and yapistirilan_metin == st.session_state.analiz_metni
    )
    if metin_basari_durumu:
        st.markdown(
            """
            <style>
            .element-container:has(.paste-card-anchor) ~ div .stTextArea textarea {
                border-color: rgba(34, 197, 94, 0.72) !important;
                box-shadow:
                    0 0 0 3px rgba(34, 197, 94, 0.10),
                    inset 0 2px 9px rgba(0, 0, 0, 0.24),
                    0 14px 34px rgba(22, 163, 74, 0.13) !important;
            }
            </style>
            <span class="metin-success-style"></span>
            """,
            unsafe_allow_html=True,
        )

    button_state_class = "paste-button-success" if metin_basari_durumu else ""
    st.markdown(f'<span class="paste-button-anchor {button_state_class}"></span>', unsafe_allow_html=True)
    metin_buton_etiketi = "✓ Metin yüklendi" if metin_basari_durumu else "→ Bu metni kullan"
    if st.button(metin_buton_etiketi, key=f"metin_btn_{wk}", use_container_width=True):
        if yapistirilan_metin.strip():
            with st.spinner("Metin aktarılıyor..."):
                st.session_state.analiz_metni = yapistirilan_metin
                st.session_state.sozlesme_yuklendi = True
                st.session_state.chat_gecmisi = []
                st.session_state.analiz_sonucu = ""
                st.session_state.link_aktarildi = False
                st.session_state.metin_aktarildi = True
            st.rerun()
        else:
            st.session_state.metin_aktarildi = False

    metin_basari_durumu = (
        st.session_state.metin_aktarildi
        and yapistirilan_metin.strip()
        and yapistirilan_metin == st.session_state.analiz_metni
    )
    st.markdown("</div>", unsafe_allow_html=True)
with sekme3:
    st.markdown(
        """
        <div class="link-glass-card">
            <span class="link-card-anchor"></span>
            <div class="link-info-compact">
                <span class="link-info-icon">↗</span>
                <span>Sözleşmenin bulunduğu URL’yi yapıştırıp Enter’a basın.</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    girilen_url = st.text_input(
        "Web sitesi linki",
        placeholder="https://example.com/terms",
        key=f"url_input_{wk}"
    )
    temiz_url = girilen_url.strip()
    if temiz_url and temiz_url != st.session_state.son_url:
        st.session_state.son_url = temiz_url
        st.session_state.link_aktarildi = False
        with st.spinner("İçerik çekiliyor..."):
            cikarilan_metin = url_okuyucu(temiz_url)
            if cikarilan_metin and len(cikarilan_metin.strip()) > 50:
                with st.expander("Çekilen metni gözden geçir"):
                    st.write(cikarilan_metin[:1000] + "...")
                st.session_state.analiz_metni = cikarilan_metin
                st.session_state.sozlesme_yuklendi = True
                st.session_state.chat_gecmisi = []
                st.session_state.analiz_sonucu = ""
                st.session_state.metin_aktarildi = False
                st.session_state.link_aktarildi = True
    st.markdown("</div>", unsafe_allow_html=True)

sekme_icinde_basari_aktif = (
    (st.session_state.get("metin_aktarildi", False) or st.session_state.get("link_aktarildi", False))
    and st.session_state.get("analiz_metni", "").strip()
)

if st.session_state.sozlesme_yuklendi and not sekme_icinde_basari_aktif:
    st.success("Sözleşme yüklendi. Sol menüden Chatbot sayfasına geçerek soru sorabilirsiniz.")

st.markdown('<div class="section-title">Analiz işlemi</div>', unsafe_allow_html=True)

analiz_buton_metni = "Analiz yapılıyor..." if st.session_state.analiz_yapiliyor else "✨ Sözleşmeyi analiz et"
analiz_butona_basildi = st.button(
    analiz_buton_metni,
    use_container_width=True,
    disabled=st.session_state.analiz_yapiliyor,
)

if analiz_butona_basildi and not st.session_state.analiz_yapiliyor:
    if not st.session_state.analiz_metni.strip():
        st.error("Önce bir sözleşme yükleyin.")
    else:
        st.session_state.analiz_hatasi = ""
        st.session_state.analiz_yapiliyor = True
        st.session_state.analiz_tetikle = True
        st.rerun()

if st.session_state.analiz_tetikle and st.session_state.analiz_yapiliyor:
    try:
        with st.spinner("Analiz yapılıyor..."):
            prompt = f"""
Sen hukuki metinleri analiz etmek ve Kişisel Verilerin Korunması Kanunu (KVKK) uyumluluğunu denetlemek üzere tasarlanmış uzman bir Yapay Zeka Asistanısın. Asla resmi bir avukat olduğunu iddia etme. Aşağıdaki metni oku ve sıradan bir vatandaşın anlayacağı dilde tam olarak şu formatta cevap ver:
                
                📋 1. Sözleşmenin Kimliği
                - Sözleşme Türü: (Örn: Gizlilik, Hizmet Kullanım, Satış vb.)
                - Taraflar: (Bu sözleşme kimler arasında yapılıyor?)
                - Geçerlilik Süresi: (Ne zamana kadar geçerli? Metinde tarih yoksa "Belirtilmemiş" yaz.)

                📝 2. Sözleşmenin Genel Özeti
                (Maksimum 2 cümle ile ana amacı açıkla.)

                🚨 3. Kullanıcı İçin Kritik Riskler
                (Gizli ücretler, hesabın tek taraflı kapatılması, cayma hakkı zorlukları vb. riskleri madde madde yaz. KVKK risklerini buraya yazma, onu aşağıda değerlendir.)

                🇹🇷 4. KVKK (Kişisel Veri) Uyumluluk Analizi
                (Metni KVKK açısından incele. 'Açık Rıza' alınıyor mu? Veriler yurtdışına veya 3. şahıslara aktarılıyor mu? Veri saklama süresi belli mi? Eğer sözleşmede hiç KVKK veya veri maddesi yoksa "Bu metinde kişisel veri işleme şartlarına dair bir madde bulunmamaktadır" yaz.)

                

Sözleşme Metni:
{st.session_state.analiz_metni}
"""
            model = model_olustur()
            response = model.generate_content(prompt)
            st.session_state.analiz_sonucu = response.text
            st.session_state.analiz_hatasi = ""
    except Exception as e:
        st.session_state.analiz_hatasi = "AI şu anda yoğun. Lütfen birkaç saniye sonra tekrar deneyin."
    finally:
        st.session_state.analiz_yapiliyor = False
        st.session_state.analiz_tetikle = False
        st.rerun()

if st.session_state.analiz_hatasi:
    st.error(st.session_state.analiz_hatasi)

if st.session_state.analiz_sonucu:
    st.success("Analiz tamamlandı.")
    temiz_analiz_sonucu = html_taglerini_temizle(st.session_state.analiz_sonucu)

    st.markdown(
        f'<div class="analysis-full-card">{escape(temiz_analiz_sonucu)}</div>',
        unsafe_allow_html=True
    )

    try:
        pdf_verisi = analiz_pdf_olustur(temiz_analiz_sonucu)

        st.download_button(
            "Analizi PDF olarak indir",
            data=pdf_verisi,
            file_name=f"sozlesme_analizi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except ModuleNotFoundError:
        st.warning("PDF indirme için reportlab kurulu olmalı.")

if st.session_state.sozlesme_yuklendi:
    if st.button("Sözleşmeyi sil ve sıfırla", use_container_width=True):
        st.session_state.analiz_metni = ""
        st.session_state.sozlesme_yuklendi = False
        st.session_state.analiz_sonucu = ""
        st.session_state.chat_gecmisi = []
        st.session_state.son_url = ""
        st.session_state.metin_aktarildi = False
        st.session_state.link_aktarildi = False
        st.session_state.widget_key += 1
        st.rerun()

st.markdown(
    """
    <div class="legal-note">
        <strong>Yasal uyarı:</strong> Bu platformdaki analizler yapay zeka tarafından üretilir;
        resmi hukuki tavsiye niteliğinde değildir. Kesin hükümler için bir avukata danışın.
    </div>
    """,
    unsafe_allow_html=True,
)
