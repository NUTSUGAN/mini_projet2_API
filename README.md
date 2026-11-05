# Mini-projet 2 — PokéAPI

Application Python et Streamlit pour découvrir les statistiques des Pokémon, comparer deux Pokémon, étudier un type et simuler un combat. Les noms et les types doivent être saisis en anglais (par exemple `pikachu`, `bulbasaur`, `fire`). Aucun compte ni clé API n'est nécessaire.

## Installation et lancement

Dans PowerShell, depuis le dossier du projet :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ouvrir l'adresse affichée dans le navigateur. Pour les statistiques d'un type, le premier calcul peut prendre du temps : chaque Pokémon ou forme listé par PokéAPI nécessite une fiche. Le nombre et la moyenne incluent toutes les entrées renvoyées par l'API, y compris les formes alternatives. Une erreur interrompt le calcul pour éviter d'afficher une moyenne partielle.

## Fonctionnalités

- **Fiche** : nom ou identifiant, types et statistiques de base.
- **Comparaison** : affiche les deux fiches puis indique séparément le meilleur pour les PV et l'attaque, avec égalités possibles.
- **Type** : nombre d'entrées et moyenne de leurs PV de base.
- **Combat** : cinq échanges simultanés. À chaque tour, chaque Pokémon inflige `max(1, attaque - défense adverse // 2)`. Le plus grand total de dégâts gagne ; une égalité est possible. Cette simulation pédagogique n'applique ni KO, ni attaques, ni multiplicateurs de types des jeux Pokémon.

## Questions communes

- **Q1** : `projet/client.py` gère les erreurs HTTP et de connexion, avec quatre tentatives maximum pour les erreurs temporaires et respect de `Retry-After`.
- **Q2** : simulation locale avec `asyncio`, file bornée et nombre configurable de workers. Elle n'envoie aucune requête réelle aux trois routes de l'énoncé.
- **Q3** : réponses réussies en cache SQLite pendant une heure, avec limite de 1 000 entrées et regroupement des appels simultanés identiques d'un même client. Le cache est partagé localement via le fichier `pokemon_cache.sqlite3` et ignoré par Git. Sur un hébergement, sa persistance dépend de la plateforme.

```powershell
.\.venv\Scripts\python.exe -m demonstrations.simulation_charge --nombre 1000 --workers 50
.\.venv\Scripts\python.exe -m demonstrations.simulation_charge --nombre 1000000 --workers 50
.\.venv\Scripts\python.exe -m demonstrations.cache
```

La démonstration du cache avance une horloge fictive pour montrer l'expiration sans attendre une heure. Le débit de la simulation est local : ce n'est pas un débit réel de PokéAPI. Les vrais appels sont limités à cinq en concurrence et utilisent le cache, conformément à la politique de bon usage de PokéAPI.

## Tester

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Organisation

- `app.py` : interface Streamlit.
- `projet/client.py` : requêtes robustes et cache.
- `projet/pokemon.py` : extraction des données, comparaison, type et combat.
- `demonstrations/` : simulations des questions Q2 et Q3.
- `tests/` : vérifications automatiques avec API fictive.

Données fournies par [PokéAPI](https://pokeapi.co/).
