import re
import requests
import streamlit as st
import deepl
from ingredients import CATEGORIES

SPOON = "https://api.spoonacular.com/recipes"
SPOON_KEY = st.secrets["SPOON_KEY"]
traducteur = deepl.DeepLClient(st.secrets["DEEPL_KEY"])

st.set_page_config(page_title="Qu'est-ce que je mange ?", page_icon="🍳", layout="wide")


@st.cache_data
def traduire_liste(textes, cible):
    textes = list(textes)
    if not textes:
        return []
    return [r.text for r in traducteur.translate_text(textes, target_lang=cible)]


@st.cache_data
def chercher_recettes(ingredients):
    params = {
        "ingredients": ",".join(ingredients),
        "number": 15,
        "ranking": 2,
        "ignorePantry": True,
        "apiKey": SPOON_KEY,
    }
    return requests.get(f"{SPOON}/findByIngredients", params=params).json()


@st.cache_data
def details_recette(id_recette):
    return requests.get(f"{SPOON}/{id_recette}/information", params={"apiKey": SPOON_KEY}).json()


st.title("🍳 Qu'est-ce que je mange ?")

# ---------- Sélection du frigo ----------
st.subheader("🧊 Mon frigo")
frigo = []
for categorie, produits in CATEGORIES.items():
    with st.expander(categorie):
        colonnes = st.columns(6)
        for index, (nom_fr, nom_en) in enumerate(produits):
            with colonnes[index % 6]:
                st.image(f"https://www.themealdb.com/images/ingredients/{nom_en}-Small.png", width=70)
                if st.checkbox(nom_fr, key=nom_en):
                    frigo.append(nom_en.lower())

frigo = tuple(frigo)
if frigo:
    st.caption(f"{len(frigo)} ingrédient(s) sélectionné(s)")

# ---------- Recherche ----------
if st.button("Trouver des recettes", type="primary", disabled=not frigo):
    st.session_state["recettes"] = chercher_recettes(frigo)

if "recettes" in st.session_state:
    recettes = st.session_state["recettes"]
    if isinstance(recettes, dict):
        st.error(f"Erreur Spoonacular : {recettes.get('message')}")
    elif not recettes:
        st.warning("Aucune recette trouvée, essaie d'autres ingrédients.")
    else:
        titres_fr = traduire_liste(tuple(r["title"] for r in recettes), "FR")
        options = {
            f"{titre} (il manque {r['missedIngredientCount']} ingrédient(s))": (r["id"], titre)
            for titre, r in zip(titres_fr, recettes)
        }
        choix = st.selectbox("Choisis une recette", list(options))
        id_recette, titre_fr = options[choix]
        recette = details_recette(id_recette)

        st.header(titre_fr)
        col_image, col_ingredients = st.columns(2)

        with col_image:
            if recette.get("image"):
                st.image(recette["image"], use_container_width=True)
            st.caption(f"⏱️ {recette.get('readyInMinutes', '?')} min · 🍽️ {recette.get('servings', '?')} portions")

        ingredients = recette.get("extendedIngredients", [])
        lignes = [ing["original"] for ing in ingredients]
        instructions = re.sub(r"<[^>]+>", " ", recette.get("instructions") or "No instructions.")
        tout = traduire_liste(tuple(lignes + [instructions]), "FR")
        lignes_fr, instructions_fr = tout[:-1], tout[-1]

        with col_ingredients:
            st.subheader("🥕 Ingrédients")
            manquants = []
            for ing, ligne_fr in zip(ingredients, lignes_fr):
                nom = ing["name"].lower()
                if any(f in nom or nom in f for f in frigo):
                    st.write(f"✅ {ligne_fr}")
                else:
                    st.write(f"❌ {ligne_fr}")
                    manquants.append(ligne_fr)

            st.subheader("🛒 Liste de courses")
            if manquants:
                for m in manquants:
                    st.write("-", m)
            else:
                st.success("Tu as tout ce qu'il faut !")

        st.subheader("📖 Instructions")
        st.write(instructions_fr)