import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# ---------- LASKENTAFUNKTIOT ----------

def laske_kustannukset_50v(investointi, laina_aika, korko,
                            sahkon_hinta, sahkon_kulutus,
                            korjaus_vali, korjaus_hinta, korjaus_laina_aika,
                            sahkon_inflaatio):
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

def diskonttaa(kustannukset, diskontto):
    return [k / ((1 + diskontto / 100) ** i) for i, k in enumerate(kustannukset, 1)]

def npv(kustannukset, diskontto):
    return float(np.sum(diskonttaa(kustannukset, diskontto)))

def takaisinmaksuaika_investointi(investointi, kaukolampo, maalampo):
    vuosittainen_saasto = np.array(kaukolampo) - np.array(maalampo)
    kum = np.cumsum(vuosittainen_saasto)
    for vuosi, summa in enumerate(kum, 1):
        if summa >= investointi:
            return vuosi
    return None

# ---------- KÄYTTÖLIITTYMÄ ----------

st.set_page_config(page_title="Lämmitysvaihtoehdot", layout="wide")
st.title("Maalämpö (3 sähkön hintaa) vs Kaukolämpö – 50 vuoden vertailu")

with st.sidebar:
    st.header("Yhteiset oletukset")
    investointi = st.number_input("Investointi (€)", min_value=0.0, value=650_000.0, step=10_000.0)
    laina_aika = st.slider("Investointilaina (v)", 5, 40, 20)
    korko = st.number_input("Korko (%/v)", min_value=0.0, value=3.0, step=0.1)
    sahkon_kulutus = st.number_input("Sähkönkulutus (kWh/v)", min_value=0.0, value=180_000.0, step=10_000.0)
    sahkon_inflaatio = st.number_input("Sähkön inflaatio (%/v)", min_value=0.0, value=2.0, step=0.1)
    korjaus_vali = st.slider("Korjausväli (v)", 5, 30, 15)
    korjaus_hinta = st.number_input("Korjauksen hinta (€)", min_value=0.0, value=20_000.0, step=5_000.0)
    korjaus_laina_aika = st.slider("Korjauslaina (v)", 1, 30, 10)

    st.header("Maalämmön sähkön hinnat (€/kWh)")
    hinta1 = st.number_input("Vaihtoehto A", min_value=0.0, value=0.08, step=0.01)
    hinta2 = st.number_input("Vaihtoehto B", min_value=0.0, value=0.12, step=0.01)
    hinta3 = st.number_input("Vaihtoehto C", min_value=0.0, value=0.16, step=0.01)

    st.header("Kaukolämpö")
    kl_kustannus = st.number_input("Kaukolämpö/vuosi (€)", min_value=0.0, value=85_000.0, step=5_000.0)
    kl_inflaatio = st.number_input("Kaukolämmön inflaatio (%/v)", min_value=0.0, value=2.0, step=0.1)

    st.header("Muuta")
    diskontto = st.number_input("Diskonttokorko NPV (%/v)", min_value=0.0, value=4.0, step=0.1)
    neliot = st.number_input("Maksavat neliöt (m²)", min_value=1.0, value=1_000.0, step=100.0)

# ---------- LASKENTA ----------

vuodet = list(range(1, 51))
kl = laske_kaukolampo_kustannukset(kl_kustannus, kl_inflaatio)
ml1 = laske_kustannukset_50v(investointi, laina_aika, korko, hinta1, sahkon_kulutus,
                              korjaus_vali, korjaus_hinta, korjaus_laina_aika, sahkon_inflaatio)
ml2 = laske_kustannukset_50v(investointi, laina_aika, korko, hinta2, sahkon_kulutus,
                              korjaus_vali, korjaus_hinta, korjaus_laina_aika, sahkon_inflaatio)
ml3 = laske_kustannukset_50v(investointi, laina_aika, korko, hinta3, sahkon_kulutus,
                              korjaus_vali, korjaus_hinta, korjaus_laina_aika, sahkon_inflaatio)

# ---------- KAAVIO ----------

fig, ax = plt.subplots()
ax.plot(vuodet, kl, label="Kaukolämpö", linestyle="--")
ax.plot(vuodet, ml1, label=f"Maalämpö A ({hinta1:.2f} €/kWh)")
ax.plot(vuodet, ml2, label=f"Maalämpö B ({hinta2:.2f} €/kWh)")
ax.plot(vuodet, ml3, label=f"Maalämpö C ({hinta3:.2f} €/kWh)")
ax.set_xlabel("Vuosi")
ax.set_ylabel("Kustannus (€)")
ax.set_title("Lämmityskustannukset 50 vuoden ajalla")
ax.legend()
ax.grid(True)
st.pyplot(fig, use_container_width=True)

# ---------- NPV ----------

st.markdown("### Nettonykyarvot (NPV)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Kaukolämpö", f"{npv(kl, diskontto):,.0f} €")
col2.metric(f"Maalämpö A ({hinta1:.2f})", f"{npv(ml1, diskontto):,.0f} €")
col3.metric(f"Maalämpö B ({hinta2:.2f})", f"{npv(ml2, diskontto):,.0f} €")
col4.metric(f"Maalämpö C ({hinta3:.2f})", f"{npv(ml3, diskontto):,.0f} €")

# ---------- VASTIKETAULUKKO ----------

st.markdown("### Vastikkeet €/m²/v valituissa vuosissa")

rivit = list(range(1, 11)) + list(range(15, 51, 5))
df = pd.DataFrame({
    "Vuosi": rivit,
    "Kaukolämpö": [kl[v - 1] / neliot for v in rivit],
    f"Maalämpö A ({hinta1:.2f})": [ml1[v - 1] / neliot for v in rivit],
    f"Maalämpö B ({hinta2:.2f})": [ml2[v - 1] / neliot for v in rivit],
    f"Maalämpö C ({hinta3:.2f})": [ml3[v - 1] / neliot for v in rivit],
}).set_index("Vuosi")
st.dataframe(df.style.format("{:.2f}"), use_container_width=True)

# ---------- ENSIMMÄISEN VUODEN VASTIKKEET ----------

def vastike(kust):
    return kust[0] / neliot, kust[0] / neliot / 12

k_v, k_kk = vastike(kl)
m1_v, m1_kk = vastike(ml1)
m2_v, m2_kk = vastike(ml2)
m3_v, m3_kk = vastike(ml3)

st.markdown("### Ensimmäisen vuoden vastikkeet per m²")
st.write(f"**Kaukolämpö:** {k_v:.2f} €/v | {k_kk:.2f} €/kk")
st.write(f"**Maalämpö A ({hinta1:.2f} €/kWh):** {m1_v:.2f} €/v | {m1_kk:.2f} €/kk")
st.write(f"**Maalämpö B ({hinta2:.2f} €/kWh):** {m2_v:.2f} €/v | {m2_kk:.2f} €/kk")
st.write(f"**Maalämpö C ({hinta3:.2f} €/kWh):** {m3_v:.2f} €/v | {m3_kk:.2f} €/kk")

# ---------- TAKAISINMAKSUAIKA ----------

st.markdown("### Takaisinmaksuaika (investoinnin takaisinmaksu)")

pb1 = takaisinmaksuaika_investointi(investointi, kl, ml1)
pb2 = takaisinmaksuaika_investointi(investointi, kl, ml2)
pb3 = takaisinmaksuaika_investointi(investointi, kl, ml3)

def f(v): return f"{v} vuotta" if v else "ei 50 vuodessa"

st.write(f"**Maalämpö A ({hinta1:.2f} €/kWh):** {f(pb1)}")
st.write(f"**Maalämpö B ({hinta2:.2f} €/kWh):** {f(pb2)}")
st.write(f"**Maalämpö C ({hinta3:.2f} €/kWh):** {f(pb3)}")
