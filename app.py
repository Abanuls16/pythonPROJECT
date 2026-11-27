import re
import requests
import streamlit as st
import deepl
from ingredients import CATEGORIES
from pathlib import Path

st.set_page_config(page_title="Qu'est-ce que je mange ?", page_icon="🍳", layout="wide")
st.html(Path("style.css"))  # charge le fichier de style

SPOON = "https://api.spoonacular.com/recipes"
SPOON_KEY = st.secrets["SPOON_KEY"]
traducteur = deepl.DeepLClient(st.secrets["DEEPL_KEY"])


# ---------- Fonctions API ----------
@st.cache_data
def traduire_liste(textes, cible):
    textes = list(textes)
    if not textes:
        return []
    return [r.text for r in traducteur.translate_text(textes, target_lang=cible)]


@st.cache_data
def chercher_recettes(ingredients):
    params = {"ingredients": ",".join(ingredients), "number": 12, "ranking": 2,
              "ignorePantry": True, "apiKey": SPOON_KEY}
    return requests.get(f"{SPOON}/findByIngredients", params=params).json()


@st.cache_data
def details_recette(id_recette):
    return requests.get(f"{SPOON}/{id_recette}/information", params={"apiKey": SPOON_KEY}).json()


# ---------- En-tête ----------
st.markdown("""
<div class="hero">
  <h1>🍳 Qu'est-ce que je mange ?</h1>
  <p>Coche ce que tu as dans ton frigo, on s'occupe du reste.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sélection du frigo ----------
frigo, frigo_fr = [], []
for categorie, produits in CATEGORIES.items():
    with st.expander(categorie):
        colonnes = st.columns(6)
        for index, (nom_fr, nom_en) in enumerate(produits):
            with colonnes[index % 6]:
                st.image(f"https://www.themealdb.com/images/ingredients/{nom_en}-Small.png", width=64)
                if st.checkbox(nom_fr, key=nom_en):
                    frigo.append(nom_en.lower())
                    frigo_fr.append(nom_fr)
frigo = tuple(frigo)

# ---------- Barre latérale : mon frigo ----------
with st.sidebar:
    st.header("🧊 Mon frigo")
    if frigo_fr:
        st.markdown("".join(f'<span class="puce">{n}</span>' for n in frigo_fr), unsafe_allow_html=True)
        st.caption(f"{len(frigo)} ingrédient(s)")
    else:
        st.info("Ouvre une catégorie et coche tes ingrédients.")
    if st.button("🔍 Trouver des recettes", type="primary", disabled=not frigo, use_container_width=True):
        st.session_state["recettes"] = chercher_recettes(frigo)
        st.session_state.pop("choisie", None)

# ---------- Résultats en cartes ----------
recettes = st.session_state.get("recettes")
if isinstance(recettes, dict):
    st.error(f"Erreur Spoonacular : {recettes.get('message')}")
elif recettes == []:
    st.warning("Aucune recette trouvée, essaie d'autres ingrédients.")
elif recettes:
    st.subheader("🍽️ Idées de repas")
    titres_fr = traduire_liste(tuple(r["title"] for r in recettes), "FR")
    colonnes = st.columns(3)
    for index, (r, titre) in enumerate(zip(recettes, titres_fr)):
        manque = r["missedIngredientCount"]
        badge = ('<span class="badge ok">✅ Tu as tout !</span>' if manque == 0
                 else f'<span class="badge manque">🛒 Il manque {manque} ingrédient(s)</span>')
        with colonnes[index % 3]:
            with st.container(border=True):
                st.image(r["image"], use_container_width=True)
                st.markdown(f'<div class="titre-carte">{titre}</div>{badge}', unsafe_allow_html=True)
                if st.button("Voir la recette", key=f"voir_{r['id']}", use_container_width=True):
                    st.session_state["choisie"] = (r["id"], titre)

# ---------- Détail de la recette ----------
if "choisie" in st.session_state:
    id_recette, titre_fr = st.session_state["choisie"]
    recette = details_recette(id_recette)
    st.divider()
    st.header(f"👨‍🍳 {titre_fr}")

    ingredients = recette.get("extendedIngredients", [])
    lignes = [ing["original"] for ing in ingredients]
    instructions = re.sub(r"<[^>]+>", " ", recette.get("instructions") or "No instructions.")
    tout = traduire_liste(tuple(lignes + [instructions]), "FR")
    lignes_fr, instructions_fr = tout[:-1], tout[-1]

    possedes, manquants = [], []
    for ing, ligne_fr in zip(ingredients, lignes_fr):
        nom = ing["name"].lower()
        (possedes if any(f in nom or nom in f for f in frigo) else manquants).append(ligne_fr)

    col_image, col_infos = st.columns([1, 1])
    with col_image:
        if recette.get("image"):
            st.image(recette["image"], use_container_width=True)
    with col_infos:
        m1, m2, m3 = st.columns(3)
        m1.metric("⏱️ Temps", f"{recette.get('readyInMinutes', '?')} min")
        m2.metric("🍽️ Portions", recette.get("servings", "?"))
        m3.metric("✅ Tu as", f"{len(possedes)}/{len(ingredients)}")
        st.progress(len(possedes) / max(len(ingredients), 1))

    onglet1, onglet2, onglet3 = st.tabs(["🥕 Ingrédients", "🛒 Liste de courses", "📖 Instructions"])
    with onglet1:
        for l in possedes:
            st.markdown(f"✅ {l}")
        for l in manquants:
            st.markdown(f"❌ {l}")
    with onglet2:
        if manquants:
            for l in manquants:
                st.checkbox(l, key=f"course_{id_recette}_{l}")
        else:
            st.success("Tu as tout ce qu'il faut ! 🎉")
    with onglet3:
        st.write(instructions_fr)