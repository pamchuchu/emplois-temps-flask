# Emplois du temps - Flask starter (Render)

Starter pour gérer les emplois du temps des enseignants par classe.

## Contenu
- app.py : app Flask + API CRUD
- init_db.py : script d'initialisation
- requirements.txt
- Procfile (pour render)
- templates/ (index, admin, teacher)
- static/style.css

## Déploiement sur Render
1. Crée un repo GitHub et pousse tous les fichiers (ou crée-les via l'interface GitHub web).
2. Crée un compte sur https://render.com et connecte GitHub.
3. New → Web Service → choose repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Dans Environment Variables (Settings), si tu veux Postgres sur Render :
   - DATABASE_URL = la URL Postgres fournie par Render (recommandé)
   - SECRET_KEY = valeur secrète
5. Deploy.

Remarque : SQLite est possible mais le filesystem des hébergeurs peut être éphémère. Préfère Postgres pour production.
