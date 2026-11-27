# 🍳 Qu'est-ce que je mange ?

Une app Python qui propose des recettes selon ce qu'il y a dans ton frigo, avec la liste de courses des ingrédients manquants.

## Fonctionnalités
- Sélection des ingrédients par catégories, avec photos
- Plus de 5 000 recettes via l'API Spoonacular
- Traduction en français avec DeepL
- Liste de courses automatique

## Installation
1. `pip install -r requirements.txt`
2. Crée `.streamlit/secrets.toml` avec tes clés :
   DEEPL_KEY = "..."
   SPOON_KEY = "..."
3. `streamlit run app.py`