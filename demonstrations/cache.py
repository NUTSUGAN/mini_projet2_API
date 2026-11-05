"""Démonstration du cache d'une heure sans attendre ni utiliser Internet."""
import asyncio
import tempfile
from pathlib import Path
import httpx
from projet.client import PokeClient


async def demonstration():
    heure = [0.0]
    appels = [0]
    async def serveur(request):
        appels[0] += 1
        return httpx.Response(200, json={"appel": appels[0]})
    with tempfile.TemporaryDirectory() as dossier:
        async with httpx.AsyncClient(transport=httpx.MockTransport(serveur)) as http:
            client = PokeClient(http, cache_file=Path(dossier) / "cache.sqlite3", horloge=lambda: heure[0])
            url = "https://api.example.com/data1"
            for etape in ("Premier appel", "Cache", "Après une heure"):
                if etape == "Après une heure":
                    heure[0] += 3600
                reponse = await client.get(url, {"langue": "fr"})
                print(f"{etape} : {reponse} ; appels simulés : {appels[0]}")


if __name__ == "__main__":
    asyncio.run(demonstration())
