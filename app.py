import streamlit as st
import json
import os
from datetime import datetime

FITXER_DADES = 'dades_inventari.json'

# --- Lògica de dades ---
def carregar_inventari():
    if os.path.exists(FITXER_DADES):
        try:
            with open(FITXER_DADES, 'r') as f:
                dades = json.load(f)
                if "Llista_Manual" not in dades: dades["Llista_Manual"] = []
                return dades
        except: return {"Llista_Manual": []}
    return {"Llista_Manual": []}

def desar_inventari(inventari):
    with open(FITXER_DADES, 'w') as f:
        json.dump(inventari, f, indent=4)

# --- Interfície d'usuari ---
st.set_page_config(page_title="El meu Inventari", page_icon="📦")
st.title("📦 Gestor d'Inventari")

inv = carregar_inventari()

# Menú lateral per a la navegació (molt còmode al mòbil)
menu = st.sidebar.radio("Menú", ["🏠 Inici", "🔍 Veure i Editar", "➕ Nou Producte", "📝 Notes Compra", "🛒 Llista Final"])

if menu == "🏠 Inici":
    st.subheader("Benvingut/da!")
    st.write("Selecciona una opció al menú lateral per començar.")
    
    # Resum ràpid
    total_prods = sum(len(v) for k, v in inv.items() if k != "Llista_Manual")
    st.metric("Productes en estoc", total_prods)

elif menu == "➕ Nou Producte":
    st.subheader("Afegir producte")
    with st.form("nou_prod"):
        ubi = st.text_input("Ubicació (ex: Cuina)").capitalize()
        nom = st.text_input("Nom del producte").capitalize()
        col1, col2 = st.columns(2)
        with col1:
            q = st.number_input("Quantitat", min_value=0, value=1)
        with col2:
            m = st.number_input("Estoc mínim", min_value=0, value=0)
        cad = st.text_input("Caducitat (opcional)")
        
        enviat = st.form_submit_button("Desar Producte")
        if enviat and ubi and nom:
            if ubi not in inv: inv[ubi] = {}
            inv[ubi][nom] = {'quantitat': q, 'caducitat': cad, 'estoc_minim': m}
            desar_inventari(inv)
            st.success(f"{nom} afegit!")

elif menu == "🔍 Veure i Editar":
    st.subheader("Inventari actual")
    for ubi, prods in inv.items():
        if ubi == "Llista_Manual": continue
        with st.expander(f"📍 {ubi.upper()}"):
            for nom, dades in prods.items():
                st.write(f"**{nom}**")
                col1, col2, col3 = st.columns([2, 2, 1])
                nova_q = col1.number_input(f"Qt: {nom}", value=dades['quantitat'], key=f"q_{ubi}_{nom}")
                nova_cad = col2.text_input(f"Cad: {nom}", value=dades.get('caducitat', ''), key=f"c_{ubi}_{nom}")
                
                if st.button("Actualitzar", key=f"b_{ubi}_{nom}"):
                    inv[ubi][nom]['quantitat'] = nova_q
                    inv[ubi][nom]['caducitat'] = nova_cad
                    desar_inventari(inv)
                    st.rerun()

elif menu == "📝 Notes Compra":
    st.subheader("Coses que falten (Manual)")
    nou_item = st.text_input("Què vols afegir?")
    if st.button("Afegir a la llista"):
        if nou_item:
            inv["Llista_Manual"].append(nou_item.capitalize())
            desar_inventari(inv)
            st.rerun()
    
    for i, item in enumerate(inv["Llista_Manual"]):
        col1, col2 = st.columns([4, 1])
        col1.write(f"• {item}")
        if col2.button("🗑️", key=f"del_{i}"):
            inv["Llista_Manual"].pop(i)
            desar_inventari(inv)
            st.rerun()

elif menu == "🛒 Llista Final":
    st.subheader("🛒 Llista de la Compra")
    falta = False
    
    st.write("### ⚠️ Per reposar")
    for ubi, prods in inv.items():
        if ubi == "Llista_Manual": continue
        for nom, dades in prods.items():
            if dades.get('estoc_minim') is not None and dades['quantitat'] <= dades['estoc_minim']:
                st.warning(f"{nom} ({ubi}) - En queden: {dades['quantitat']}")
                falta = True
                
    st.write("### 📌 Notes manuals")
    for item in inv.get("Llista_Manual", []):
        st.info(item)
        falta = True
    
    if not falta:
        st.success("Tens de tot!")