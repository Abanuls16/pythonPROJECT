import requests

API = "https://www.themealdb.com/api/json/v1/1"

saisie = input("Qu'as-tu dans ton frigo ? (en anglais, séparé par des virgules) : ")
frigo = [i.strip().lower() for i in saisie.split(",")]

compteur = {}  # id -> nombre d'ingrédients du frigo
noms = {}      # id -> nom de la recette

for ingredient in frigo:
    recettes = requests.get(f"{API}/filter.php?i={ingredient}").json()["meals"] or []
    for r in recettes:
        compteur[r["idMeal"]] = compteur.get(r["idMeal"], 0) + 1
        noms[r["idMeal"]] = r["strMeal"]

classement = sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:10]

print("\nMeilleures idées de repas :")
for numero, (id_recette, nb) in enumerate(classement, start=1):
    print(f" {numero}. {noms[id_recette]} ({nb}/{len(frigo)})")

choix = int(input("\nQuel numéro veux-tu cuisiner ? "))
id_choisi = classement[choix - 1][0]

recette = requests.get(f"{API}/lookup.php?i={id_choisi}").json()["meals"][0]

print(f"\n=== {recette['strMeal']} ===")
manquants = []
for n in range(1, 21):
    ing = (recette[f"strIngredient{n}"] or "").strip()
    dose = (recette[f"strMeasure{n}"] or "").strip()
    if ing:
        if ing.lower() in frigo:
            print(f" ✅ {ing} ({dose})")
        else:
            print(f" ❌ {ing} ({dose})")
            manquants.append(f"{ing} ({dose})")

print("\n🛒 Liste de courses :")
for m in manquants:
    print(" -", m)

print("\n📖 Instructions :\n", recette["strInstructions"])