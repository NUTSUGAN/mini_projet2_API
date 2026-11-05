"""Interface Streamlit du mini-projet PokéAPI."""
import asyncio
import httpx
import streamlit as st
from projet.client import ErreurAPI, PokeClient
from projet.pokemon import pokemon, comparer, combat, statistiques_type


async def executer(operation, *valeurs):
    async with httpx.AsyncClient() as http:
        client = PokeClient(http)
        if operation == "fiche":
            return await pokemon(client, valeurs[0])
        if operation == "type":
            return await statistiques_type(client, valeurs[0])
        return await asyncio.gather(*(pokemon(client, nom) for nom in valeurs))


def afficher_fiche(p):
    st.subheader(f"{p['nom'].capitalize()} — n° {p['id']}")
    if p["image"]:
        st.image(p["image"], width=120)
    st.write("Types :", ", ".join(p["types"]))
    noms = {"hp": "Points de vie", "attack": "Attaque", "defense": "Défense", "special-attack": "Attaque spéciale", "special-defense": "Défense spéciale", "speed": "Vitesse"}
    st.table({"Statistique": [noms.get(k, k) for k in p["stats"]], "Valeur": list(p["stats"].values())})


def executer_sans_erreur(operation, *valeurs):
    try:
        with st.spinner("Chargement des données PokéAPI..."):
            return asyncio.run(executer(operation, *valeurs))
    except (ErreurAPI, ValueError, httpx.HTTPError) as erreur:
        st.error(str(erreur))
        return None


st.title("Explorateur Pokémon")
st.caption("Données fournies par PokéAPI. Noms et types en anglais : pikachu, charizard, fire…")
fiche, comparaison, types, bataille = st.tabs(["Fiche Pokémon", "Comparaison", "Statistiques par type", "Combat"])
with fiche:
    with st.form("fiche"):
        nom = st.text_input("Nom ou identifiant", "pikachu")
        valider = st.form_submit_button("Rechercher")
    if valider:
        resultat = executer_sans_erreur("fiche", nom)
        if resultat:
            afficher_fiche(resultat)
with comparaison:
    with st.form("comparaison"):
        a = st.text_input("Premier Pokémon", "pikachu", key="compare_a")
        b = st.text_input("Deuxième Pokémon", "bulbasaur", key="compare_b")
        valider = st.form_submit_button("Comparer")
    if valider:
        resultat = executer_sans_erreur("comparaison", a, b)
        if resultat:
            premier, second = resultat
            afficher_fiche(premier)
            afficher_fiche(second)
            gagnants = comparer(premier, second)
            st.write("Meilleurs points de vie :", gagnants["hp"])
            st.write("Meilleure attaque :", gagnants["attack"])
with types:
    with st.form("type"):
        nom_type = st.text_input("Type en anglais", "fire")
        valider = st.form_submit_button("Calculer")
    if valider:
        resultat = executer_sans_erreur("type", nom_type)
        if resultat:
            st.write("Nombre de Pokémon et formes :", resultat["nombre"])
            st.write("Moyenne des points de vie :", f"{resultat['moyenne_hp']:.2f}" if resultat["moyenne_hp"] is not None else "Aucune donnée")
with bataille:
    with st.form("combat"):
        a = st.text_input("Premier Pokémon", "pikachu", key="combat_a")
        b = st.text_input("Deuxième Pokémon", "bulbasaur", key="combat_b")
        valider = st.form_submit_button("Simuler le combat")
    st.caption("Cinq échanges simultanés, sans KO : dégâts par tour = max(1, attaque − défense adverse // 2).")
    if valider:
        resultat = executer_sans_erreur("combat", a, b)
        if resultat:
            premier, second = resultat
            score = combat(premier, second)
            st.write(f"{premier['nom']} : {score['degats_a']} par tour, soit {score['total_a']} dégâts.")
            st.write(f"{second['nom']} : {score['degats_b']} par tour, soit {score['total_b']} dégâts.")
            st.subheader(f"Résultat : {score['gagnant']}")
