"""Client PokéAPI : erreurs, nouvelles tentatives et cache d'une heure."""
import asyncio
import json
import random
import sqlite3
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from contextlib import closing

import httpx

BASE_URL = "https://pokeapi.co/api/v2"
CACHE_FILE = Path(__file__).resolve().parent.parent / "pokemon_cache.sqlite3"


class ErreurAPI(Exception):
    """Erreur lisible pour l'utilisateur."""


class PokeClient:
    def __init__(self, client, cache_file=CACHE_FILE, horloge=time.time, limite=1000):
        self.client = client
        self.cache_file = str(cache_file)
        self.horloge = horloge
        self.limite = limite
        self.verrous = {}
        self.semaphore = asyncio.Semaphore(5)
        with closing(sqlite3.connect(self.cache_file, isolation_level=None)) as connexion:
            connexion.execute("CREATE TABLE IF NOT EXISTS cache (cle TEXT PRIMARY KEY, reponse TEXT NOT NULL, expiration REAL NOT NULL)")

    async def get(self, url, params=None):
        adresse = httpx.URL(url)
        if params is not None:
            adresse = adresse.copy_merge_params(params)
        cle = str(adresse)
        # Un seul appel à la fois pour une URL, même si plusieurs tâches la demandent.
        verrou = self.verrous.setdefault(cle, asyncio.Lock())
        async with verrou:
            with closing(sqlite3.connect(self.cache_file, isolation_level=None)) as connexion:
                ligne = connexion.execute("SELECT reponse, expiration FROM cache WHERE cle = ?", (cle,)).fetchone()
            if ligne and ligne[1] > self.horloge():
                return json.loads(ligne[0])
            data = await self._requete(cle)
            with closing(sqlite3.connect(self.cache_file, isolation_level=None)) as connexion:
                connexion.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)", (cle, json.dumps(data), self.horloge() + 3600))
                connexion.execute("DELETE FROM cache WHERE expiration <= ?", (self.horloge(),))
                connexion.execute("DELETE FROM cache WHERE cle IN (SELECT cle FROM cache ORDER BY expiration DESC LIMIT -1 OFFSET ?)", (self.limite,))
            return data

    async def _requete(self, url):
        for tentative in range(1, 5):
            response = None
            try:
                async with self.semaphore:
                    response = await self.client.get(url, timeout=15.0)
                if response.is_success:
                    try:
                        return response.json()
                    except ValueError as erreur:
                        raise ErreurAPI("La réponse de l'API n'est pas un JSON valide.") from erreur
                if response.status_code == 404:
                    raise ErreurAPI("Pokémon ou type introuvable. Vérifie le nom ou l'identifiant.")
                if response.status_code not in (429, 500, 502, 503, 504):
                    raise ErreurAPI(f"Erreur HTTP {response.status_code}.")
                if tentative == 4:
                    raise ErreurAPI(f"API indisponible après 4 tentatives (HTTP {response.status_code}).")
            except httpx.RequestError as erreur:
                if tentative == 4:
                    raise ErreurAPI("Connexion impossible après 4 tentatives.") from erreur
            delai = 2 ** (tentative - 1) + random.uniform(0, 1)
            valeur = response.headers.get("Retry-After") if response is not None else None
            if valeur:
                try:
                    delai = max(0, float(valeur))
                except ValueError:
                    try:
                        date = parsedate_to_datetime(valeur)
                        delai = max(0, (date - datetime.now(timezone.utc)).total_seconds())
                    except (ValueError, TypeError, OverflowError):
                        pass
            await asyncio.sleep(delai)
