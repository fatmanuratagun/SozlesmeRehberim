import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import docx
import requests
from bs4 import BeautifulSoup # YENİ: Web sitelerini okumak için eklendi

# --- 1. AYARLAR VE YAPAY ZEKA BAĞLANTISI ---
API_KEY = "BURAYA_API_ANAHTARINIZI_YAZIN"
genai.configure(api_key=API_KEY)

dogru_model_adi = "gemini-1.5-flash"
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        dogru_model_adi = m.name
        break 
model = genai.GenerativeModel(dogru_model_adi)

# --- 2. YARDIMCI FONKSİYONLAR ---

def dokuman_okuyucu(yuklenen_dosya):
    """Yüklenen PDF, Word veya TXT dosyasını okur."""
    metin = ""
    try:
        dosya_adi = yuklenen_dosya.name.lower()
        if dosya_adi.endswith('.pdf'):
            pdf_nesnesi = PdfReader(yuklenen_dosya)
            for sayfa in pdf_nesnesi.pages:
                sayfa_metni = sayfa.extract_text()
                if sayfa_metni: metin += sayfa_metni + "\n"
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
    """Verilen URL'deki web sayfasının metnini çeker (Web Scraping)."""
    try:
        # Sitelerin bizi 'bot' sanıp engellemesini önlemek için tarayıcı kimliği (User-Agent) ekliyoruz
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Eğer site 404 vs verirse hatayı yakalar
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Sitedeki gereksiz kodları (menüler, scriptler, reklamlar) temizliyoruz
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
            
        # Sadece saf metni alıyoruz
        metin = soup.get_text(separator=' ', strip=True)
        return metin
    except Exception as e:
        st.error(f"Bağlantıdan metin çekilemedi. Site güvenlik nedeniyle botları engelliyor olabilir. Hata: {e}")
        return None

# --- 3. KULLANICI ARAYÜZÜ (UI/UX) ---
st.set_page_config(page_title="Sözleşme Rehberim", page_icon="⚖️", layout="wide")

st.title("⚖️ Sözleşme Rehberim - AI Risk Analizi")
st.markdown("Uzun hukuki sözleşmeleri saniyeler içinde analiz edin ve gizli riskleri öğrenin.")
st.divider()

analiz_edilecek_metin = ""

# YENİ: 3. Sekmeyi (Link Analizi) Ekledik
sekme1, sekme2, sekme3 = st.tabs(["📁 Doküman Yükle", "📝 Metin Yapıştır", "🌐 Link (URL) Analizi"])

with sekme1:
    st.info("Sözleşmenizi PDF, Word (.docx) veya TXT formatında yükleyebilirsiniz.")
    yuklenen_dosya = st.file_uploader("Dosyanızı seçin", type=['pdf', 'docx', 'txt'])
    
    if yuklenen_dosya:
        cikarilan_metin = dokuman_okuyucu(yuklenen_dosya)
        if cikarilan_metin and len(cikarilan_metin.strip()) > 10:
            st.success(f"✅ Doküman ({yuklenen_dosya.name}) başarıyla okundu!")
            with st.expander("Okunan Metni Gözden Geçir"):
                st.write(cikarilan_metin[:1000] + "...")
            analiz_edilecek_metin = cikarilan_metin

with sekme2:
    st.info("Sözleşme metnini doğrudan kopyalayıp aşağıdaki alana yapıştırabilirsiniz.")
    yapistirilan_metin = st.text_area("Sözleşme Metni:", height=200, placeholder="Lütfen metni buraya yapıştırın...")
    if yapistirilan_metin:
        analiz_edilecek_metin = yapistirilan_metin

with sekme3:
    st.info("Sözleşmenin bulunduğu web sitesinin linkini (URL) yapıştırın.")
    girilen_url = st.text_input("Web Sitesi Linki (Örn: https://www.whatsapp.com/legal/terms-of-service)")
    
    if girilen_url:
        with st.spinner("Siteye bağlanılıyor ve içerik çekiliyor..."):
            cikarilan_metin = url_okuyucu(girilen_url)
            if cikarilan_metin and len(cikarilan_metin.strip()) > 50:
                st.success("✅ Web sitesi metni başarıyla çekildi!")
                with st.expander("Çekilen Metni Gözden Geçir"):
                    st.write(cikarilan_metin[:1000] + "... (Metnin devamı yapay zekaya iletilecek)")
                analiz_edilecek_metin = cikarilan_metin

# --- 4. ANALİZ MOTORU ---
st.divider()
st.subheader("🚀 Analiz İşlemi")

if st.button("Sözleşmeyi Analiz Et 🔍", use_container_width=True):
    if not analiz_edilecek_metin.strip():
        st.error("Lütfen analize başlamadan önce bir doküman yükleyin, metin veya link yapıştırın!")
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
                {analiz_edilecek_metin}
                """
                
                response = model.generate_content(prompt)
                
                st.success("✅ Analiz Tamamlandı!")
                with st.container(border=True):
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"Yapay zeka ile iletişim kurulurken bir hata oluştu: {e}")

# --- 5. YASAL UYARI (FOOTER) ---
st.divider()
st.caption("⚠️ **Yasal Uyarı:** Bu platformdaki analizler yapay zeka (Gemini 1.5 Flash) tarafından üretilmektedir ve %100 doğruluk garantisi taşımaz. Üretilen içerikler bilgilendirme amaçlıdır ve resmi bir hukuki tavsiye niteliğinde değildir. Kesin hükümler için lütfen gerçek bir avukata danışın.")
