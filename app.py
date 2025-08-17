# app.py — Lämmitysvaihtoehtojen vertailu PDF-raportilla

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import tempfile

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

def luo_pdf(kaavio, tbl_df, pb1, pb2, pb3, lainaosuus, syotteet):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Lämmitysvaihtoehtojen vertailuraportti", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Syötetyt arvot:", styles['Heading2']))
    for nimi, arvo in syotteet.items():
        elements.append(Paragraph(f"{nimi}: {arvo}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    kaavio.savefig(tmpfile.name, dpi=150, bbox_inches="tight")
    elements.append(Paragraph("Lämmityskustannukset 50 vuoden ajalta", styles['Heading2']))
    elements.append(Image(tmpfile.name, width=6*inch, height=3*inch))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Rahoitus- ja lämmitysvastikkeet €/m²/kk (5 v välein)", styles['Heading2']))
    taulu = [tbl_df.columns.to_list()] + tbl_df.reset_index().values.tolist()
    table = Table(taulu)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Investoinnin takaisinmaksuaika:", styles['Heading2']))
    f = lambda v: f"{v} vuotta" if v else "ei 50 vuodessa"
    elements.append(Paragraph(f"Maalämpö A: {f(pb1)}", styles['Normal']))
    elements.append(Paragraph(f"Maalämpö B: {f(pb2)}", styles['Normal']))
    elements.append(Paragraph(f"Maalämpö C: {f(pb3)}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(f"Lainaosuus: {lainaosuus:,.0f} €/m²", styles['Normal']))
    doc.build(elements)
    buffer.seek(0)
    return buffer
