import streamlit as st
import json
import os

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

# --- Configuració i Estil ---
st.set_page_config(page_title="El meu Inventari", page_icon="📦")
st.title("📦 Gestor d'Inventari")

inv = carregar_inventari()

# Menú lateral
menu = st.sidebar.radio("Menú", ["🏠 Inici", "🔍 Veure i Editar", "➕ Nou Producte", "📝 Notes Compra", "🛒 Llista Final"])

# --- SECCIÓ 1: INICI ---
if menu == "🏠 Inici":
    st.subheader("Benvingut/da!")
    total_prods = sum(len(v) for k, v in inv.items() if k != "Llista_Manual")
    st.metric("Productes totals en estoc", total_prods)
    st.info("Pots accedir a les diferents seccions des del menú lateral.")

# --- SECCIÓ 2: NOU PRODUCTE ---
elif menu == "➕ Nou Producte":
    st.subheader("Afegir producte")
    with st.form("formulari_nou", clear_on_submit=True):
        ubi = st.text_input("Ubicació (ex: Cuina, Rebost)").strip().capitalize()
        nom = st.text_input("Nom del producte").strip().capitalize()
        col1, col2 = st.columns(2)
        with col1:
            q = st.number_input("Quantitat actual", min_value=0, value=1)
        with col2:
            m = st.number_input("Estoc mínim per avís", min_value=0, value=0)
        cad = st.text_input("Data caducitat (opcional)")
        
        enviat = st.form_submit_button("Desar a l'Inventari")
        if enviat and ubi and nom:
            if ubi not in inv: inv[ubi] = {}
            inv[ubi][nom] = {'quantitat': q, 'caducitat': cad, 'estoc_minim': m}
            desar_inventari(inv)
            st.success(f"✅ {nom} afegit correctament!")

# --- SECCIÓ 3: VEURE I EDITAR ---
elif menu == "🔍 Veure i Editar":
    st.subheader("Consulta per Ubicacions")
    ubicacions_ordenades = sorted([k for k in inv.keys() if k != "Llista_Manual"])
    
    for ubi in ubicacions_ordenades:
        with st.expander(f"📍 {ubi.upper()}"):
            productes_ordenats = sorted(inv[ubi].keys())
            for nom in productes_ordenats:
                dades = inv[ubi][nom]
                st.write(f"**{nom}**")
                col1, col2, col3 = st.columns([2, 2, 1])
                
                nova_q = col1.number_input(f"Qt", value=dades['quantitat'], key=f"q_{ubi}_{nom}", label_visibility="collapsed")
                nova_cad = col2.text_input(f"Cad", value=dades.get('caducitat', ''), key=f"c_{ubi}_{nom}", label_visibility="collapsed")
                
                if col3.button("💾", key=f"b_{ubi}_{nom}"):
                    inv[ubi][nom]['quantitat'] = nova_q
                    inv[ubi][nom]['caducitat'] = nova_cad
                    desar_inventari(inv)
                    st.toast(f"Actualitzat: {nom}")

# --- SECCIÓ 4: NOTES MANUALS ---
elif menu == "📝 Notes Compra":
    st.subheader("Coses extres per comprar")
    
    def afegir_nota():
        item = st.session_state.nova_nota.strip().capitalize()
        if item:
            inv["Llista_Manual"].append(item)
            desar_inventari(inv)
            st.session_state.nova_nota = ""

    st.text_input("Escriu i prem Enter:", key="nova_nota", on_change=afegir_nota)
    
    st.divider()
    for i, item in enumerate(inv["Llista_Manual"]):
        col1, col2 = st.columns([4, 1])
        col1.write(f"• {item}")
        if col2.button("🗑️", key=f"del_{i}_{item}"):
            inv["Llista_Manual"].pop(i)
            desar_inventari(inv)
            st.rerun()

# --- SECCIÓ 5: LLISTA FINAL (LA DEL SÚPER) ---
elif menu == "🛒 Llista Final":
    st.subheader("🛒 Check-list per anar a comprar")
    st.caption("Marca els productes a mesura que els posis al carret.")
    
    falta_alguna_cosa = False
    
    # 1. Automàtic per estoc baix
    st.markdown("### ⚠️ Reposar (Estoc Baix)")
    ubi_ord = sorted([k for k in inv.keys() if k != "Llista_Manual"])
    for ubi in ubi_ord:
        for nom in sorted(inv[ubi].keys()):
            d = inv[ubi][nom]
            if d['quantitat'] <= d.get('estoc_minim', 0):
                st.checkbox(f"**{nom}** ({ubi}) - En queden: {d['quantitat']}", key=f"ch_auto_{nom}_{ubi}")
                falta_alguna_cosa = True

    st.divider()

    # 2. Manuals
    st.markdown("### 📌 Notes Manuals")
    notes = inv.get("Llista_Manual", [])
    if not notes and not falta_alguna_cosa:
        st.success("No tens res pendent de comprar!")
    else:
        for i, item in enumerate(sorted(notes)):
            st.checkbox(item, key=f"ch_man_{i}_{item}")
    
    # Botó especial al final per netejar la llista manual quan tornes a casa
    st.sidebar.divider()
    if st.sidebar.button("Buidar Notes Manuals"):
        inv["Llista_Manual"] = []
        desar_inventari(inv)
        st.rerun()
