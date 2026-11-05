import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from projet.client import PokeClient, ErreurAPI
from projet.pokemon import pokemon, comparer, combat, statistiques_type


def fiche(nom, hp, attaque, defense):
    return {'nom': nom, 'stats': {'hp': hp, 'attack': attaque, 'defense': defense}}


class TestsProjet(unittest.IsolatedAsyncioTestCase):
    async def test_cache_expiration_concurrence_et_erreurs(self):
        temps, appels = [0], []
        async def serveur(request):
            appels.append(str(request.url))
            await asyncio.sleep(0)
            return httpx.Response(404 if request.url.path == '/erreur' else 200, json={'ok': True})
        with tempfile.TemporaryDirectory() as dossier:
            async with httpx.AsyncClient(transport=httpx.MockTransport(serveur)) as http:
                client = PokeClient(http, Path(dossier) / 'test.sqlite3', horloge=lambda: temps[0])
                url = 'https://example.com/test'
                await asyncio.gather(*(client.get(url, {'x': 1}) for _ in range(10)))
                self.assertEqual(len(appels), 1)
                await client.get(url, {'x': 2})
                self.assertEqual(len(appels), 2)
                temps[0] = 3600
                await client.get(url, {'x': 1})
                self.assertEqual(len(appels), 3)
                for _ in range(2):
                    with self.assertRaises(ErreurAPI):
                        await client.get('https://example.com/erreur')
                self.assertEqual(len(appels), 5)

    async def test_retry(self):
        appels = [0]
        async def serveur(request):
            appels[0] += 1
            return httpx.Response(503 if appels[0] == 1 else 200, headers={'Retry-After': '0'}, json={'ok': True})
        with tempfile.TemporaryDirectory() as dossier:
            async with httpx.AsyncClient(transport=httpx.MockTransport(serveur)) as http:
                client = PokeClient(http, Path(dossier) / 'test.sqlite3')
                self.assertEqual(await client.get('https://example.com/data'), {'ok': True})
                self.assertEqual(appels[0], 2)

    async def test_type_et_erreur(self):
        class Client:
            async def get(self, url):
                if '/type/' in url:
                    return {'name': 'fire', 'pokemon': [{'pokemon': {'name': 'a'}}, {'pokemon': {'name': 'b'}}]}
                nom = url.rstrip('/').split('/')[-1]
                return {'id': 1, 'name': nom, 'types': [], 'sprites': {'front_default': None}, 'stats': [{'stat': {'name': 'hp'}, 'base_stat': 40 if nom == 'a' else 60}]}
        resultat = await statistiques_type(Client(), 'fire')
        self.assertEqual((resultat['nombre'], resultat['moyenne_hp']), (2, 50))
        with self.assertRaises(ValueError):
            await pokemon(Client(), '../invalid')

    def test_comparaison_combat_et_egalite(self):
        a, b = fiche('a', 50, 30, 20), fiche('b', 40, 30, 40)
        self.assertEqual(comparer(a, b), {'hp': 'a', 'attack': 'Égalité'})
        self.assertEqual(combat(a, b)['gagnant'], 'b')
        self.assertEqual(combat(a, a)['gagnant'], 'Égalité')


if __name__ == '__main__':
    unittest.main()
