# Site Web Omniscol - Guide de démarrage

## 🚀 Démarrage rapide

### Option 1 : Utiliser Python (recommandé)

1. Ouvrez un terminal dans ce dossier
2. Exécutez la commande :
   ```bash
   python3 server.py
   ```
   
   Ou utilisez le script shell :
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. Ouvrez votre navigateur à l'adresse : **http://localhost:8001**

### Option 2 : Utiliser Node.js (si Python n'est pas disponible)

Si vous avez Node.js installé, vous pouvez utiliser `npx` :

```bash
npx http-server -p 8000
```

Puis ouvrez : **http://localhost:8000**

## 📝 Notes importantes

- Le serveur doit être en cours d'exécution pour que le site fonctionne correctement
- Les fichiers doivent être servis via un serveur web (pas en ouvrant directement le fichier HTML)
- Pour arrêter le serveur, appuyez sur `Ctrl+C` dans le terminal

## 🔧 Dépannage

Si le port 8001 est déjà utilisé, modifiez la variable `PORT` dans `server.py` pour utiliser un autre port (par exemple 8080, 3000, etc.)
