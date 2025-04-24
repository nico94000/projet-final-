#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper LinkedIn via ScrapingDog API
-----------------------------------
Ce script permet de collecter des posts LinkedIn en français sur l'IA 
en utilisant l'API ScrapingDog, qui permet d'éviter les blocages de LinkedIn.
Il extrait également les métriques d'engagement (likes, commentaires, partages) quand c'est possible.
"""

import requests
import json
import csv
import os
import time
import random
from datetime import datetime
import argparse

# Dossier pour sauvegarder les résultats
RESULTS_DIR = 'resultats'
os.makedirs(RESULTS_DIR, exist_ok=True)

class LinkedInScrapingDogAPI:
    def __init__(self, api_key, pause_min=1, pause_max=3):
        """
        Initialise le scraper basé sur l'API ScrapingDog
        
        Args:
            api_key (str): Clé API ScrapingDog
            pause_min (int): Délai minimum entre les requêtes (en secondes)
            pause_max (int): Délai maximum entre les requêtes (en secondes)
        """
        self.api_key = api_key
        self.pause_min = pause_min
        self.pause_max = pause_max
        self.base_url = "https://api.scrapingdog.com/linkedin"
        self.found_urls = set()
        self.results = []
        
    def random_pause(self):
        """Pause aléatoire pour éviter de surcharger l'API"""
        sleep_time = random.uniform(self.pause_min, self.pause_max)
        print(f"Pause de {sleep_time:.2f} secondes...")
        time.sleep(sleep_time)
    
    def search_linkedin_posts(self, keywords, language='fr', max_results=100):
        """
        Recherche des posts LinkedIn via l'API ScrapingDog
        
        Args:
            keywords (list): Liste de mots-clés à rechercher
            language (str): Langue des résultats ('fr' pour français)
            max_results (int): Nombre maximum de résultats à récupérer
            
        Returns:
            set: Ensemble des URLs LinkedIn trouvées
        """
        print(f"Recherche de posts LinkedIn avec les mots-clés: {keywords}")
        
        # Construire la requête de recherche
        keyword_query = " OR ".join(keywords)
        
        # Paramètres pour l'API ScrapingDog
        for keyword in keywords:
            print(f"\nRecherche pour le mot-clé: {keyword}")
            
            params = {
                "api_key": self.api_key,
                "type": "search",
                "search_term": keyword,
                "content_type": "posts",
                "language": language,
                "limit": min(100, max_results)  # Maximum 100 par requête
            }
            
            try:
                # Faire la requête à l'API
                response = requests.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extraire les URLs des posts
                    if "posts" in data and isinstance(data["posts"], list):
                        for post in data["posts"]:
                            if "url" in post:
                                self.found_urls.add(post["url"])
                                print(f"  -> Trouvé: {post['url']}")
                    
                    print(f"  -> {len(data.get('posts', []))} posts trouvés pour '{keyword}'")
                else:
                    print(f"  -> Erreur API ({response.status_code}): {response.text}")
                
                # Pause pour éviter de surcharger l'API
                self.random_pause()
                
            except requests.exceptions.RequestException as e:
                print(f"Erreur lors de la requête à l'API: {e}")
            except Exception as e:
                print(f"Une erreur inattendue s'est produite: {e}")
        
        print(f"\nTotal d'URLs LinkedIn uniques trouvées: {len(self.found_urls)}")
        return self.found_urls
    
    def extract_post_content(self, url):
        """
        Extrait le contenu d'un post LinkedIn via l'API ScrapingDog
        
        Args:
            url (str): URL du post LinkedIn
            
        Returns:
            dict: Dictionnaire contenant les informations du post
        """
        print(f"Extraction du contenu pour: {url}")
        
        # Initialiser le dictionnaire de résultats
        post_data = {
            'url': url,
            'text': '',
            'author': '',
            'date': '',
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'success': False
        }
        
        try:
            # Paramètres pour l'API ScrapingDog
            params = {
                "api_key": self.api_key,
                "type": "post",
                "url": url
            }
            
            # Faire la requête à l'API
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraire les données du post
                if "post" in data:
                    post_info = data["post"]
                    
                    # Texte du post
                    post_data['text'] = post_info.get('text', '')
                    
                    # Auteur
                    if "author" in post_info:
                        post_data['author'] = post_info["author"].get('name', '')
                    
                    # Date
                    post_data['date'] = post_info.get('date', '')
                    
                    # Métriques d'engagement
                    post_data['likes'] = post_info.get('likes', 0)
                    post_data['comments'] = post_info.get('comments', 0)
                    post_data['shares'] = post_info.get('shares', 0)
                    
                    # Marquer comme réussi si on a du texte
                    if post_data['text']:
                        post_data['success'] = True
                        print(f"  -> Extraction réussie: {len(post_data['text'])} caractères, {post_data['likes']} likes, {post_data['comments']} commentaires")
                    else:
                        print("  -> Échec de l'extraction: aucun contenu trouvé")
                else:
                    print(f"  -> Erreur: Données de post non trouvées dans la réponse")
            else:
                print(f"  -> Erreur API ({response.status_code}): {response.text}")
            
        except requests.exceptions.RequestException as e:
            print(f"  -> Erreur lors de la requête à l'API: {e}")
        except Exception as e:
            print(f"  -> Erreur inattendue: {e}")
        
        # Pause pour éviter de surcharger l'API
        self.random_pause()
        
        return post_data
    
    def process_urls(self, urls=None, max_urls=None):
        """
        Traite une liste d'URLs pour extraire le contenu des posts
        
        Args:
            urls (set, optional): Ensemble d'URLs à traiter. Si None, utilise self.found_urls
            max_urls (int, optional): Nombre maximum d'URLs à traiter. Si None, traite toutes les URLs
            
        Returns:
            list: Liste des données de posts extraites
        """
        if urls is None:
            urls = self.found_urls
        
        if max_urls is not None:
            urls_to_process = list(urls)[:max_urls]
        else:
            urls_to_process = list(urls)
        
        print(f"Traitement de {len(urls_to_process)} URLs...")
        
        for i, url in enumerate(urls_to_process):
            print(f"[{i+1}/{len(urls_to_process)}] Traitement de l'URL: {url}")
            post_data = self.extract_post_content(url)
            self.results.append(post_data)
        
        # Filtrer les résultats réussis
        successful_results = [r for r in self.results if r['success']]
        print(f"\nExtraction réussie pour {len(successful_results)}/{len(self.results)} posts")
        
        return self.results
    
    def save_results(self, filename_prefix='linkedin_posts'):
        """
        Sauvegarde les résultats dans des fichiers CSV et JSON
        
        Args:
            filename_prefix (str): Préfixe pour les noms de fichiers
            
        Returns:
            tuple: Chemins des fichiers CSV et JSON créés
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = os.path.join(RESULTS_DIR, f"{filename_prefix}_{timestamp}.csv")
        json_filename = os.path.join(RESULTS_DIR, f"{filename_prefix}_{timestamp}.json")
        urls_filename = os.path.join(RESULTS_DIR, f"{filename_prefix}_urls_{timestamp}.txt")
        
        # Sauvegarder les URLs brutes
        with open(urls_filename, 'w', encoding='utf-8') as f:
            for url in self.found_urls:
                f.write(f"{url}\n")
        
        # Sauvegarder en CSV
        with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['url', 'author', 'date', 'text', 'likes', 'comments', 'shares', 'success']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow(result)
        
        # Sauvegarder en JSON
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"URLs sauvegardées dans: {urls_filename}")
        print(f"Résultats sauvegardés en CSV: {csv_filename}")
        print(f"Résultats sauvegardés en JSON: {json_filename}")
        
        return csv_filename, json_filename, urls_filename

def main():
    """Fonction principale"""
    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description='Scraper LinkedIn via ScrapingDog API')
    parser.add_argument('--api_key', required=True, help='Clé API ScrapingDog')
    parser.add_argument('--max_results', type=int, default=100, help='Nombre maximum de résultats à récupérer')
    parser.add_argument('--sample_size', type=int, default=10, help='Taille de l\'échantillon pour le test')
    args = parser.parse_args()
    
    # Mots-clés liés à l'IA en français
    keywords = [
        "intelligence artificielle",
        "IA générative",
        "machine learning",
        "apprentissage automatique",
        "deep learning",
        "GPT",
        "ChatGPT",
        "IA France",
        "Acte IA Europe",
        "EU AI Act",
        "IA éthique",
        "IA responsable"
    ]
    
    # Initialiser le scraper
    scraper = LinkedInScrapingDogAPI(api_key=args.api_key, pause_min=1, pause_max=3)
    
    # Rechercher des posts LinkedIn
    urls = scraper.search_linkedin_posts(keywords, language='fr', max_results=args.max_results)
    
    # Traiter un échantillon pour tester
    sample_size = min(args.sample_size, len(urls))
    if sample_size > 0:
        print(f"\nTraitement d'un échantillon de {sample_size} URLs pour test...")
        scraper.process_urls(max_urls=sample_size)
        
        # Sauvegarder les résultats
        scraper.save_results(filename_prefix='linkedin_posts_ia_scrapingdog')
    else:
        print("Aucune URL trouvée pour le test.")

if __name__ == "__main__":
    main()
