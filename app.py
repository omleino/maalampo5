
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ---------- LASKENTAFUNKTIOT ----------

def laske_kustannukset_50v(investointi, laina_aika, korko, sahkon_hinta, sahkon_kulutus,
                            korjaus_vali, korjaus_hinta, korjaus_laina_aika, sahkon_inflaatio):
    vuodet = 50
    lyhennys = investointi / laina_aika
    jaljella = investointi
    hinta = sahkon_hinta
    kustannukset = []
    korjauslainat = []

    for v in range(1, vuodet + 1):
        lyh = lyhennys if v <= laina_aika else 0
        korko_inv = jaljella * (korko / 100) if v <= laina_aika else 0
        if v <= laina_aika:
            jaljella -= lyh

        sahko = hinta * sahkon_kulutus

        if v > 1 and (v - 1) % korjaus_vali == 0:
            korjauslainat.append({
                "jaljella": korjaus_hinta,
                "lyh": korjaus_hinta / korjaus_laina_aika,
                "vuosia": korjaus_laina_aika
            })

        korjaus_lyh = korjaus_korot = 0
        for l in korjauslainat:
            if l["vuosia"] > 0:
                korko_l = l["jaljella"] * (korko / 100)
                korjaus_korot += korko_l
                korjaus_lyh += l["lyh"]
                l["jaljella"] -= l["lyh"]
                l["vuosia"] -= 1
        korjauslainat = [l for l in korjauslainat if l["vuosia"] > 0]

        vuosi_kust = lyh + korko_inv + sahko + korjaus_lyh + korjaus_korot
        kustannukset.append(vuosi_kust)
        hinta *= (1 + sahkon_inflaatio / 100)

    return kustannukset

# ---------- KÄYTTÖLIITTYMÄ ----------

st.set_page_config(page_title="PDF-raportti", layout="wide")
st.title("Lämmityskustannuslaskuri + PDF-raportti")

# Syötteet sivupalkista
with st.sidebar:
    st.header("Lähtötiedot")
    investointi = st.number_input("Investointi (€)", value=650000, step=10000)
    laina_aika = st.slider("Laina-aika (v)", 5, 40, 20)
    korko = st.number_input("Korko (%/v)", value=3.0, step=0.1)
    kulutus = st.number_input("Sähkönkulutus (kWh/v)", value=180000, step=10000)
    inflaatio = st.number_input("Sähkön inflaatio (%/v)", value=2.0, step=0.1)
    korjaus_vali = st.slider("Korjausväli (v)", 5, 30, 15)
    korjaus_hinta = st.number_input("Korjauksen hinta (€)", value=20000, step=5000)
    korjaus_laina_aika = st.slider("Korjauslaina (v)", 1, 30, 10)
    maalampo_kk_kulu = st.number_input("Maalämmön kuukausikustannus (€ / kk)", value=100.0, step=10.0)
    sahkon_hinta = st.number_input("Sähkön hinta (€/kWh)", value=0.12, step=0.01)

# Laskenta
vuodet = list(range(1, 51))
ml_extra = maalampo_kk_kulu * 12
ml = [v + ml_extra for v in laske_kustannukset_50v(
    investointi, laina_aika, korko, sahkon_hinta, kulutus,
    korjaus_vali, korjaus_hinta, korjaus_laina_aika, inflaatio
)]

# Kuvaaja
fig, ax = plt.subplots()
ax.plot(vuodet, ml, label="Maalämpö ({:.2f} €/kWh)".format(sahkon_hinta))
ax.set_xlabel("Vuosi")
ax.set_ylabel("Kustannus (€)")
ax.set_title("Lämmityskustannukset 50 vuoden ajalta")
ax.grid(True)
ax.legend()
st.pyplot(fig, use_container_width=True)

# ========== PDF-LUONTI JA LATAUS ==========

# Tallenna kuvaaja PNG-tiedostoksi
kuva_polku = "/tmp/kuvaaja.png"
fig.savefig(kuva_polku, bbox_inches="tight")

# Luo PDF
pdf_buffer = io.BytesIO()
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
styles = getSampleStyleSheet()
elements = []

elements.append(Paragraph("Lämmitysjärjestelmän vertailu – Lähtötiedot", styles["Heading2"]))
elements.append(Spacer(1, 12))

syottotiedot = {
    "Investointi (€)": investointi,
    "Laina-aika (v)": laina_aika,
    "Korko (%/v)": korko,
    "Sähkönkulutus (kWh/v)": kulutus,
    "Sähkön inflaatio (%/v)": inflaatio,
    "Korjausväli (v)": korjaus_vali,
    "Korjauksen hinta (€)": korjaus_hinta,
    "Korjauslaina (v)": korjaus_laina_aika,
    "Maalämmön kuukausikustannus (€ / kk)": maalampo_kk_kulu,
    "Sähkön hinta (€/kWh)": sahkon_hinta
}

for nimi, arvo in syottotiedot.items():
    elements.append(Paragraph("<b>{}:</b> {}".format(nimi, arvo), styles["Normal"]))

elements.append(Spacer(1, 24))
elements.append(Paragraph("Kuvaaja:", styles["Heading3"]))
elements.append(Spacer(1, 12))
elements.append(Image(kuva_polku, width=6*inch, height=3.5*inch))

doc.build(elements)
pdf_buffer.seek(0)

# Latauspainike
st.download_button(
    label="📄 Lataa PDF-raportti",
    data=pdf_buffer,
    file_name="lamporatkaisu_raportti.pdf",
    mime="application/pdf"
)
