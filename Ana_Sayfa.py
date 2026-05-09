import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import docx
import requests
from bs4 import BeautifulSoup

# --- AYARLAR ---
API_KEY = "BURAYA_KENDİ_APİNİZİ_GİRİN"
genai.configure(api_key=API_KEY)

dogru_model_adi = "gemini-1.5-flash"
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        dogru_model_adi = m.name
        break
model = genai.GenerativeModel(dogru_model_adi)

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

# --- SAYFA ---
st.set_page_config(page_title="Sözleşme Rehberim", page_icon="⚖️", layout="wide")
st.title("⚖️ Sözleşme Rehberim")
st.markdown("Uzun hukuki sözleşmeleri saniyeler içinde analiz edin ve gizli riskleri öğrenin.")
st.divider()

wk = st.session_state.widget_key  # kısa alias

sekme1, sekme2, sekme3 = st.tabs(["📁 Doküman Yükle", "📝 Metin Yapıştır", "🌐 Link (URL) Analizi"])

with sekme1:
    st.info("PDF, Word (.docx) veya TXT formatında yükleyebilirsiniz.")
    yuklenen_dosya = st.file_uploader(
        "Dosyanızı seçin", type=['pdf', 'docx', 'txt'],
        key=f"uploader_{wk}"
    )
    if yuklenen_dosya:
        cikarilan_metin = dokuman_okuyucu(yuklenen_dosya)
        if cikarilan_metin and len(cikarilan_metin.strip()) > 10:
            st.success(f"✅ {yuklenen_dosya.name} başarıyla okundu!")
            with st.expander("Okunan Metni Gözden Geçir"):
                st.write(cikarilan_metin[:1000] + "...")
            if st.session_state.analiz_metni != cikarilan_metin:
                st.session_state.analiz_metni = cikarilan_metin
                st.session_state.sozlesme_yuklendi = True
                st.session_state.chat_gecmisi = []
                st.session_state.analiz_sonucu = ""

with sekme2:
    st.info("Sözleşme metnini kopyalayıp yapıştırın.")
    yapistirilan_metin = st.text_area(
        "Sözleşme Metni:", height=200,
        placeholder="Metni buraya yapıştırın...",
        key=f"textarea_{wk}"
    )
    if st.button("Bu Metni Kullan ✅", key=f"metin_btn_{wk}"):
        if yapistirilan_metin.strip():
            st.session_state.analiz_metni = yapistirilan_metin
            st.session_state.sozlesme_yuklendi = True
            st.session_state.chat_gecmisi = []
            st.session_state.analiz_sonucu = ""
            st.success("✅ Metin kaydedildi!")

with sekme3:
    st.info("Sözleşmenin bulunduğu URL'yi yapıştırıp Enter'a basın.")
    girilen_url = st.text_input(
        "Web Sitesi Linki:", placeholder="https://...",
        key=f"url_input_{wk}"
    )
    if girilen_url and girilen_url != st.session_state.son_url:
        st.session_state.son_url = girilen_url
        with st.spinner("İçerik çekiliyor..."):
            cikarilan_metin = url_okuyucu(girilen_url)
            if cikarilan_metin and len(cikarilan_metin.strip()) > 50:
                st.success("✅ Web sitesi metni çekildi!")
                with st.expander("Çekilen Metni Gözden Geçir"):
                    st.write(cikarilan_metin[:1000] + "...")
                st.session_state.analiz_metni = cikarilan_metin
                st.session_state.sozlesme_yuklendi = True
                st.session_state.chat_gecmisi = []
                st.session_state.analiz_sonucu = ""

st.divider()

if st.session_state.sozlesme_yuklendi:
    st.success("✅ Sözleşme yüklendi. Sol menüden **💬 Chatbot** sayfasına geçerek soru sorabilirsiniz.")

st.subheader("🚀 Analiz İşlemi")

if st.button("Sözleşmeyi Analiz Et 🔍", use_container_width=True):
    if not st.session_state.analiz_metni.strip():
        st.error("Önce bir sözleşme yükleyin!")
    else:
        with st.spinner("Yapay Zeka sözleşmeyi hukuki açıdan değerlendiriyor..."):
            try:
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

                🛡️ 5. Genel Güvenlik Skoru
                (Kullanıcı hakları ve veri gizliliği açısından 10 üzerinden bir puan ver ve nedenini tek cümleyle açıkla.)
                

Sözleşme Metni:
{st.session_state.analiz_metni}
"""
                response = model.generate_content(prompt)
                st.session_state.analiz_sonucu = response.text
            except Exception as e:
                st.error(f"Yapay zeka ile iletişim kurulurken bir hata oluştu: {e}")

if st.session_state.analiz_sonucu:
    st.success("✅ Analiz Tamamlandı!")
    with st.container(border=True):
        st.markdown(st.session_state.analiz_sonucu)

st.divider()

if st.session_state.sozlesme_yuklendi:
    if st.button("🗑️ Sözleşmeyi Sil ve Sıfırla", use_container_width=True):
        st.session_state.analiz_metni = ""
        st.session_state.sozlesme_yuklendi = False
        st.session_state.analiz_sonucu = ""
        st.session_state.chat_gecmisi = []
        st.session_state.son_url = ""
        st.session_state.widget_key += 1
        st.rerun()

st.caption("⚠️ **Yasal Uyarı:** Bu platformdaki analizler yapay zeka (Gemini 1.5 Flash) tarafından üretilmektedir ve %100 doğruluk garantisi taşımaz. Üretilen içerikler bilgilendirme amaçlıdır ve resmi bir hukuki tavsiye niteliğinde değildir. Kesin hükümler için lütfen gerçek bir avukata danışın.")
