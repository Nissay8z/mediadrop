# Gestion des cookies YouTube (fichier monté via Secret File Render)
COOKIES_FILE = "cookies.txt"
if os.path.exists(COOKIES_FILE):
    print(f"[INFO] Fichier cookies trouvé : {COOKIES_FILE}")
else:
    print("[WARN] Aucun fichier cookies trouvé, les requêtes YouTube peuvent échouer")
