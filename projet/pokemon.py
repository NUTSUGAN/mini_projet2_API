"""Fonctions pour consulter, comparer et faire combattre des Pokémon."""
import asyncio
import re
from projet.client import BASE_URL, ErreurAPI


def identifiant(valeur):
    texte = str(valeur).strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", texte):
        raise ValueError("Saisis un identifiant ou un nom PokéAPI valide en anglais, par exemple pikachu.")
    return texte


async def pokemon(client, nom):
    data = await client.get(f"{BASE_URL}/pokemon/{identifiant(nom)}/")
    stats = {element["stat"]["name"]: element["base_stat"] for element in data["stats"]}
    return {"id": data["id"], "nom": data["name"], "types": [t["type"]["name"] for t in data["types"]],
            "stats": stats, "image": data["sprites"]["front_default"]}


def comparer(a, b):
    def gagnant(stat):
        premier, second = a["stats"][stat], b["stats"][stat]
        return "Égalité" if premier == second else (a["nom"] if premier > second else b["nom"])
    return {"hp": gagnant("hp"), "attack": gagnant("attack")}


def combat(a, b):
    """Cinq échanges simultanés, sans KO ; dégâts minimums de 1 par tour."""
    degats_a = max(1, a["stats"]["attack"] - b["stats"]["defense"] // 2)
    degats_b = max(1, b["stats"]["attack"] - a["stats"]["defense"] // 2)
    total_a, total_b = degats_a * 5, degats_b * 5
    gagnant = "Égalité" if total_a == total_b else (a["nom"] if total_a > total_b else b["nom"])
    return {"degats_a": degats_a, "degats_b": degats_b, "total_a": total_a, "total_b": total_b, "gagnant": gagnant}


async def statistiques_type(client, nom_type):
    data = await client.get(f"{BASE_URL}/type/{identifiant(nom_type)}/")
    noms = [element["pokemon"]["name"] for element in data["pokemon"]]
    if not noms:
        return {"type": data["name"], "nombre": 0, "moyenne_hp": None}
    # File bornée et cinq workers : pas de tâche par Pokémon.
    file = asyncio.Queue(maxsize=10)
    resultats = []
    async def worker():
        while True:
            nom = await file.get()
            try:
                if nom is None:
                    return
                resultats.append((await pokemon(client, nom))["stats"]["hp"])
            finally:
                file.task_done()
    workers = [asyncio.create_task(worker()) for _ in range(5)]
    async def produire():
        for nom in noms:
            await file.put(nom)
        for _ in workers:
            await file.put(None)
    producteur = asyncio.create_task(produire())
    try:
        await asyncio.gather(producteur, *workers)
    except BaseException:
        for tache in [producteur, *workers]:
            tache.cancel()
        await asyncio.gather(producteur, *workers, return_exceptions=True)
        raise
    return {"type": data["name"], "nombre": len(noms), "moyenne_hp": sum(resultats) / len(resultats)}
