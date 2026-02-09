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

# --- Interfície ---
st.set_page_config(page_title="El meu Inventari", page_icon="📦")
st.title("📦 Gestor d'Inventari")

inv = carregar_inventari()

menu = st.sidebar.radio("Menú", ["🏠 Inici", "🔍 Veure i Editar", "➕ Nou Producte", "📝 Notes Compra", "🛒 Llista Final"])

if menu == "🏠 Inici":
    st.subheader("Benvingut/da!")
    total_prods = sum(len(v) for k, v in inv.items() if k != "Llista_Manual")
    st.metric("Productes en estoc", total_prods)
    st.write("Consell: Fes servir el menú lateral per moure't ràpidament.")

elif menu == "➕ Nou Producte":
    st.subheader("Afegir producte")
    
    # Fem servir un formulari i li posem un nom (clear_on_submit fa la màgia)
    with st.form("formulari_nou", clear_on_submit=True):
        ubi = st.text_input("Ubicació (ex: Cuina)").strip().capitalize()
        nom = st.text_input("Nom del producte").strip().capitalize()
        col1, col2 = st.columns(2)
        with col1:
            q = st.number_input("Quantitat", min_value=0, value=1)
        with col2:
            m = st.number_input("Estoc mínim (avís)", min_value=0, value=0)
        cad = st.text_input("Caducitat (opcional)")
        
        enviat = st.form_submit_button("Desar Producte")
        
        if enviat:
            if ubi and nom:
                if ubi not in inv: inv[ubi] = {}
                inv[ubi][nom] = {'quantitat': q, 'caducitat': cad, 'estoc_minim': m}
                desar_inventari(inv)
                st.success(f"✅ {nom} desar a {ubi}!")
                # No cal fer rerun, clear_on_submit ja ha netejat els camps
            else:
                st.error("Si us plau, omple el nom i la ubicació.")

elif menu == "🔍 Veure i Editar":
    st.subheader("Inventari (Ordre Alfabètic)")
    
    # Ordenem les ubicacions alfabèticament
    ubicacions_ordenades = sorted([k for k in inv.keys() if k != "Llista_Manual"])
    
    for ubi in ubicacions_ordenades:
        prods = inv[ubi]
        with st.expander(f"📍 {ubi.upper()}"):
            # Ordenem els productes de cada ubicació alfabèticament
            productes_ordenats = sorted(prods.keys())
            
            for nom in productes_ordenats:
                dades = prods[nom]
                st.write(f"**{nom}**")
                col1, col2, col3 = st.columns([2, 2, 1])
                
                nova_q = col1.number_input(f"Qt", value=dades['quantitat'], key=f"q_{ubi}_{nom}")
                nova_cad = col2.text_input(f"Cad", value=dades.get('caducitat', ''), key=f"c_{ubi}_{nom}")
                
                if col3.button("💾", key=f"b_{ubi}_{nom}"):
                    inv[ubi][nom]['quantitat'] = nova_q
                    inv[ubi][nom]['caducitat'] = nova_cad
                    desar_inventari(inv)
                    st.toast(f"Actualitzat {nom}") # Missatge discret al peu

elif menu == "📝 Notes Compra":
    st.subheader("Llista Manual")
    
    # Netejar l'input de la nota manual després d'afegir
    if 'text_nota' not in st.session_state:
        st.session_state.text_nota = ""

    def afegir_nota():
        item = st.session_state.nova_nota.strip().capitalize()
        if item:
            inv["Llista_Manual"].append(item)
            desar_inventari(inv)
            st.session_state.nova_nota = "" # Neteja el camp

    st.text_input("Què vols afegir?", key="nova_nota", on_change=afegir_nota)
    st.caption("Prem 'Enter' per afegir a la llista ràpidament")
    
    st.divider()
    
    # Mostrem la llista manual (també ordenada si vols)
    llista_m = inv.get("Llista_Manual", [])
    for i, item in enumerate(llista_m):
        col1, col2 = st.columns([4, 1])
        col1.write(f"• {item}")
        if col2.button("🗑️", key=f"del_{i}_{item}"):
            inv["Llista_Manual"].pop(i)
            desar_inventari(inv)
            st.rerun()

elif menu == "🛒 Llista Final":
    st.subheader("🛒 Llista de la Compra")
    falta = False
    
    st.write("### ⚠️ Baix Estoc")
    # També ordenem aquí per trobar les coses millor al súper
    ubicacions_ordenades = sorted([k for k in inv.keys() if k != "Llista_Manual"])
    for ubi in ubicacions_ordenades:
        prods = inv[ubi]
        prods_ordenats = sorted(prods.keys())
        for nom in prods_ordenats:
            dades = prods[nom]
            min_r = dades.get('estoc_minim', 0)
            if dades['quantitat'] <= min_r:
                st.warning(f"**{nom}** ({ubi}) - Queden: {dades['quantitat']} (Mín: {min_r})")
                falta = True
                
    st.write("### 📌 Notes Manuals")
    for item in sorted(inv.get("Llista_Manual", [])):
        st.info(item)
        falta = True
    
    if not falta:
        st.success("Tot correcte! No falta res.")
