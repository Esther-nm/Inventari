import streamlit as st
import json
import os
from datetime import datetime, timedelta

FITXER_DADES = 'dades_inventari.json'

# --- Lògica de dades ---
def carregar_inventari():
    if os.path.exists(FITXER_DADES):
        try:
            with open(FITXER_DADES, 'r', encoding='utf-8') as f:
                dades = json.load(f)
                if "Llista_Manual" not in dades: dades["Llista_Manual"] = []
                return dades
        except: return {"Llista_Manual": []}
    return {"Llista_Manual": []}

def desar_inventari(inventari):
    with open(FITXER_DADES, 'w', encoding='utf-8') as f:
        json.dump(inventari, f, indent=4)

# --- Configuració ---
st.set_page_config(page_title="El meu Inventari", page_icon="🍎")
st.title("🍎 Gestor Intel·ligent")

inv = carregar_inventari()

menu = st.sidebar.radio("Menú", ["🏠 Inici", "🔍 Estoc i Edició", "➕ Nou Producte", "📝 Notes Compra", "🛒 Llista i Reposició", "⌛ Caducitat"])

# --- SECCIÓ 1: INICI ---
if menu == "🏠 Inici":
    st.subheader("Estat de la llar")
    total_prods = sum(len(v) for k, v in inv.items() if k != "Llista_Manual")
    st.metric("Productes registrats", total_prods)
    
    # Alerta ràpida de caducitat a la home
    avui = datetime.now()
    caducats = 0
    for ubi, prods in inv.items():
        if ubi == "Llista_Manual": continue
        for nom, d in prods.items():
            if d.get('caducitat'):
                try:
                    data_c = datetime.strptime(d['caducitat'], "%d-%m-%y")
                    if data_c < avui: caducats += 1
                except: pass
    if caducats > 0:
        st.error(f"⚠️ Atenció: Tens {caducats} productes caducats!")

# --- SECCIÓ 2: ESTOC I EDICIÓ ---
elif menu == "🔍 Estoc i Edició":
    st.subheader("Consulta per Ubicacions")
    for ubi in sorted([k for k in inv.keys() if k != "Llista_Manual"]):
        with st.expander(f"📍 {ubi.upper()}"):
            for nom in sorted(inv[ubi].keys()):
                d = inv[ubi][nom]
                col1, col2, col3 = st.columns([2, 2, 1])
                nova_q = col1.number_input(f"Qt: {nom}", value=d['quantitat'], key=f"q_{ubi}_{nom}")
                nova_cad = col2.text_input(f"Cad (dd-mm-yy): {nom}", value=d.get('caducitat', ''), key=f"c_{ubi}_{nom}")
                if col3.button("💾", key=f"b_{ubi}_{nom}"):
                    inv[ubi][nom].update({'quantitat': nova_q, 'caducitat': nova_cad})
                    desar_inventari(inv)
                    st.toast(f"{nom} actualitzat")

# --- SECCIÓ 3: NOU PRODUCTE ---
elif menu == "➕ Nou Producte":
    with st.form("nou", clear_on_submit=True):
        ubi = st.text_input("Ubicació").strip().capitalize()
        nom = st.text_input("Producte").strip().capitalize()
        q = st.number_input("Quantitat", min_value=0, value=1)
        m = st.number_input("Estoc mínim", min_value=0, value=0)
        cad = st.text_input("Caducitat (dd-mm-yy)")
        if st.form_submit_button("Desar") and ubi and nom:
            if ubi not in inv: inv[ubi] = {}
            inv[ubi][nom] = {'quantitat': q, 'caducitat': cad, 'estoc_minim': m}
            desar_inventari(inv)
            st.success("Afegit!")

# --- SECCIÓ 4: NOTES COMPRA ---
elif menu == "📝 Notes Compra":
    st.subheader("Coses extres")
    def af_n():
        if st.session_state.nn:
            inv["Llista_Manual"].append(st.session_state.nn.strip().capitalize())
            desar_inventari(inv)
            st.session_state.nn = ""
    st.text_input("Afegir nota:", key="nn", on_change=af_n)
    for i, item in enumerate(inv["Llista_Manual"]):
        c1, c2 = st.columns([4, 1])
        c1.write(f"• {item}")
        if c2.button("🗑️", key=f"d_{i}"):
            inv["Llista_Manual"].pop(i)
            desar_inventari(inv)
            st.rerun()

# --- SECCIÓ 5: LLISTA I REPOSICIÓ (AMB QUANTITAT EXACTA) ---
elif menu == "🛒 Llista i Reposició":
    st.subheader("🛒 Al Supermercat")
    comprat_auto = {} # Guardarem quantitat nova
    comprat_manual = []

    st.markdown("### ⚠️ Per Reposar")
    for ubi in sorted([k for k in inv.keys() if k != "Llista_Manual"]):
        for nom, d in inv[ubi].items():
            if d['quantitat'] <= d.get('estoc_minim', 0):
                col1, col2 = st.columns([3, 2])
                if col1.checkbox(f"{nom} ({ubi})", key=f"cp_{nom}_{ubi}"):
                    val = col2.number_input(f"Quants n'has comprat?", min_value=1, value=1, key=f"num_{nom}_{ubi}")
                    comprat_auto[(ubi, nom)] = val

    st.markdown("### 📌 Notes Manuals")
    for i, item in enumerate(inv["Llista_Manual"]):
        if st.checkbox(item, key=f"cm_{i}"): comprat_manual.append(item)

    if comprat_auto or comprat_manual:
        if st.button("🚀 Actualitzar Estoc Ara", use_container_width=True):
            for (u, n), q_nova in comprat_auto.items():
                inv[u][n]['quantitat'] += q_nova
            for item in comprat_manual:
                inv["Llista_Manual"].remove(item)
            desar_inventari(inv)
            st.balloons()
            st.rerun()

# --- SECCIÓ 6: CADUCITAT ---
elif menu == "⌛ Caducitat":
    st.subheader("⌛ Control de Caducitat")
    avui = datetime.now()
    proxim = avui + timedelta(days=7)
    
    trobat = False
    for ubi in sorted([k for k in inv.keys() if k != "Llista_Manual"]):
        for nom, d in inv[ubi].items():
            if d.get('caducitat'):
                try:
                    data_c = datetime.strptime(d['caducitat'], "%d-%m-%y")
                    if data_c < avui:
                        st.error(f"❌ **CADUCAT**: {nom} en {ubi} ({d['caducitat']})")
                        trobat = True
                    elif data_c <= proxim:
                        st.warning(f"⚠️ **AVIAT**: {nom} en {ubi} (Caduca: {d['caducitat']})")
                        trobat = True
                except: pass
    if not trobat:
        st.success("No hi ha cap producte caducat o a punt de caducar!")
