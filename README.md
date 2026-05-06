📀 MediaDrop
Téléchargeur et convertisseur audio/vidéo multi-plateformes (YouTube, Spotify, SoundCloud, TikTok, Instagram, Twitter, Facebook, Deezer).
100% gratuit, sans pub, avec suppression automatique des fichiers après 2h.

✨ Fonctionnalités
🎯 Support de 8 plateformes (YouTube, Spotify, etc.)

🎵 Conversion audio : MP3, FLAC, WAV, AAC, OGG, M4A, etc.

🎬 Téléchargement vidéo : MP4, MKV, AVI, WebM, MOV, GIF, etc.

📂 Playlists entières (YouTube, Spotify) → ZIP

🖼️ Métadonnées et pochettes d’album automatiques

🗑️ Fichiers supprimés après 2 heures (vie privée)

⚡ Interface moderne et responsive

🧱 Architecture
Frontend : HTML / CSS / JS (statique) – peut être hébergé sur GitHub Pages

Backend : Flask + yt-dlp + spotdl + FFmpeg – déployé sur Render.com

🔧 Prérequis (pour exécuter localement)
Python 3.10+

FFmpeg (installé et accessible dans le PATH)

pip

🚀 Installation locale
bash
git clone https://github.com/Nissay8z/mediadrop.git
cd mediadrop
pip install -r requirements.txt
Configuration des cookies YouTube (optionnel mais recommandé)
Pour éviter le blocage « Sign in to confirm you’re not a bot », exporte tes cookies YouTube au format Netscape (extension navigateur) et place le fichier cookies.txt à la racine du projet.

Lancement
bash
python app.py
Le backend sera dispo sur http://localhost:5000.
Le frontend (index.html) peut être ouvert directement ou servi via un serveur statique.

☁️ Déploiement sur Render
Mets le code (avec app.py, requirements.txt et ton frontend si tu veux tout servir ensemble) sur GitHub.

Crée un Web Service sur Render, lien vers ton dépôt.

Configuration :

Environment : Python 3

Build Command : pip install -r requirements.txt

Start Command : gunicorn app:app

Ajoute une variable d’environnement : FFMPEG_PATH = /usr/bin/ffmpeg

Ajoute un Secret File nommé cookies.txt avec le contenu brut de tes cookies YouTube.

Déploie.

🌐 Publication du frontend sur GitHub Pages
Prends le fichier index.html modifié (avec const API = "https://ton-backend.render.com").

Crée un dépôt distinct (ou le même mais avec une branche gh-pages).

Active GitHub Pages dans les paramètres du dépôt.

Accède à https://ton-utilisateur.github.io/nom-du-repo

📁 Structure du dépôt
text
mediadrop/
├── app.py                # Backend Flask
├── requirements.txt      # Dépendances Python
├── index.html            # Frontend (optionnel, peut être ailleurs)
├── cookies.txt           # (non commité, à ajouter via Secret File Render)
└── README.md
🛠️ Technologies utilisées
Flask – API REST

yt-dlp – téléchargement YouTube et autres

spotdl – téléchargement Spotify via YouTube

FFmpeg – conversion audio/vidéo

Gunicorn – serveur WSGI pour la production

Render – hébergement backend

📄 Licence
Ce projet est à but éducatif. Respectez les droits d’auteur et les conditions d’utilisation des plateformes concernées.

POUR TESTER

https://nissay8z.github.io/mediadrop/
