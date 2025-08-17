
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

# Oletusarvot
investointi = 650000
laina_aika = 20
korko = 3.0
kulutus = 180000
inflaatio = 2.0
korjaus_vali = 15
korjaus_hinta = 20000
korjaus_laina_aika = 10
maalampo_kk_kulu = 100.0
h1 = 0.08
kl0 = 85000.0
kl_inf = 2.0
neliot = 1000

# Laskenta
vuodet = list(range(1, 51))
ml_extra = maalampo_kk_kulu * 12
ml1 = [v + ml_extra for v in laske_kustannukset_50v(investointi, laina_aika, korko, h1, kulutus,
        korjaus_vali, korjaus_hinta, korjaus_laina_aika, inflaatio)]

# Kuvaaja
fig, ax = plt.subplots()
ax.plot(vuodet, ml1, label="Maalämpö ({:.2f} €/kWh)".format(h1))
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
    "Sähkön hinta (€/kWh)": h1,
    "Kaukolämpö/vuosi (€)": kl0,
    "Kaukolämmön inflaatio (%/v)": kl_inf,
    "Maksavat neliöt (m²)": neliot
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
