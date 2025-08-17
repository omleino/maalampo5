import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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

def laske_kaukolampo_kustannukset(kustannus, inflaatio):
    tulos = []
    h = kustannus
    for _ in range(50):
        tulos.append(h)
        h *= (1 + inflaatio / 100)
    return tulos

def takaisinmaksuaika_investointi(investointi, kaukolampo, maalampo):
    vuosittainen_saasto = np.array(kaukolampo) - np.array(maalampo)
    kum = np.cumsum(vuosittainen_saasto)
    for vuosi, summa in enumerate(kum, 1):
        if summa >= investointi:
            return vuosi
    return None

def erittely_listat(investointi, laina_aika, korko, sahkon_hinta, kulutus, inflaatio,
                    korjaus_vali, korjaus_hinta, korjaus_laina_aika):
    rahoitus, lampo = [], []
    jaljella = investointi
    lyhennys = investointi / laina_aika
    h = sahkon_hinta
    korjauslainat = []

    for v in range(1, 51):
        if v <= laina_aika:
            korko_v = jaljella * (korko / 100)
            rah = lyhennys + korko_v
            jaljella -= lyhennys
        else:
            rah = 0

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

        elec = h * kulutus
        lampo.append(elec + korjaus_lyh + korjaus_korot)
        rahoitus.append(rah)
        h *= (1 + inflaatio / 100)

    return rahoitus, lampo

# ---------- SOVELLUS ----------

st.set_page_config(page_title="Lämmitysvaihtoehdot", layout="wide")
st.title("Maalämpö (3 sähkön hintaa) vs Kaukolämpö – 50 vuotta")

with st.sidebar:
    st.header("Yhteiset oletukset")
    investointi = st.number_input("Investointi (€)", min_value=0.0, value=650000.0, step=10000.0)
    laina_aika = st.slider("Laina-aika (v)", 5, 40, 20)
    korko = st.number_input("Korko (%/v)", min_value=0.0, value=3.0, step=0.1)
    kulutus = st.number_input("Sähkönkulutus (kWh/v)", min_value=0.0, value=180000.0, step=10000.0)
    inflaatio = st.number_input("Sähkön inflaatio (%/v)", min_value=0.0, value=2.0, step=0.1)
    korjaus_vali = st.slider("Korjausväli (v)", 5, 30, 15)
    korjaus_hinta = st.number_input("Korjauksen hinta (€)", min_value=0.0, value=20000.0, step=5000.0)
    korjaus_laina_aika = st.slider("Korjauslaina (v)", 1, 30, 10)
    maalampo_kk_kulu = st.number_input("Maalämmön kuukausikustannus (€ / kk)", min_value=0.0, value=100.0, step=10.0)

    st.header("Sähkön hinnat")
    h1 = st.number_input("Vaihtoehto A (€/kWh)", min_value=0.0, value=0.08, step=0.01)
    h2 = st.number_input("Vaihtoehto B (€/kWh)", min_value=0.0, value=0.12, step=0.01)
    h3 = st.number_input("Vaihtoehto C (€/kWh)", min_value=0.0, value=0.16, step=0.01)

    st.header("Kaukolämpö")
    kl0 = st.number_input("Kaukolämpö/vuosi (€)", min_value=0.0, value=85000.0, step=5000.0)
    kl_inf = st.number_input("Kaukolämmön inflaatio (%/v)", min_value=0.0, value=2.0, step=0.1)

    st.header("Maksuperuste")
    neliot = st.number_input("Maksavat neliöt (m²)", min_value=1.0, value=1000.0, step=100.0)

# Laskelmat
vuodet = list(range(1, 51))
ml_extra = maalampo_kk_kulu * 12
kl = laske_kaukolampo_kustannukset(kl0, kl_inf)
ml1 = [v + ml_extra for v in laske_kustannukset_50v(investointi, laina_aika, korko, h1, kulutus, korjaus_vali, korjaus_hinta, korjaus_laina_aika, inflaatio)]
ml2 = [v + ml_extra for v in laske_kustannukset_50v(investointi, laina_aika, korko, h2, kulutus, korjaus_vali, korjaus_hinta, korjaus_laina_aika, inflaatio)]
ml3 = [v + ml_extra for v in laske_kustannukset_50v(investointi, laina_aika, korko, h3, kulutus, korjaus_vali, korjaus_hinta, korjaus_laina_aika, inflaatio)]

# Kaavio
fig, ax = plt.subplots()
ax.plot(vuodet, kl, "--", label="Kaukolämpö")
ax.plot(vuodet, ml1, label=f"Maalämpö A ({h1:.2f} €/kWh)")
ax.plot(vuodet, ml2, label=f"Maalämpö B ({h2:.2f} €/kWh)")
ax.plot(vuodet, ml3, label=f"Maalämpö C ({h3:.2f} €/kWh)")
ax.set_xlabel("Vuosi"); ax.set_ylabel("Kustannus (€)")
ax.set_title("Lämmityskustannukset 50 vuoden ajalta")
ax.grid(True); ax.legend()
st.pyplot(fig, use_container_width=True)


# Vastiketaulukko (5 v välein)
rahoitus, _ = erittely_listat(investointi, laina_aika, korko, h1, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
_, lampo1 = erittely_listat(investointi, laina_aika, korko, h1, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
_, lampo2 = erittely_listat(investointi, laina_aika, korko, h2, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
_, lampo3 = erittely_listat(investointi, laina_aika, korko, h3, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
kl_vastike = laske_kaukolampo_kustannukset(kl0, kl_inf)

yrs5 = list(range(5, 51, 5))
tbl = pd.DataFrame({
    "Vuosi": yrs5,
    "Rahoitusvastike €/m²/kk": [rahoitus[y-1]/neliot/12 for y in yrs5],
    "Lämmitysvastike A €/m²/kk": [(lampo1[y-1] + maalampo_kk_kulu * 12)/neliot/12 for y in yrs5],
    "Lämmitysvastike B €/m²/kk": [(lampo2[y-1] + maalampo_kk_kulu * 12)/neliot/12 for y in yrs5],
    "Lämmitysvastike C €/m²/kk": [(lampo3[y-1] + maalampo_kk_kulu * 12)/neliot/12 for y in yrs5],
    "Kaukolämpö €/m²/kk": [kl_vastike[y-1]/neliot/12 for y in yrs5]
}).set_index("Vuosi")
st.markdown("### Rahoitus- ja lämmitysvastikkeet €/m²/kk (5 v välein)")
st.dataframe(tbl.style.format("{:.2f}"), use_container_width=True)

# Takaisinmaksuaika
pb1 = takaisinmaksuaika_investointi(investointi, kl, ml1)
pb2 = takaisinmaksuaika_investointi(investointi, kl, ml2)
pb3 = takaisinmaksuaika_investointi(investointi, kl, ml3)
st.markdown("##")
# Vastiketaulukko (5 v välein)
rahoitus, _ = erittely_listat(investointi, laina_aika, korko, h1, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
_, lampo1 = erittely_listat(investointi, laina_aika, korko, h1, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
_, lampo2 = erittely_listat(investointi, laina_aika, korko, h2, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
_, lampo3 = erittely_listat(investointi, laina_aika, korko, h3, kulutus, inflaatio, korjaus_vali, korjaus_hinta, korjaus_laina_aika)
kl_vastike = laske_kaukolampo_kustannukset(kl0, kl_inf)

yrs5 = list(range(5, 51, 5))
tbl = pd.DataFrame({
    "Vuosi": yrs5,
    "Rahoitusvastike €/m²/kk": [rahoitus[y-1]/neliot/12 for y in yrs5],
    "Lämmitysvastike A €/m²/kk": [(lampo1[y-1] + maalampo_kk_kulu * 12)/neliot/12 for y in yrs5],
    "Lämmitysvastike B €/m²/kk": [(lampo2[y-1] + maalampo_kk_kulu * 12)/neliot/12 for y in yrs5],
    "Lämmitysvastike C €/m²/kk": [(lampo3[y-1] + maalampo_kk_kulu * 12)/neliot/12 for y in yrs5],
    "Kaukolämpö €/m²/kk": [kl_vastike[y-1]/neliot/12 for y in yrs5]
}).set_index("Vuosi")
st.markdown("### Rahoitus- ja lämmitysvastikkeet €/m²/kk (5 v välein)")
st.dataframe(tbl.style.format("{:.2f}"), use_container_width=True)

# Takaisinmaksuaika (investoinnin takaisinmaksu)")
def f(v): return f"{v} vuotta" if v else "ei 50 vuodessa"
st.write(f"**Maalämpö A ({h1:.2f} €/kWh):** {f(pb1)}")
st.write(f"**Maalämpö B ({h2:.2f} €/kWh):** {f(pb2)}")
st.write(f"**Maalämpö C ({h3:.2f} €/kWh):** {f(pb3)}")

# Lainaosuus
st.markdown(f"**Lainaosuus investoinnille:** {investointi / neliot:,.0f} €/m²")

# PDF
