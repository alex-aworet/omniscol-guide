#!/usr/bin/env python3
"""
Serveur web simple pour servir les fichiers statiques du site Omniscol
"""
import http.server
import socketserver
import os
import sys
import urllib.parse

PORT = 8001

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Ajouter des en-têtes CORS pour permettre les requêtes
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        if self.path.startswith('/socket.io/'):
            self.send_response(410)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()


    def _send_json_response(self, data, status=200):
        """Envoie une réponse JSON"""
        import json
        content = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        # Gérer les requêtes POST
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/cdn-cgi/rum'):
            # Accepter silencieusement les requêtes Cloudflare RUM
            self._send_json_response({"success": True})
            return
        
        # Gérer les requêtes POST vers /api/
        if path.startswith('/api/'):
            # Pour /api/guest/login, retourner une réponse de succès (utilisateur déjà connecté)
            if path == '/api/guest/login':
                self._send_json_response({
                    "success": True,
                    "user": {
                        "id": "kristale-mayila",
                        "login": "kristale.mayila",
                        "name": {"first_name": "Kristale", "last_name": "Mayila"},
                        "roles": ["admin"]
                    }
                })
                return
            
            # Pour les autres endpoints API POST, retourner une réponse mock
            self._send_json_response({"success": True, "message": "Mock response"})
            return
        
        # Pour les autres POST, retourner 404
        self.send_response(410)
        self.end_headers()

    def do_GET(self):
        # Si la requête est pour la racine, servir index.html
        if self.path == '/':
            self.path = '/index.html'
            return super().do_GET()
        
        # Parser l'URL pour gérer les query strings
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Gérer les requêtes socket.io (WebSocket) - retourner 404 silencieusement
        if path.startswith('/socket.io/'):
            self.send_response(404)
            self.end_headers()
            return
        
        # Gérer les fichiers API (fichiers .html dans /api/)
        if path.startswith('/api/'):
            # Chercher le fichier .html correspondant
            api_file = path
            if not api_file.endswith('.html'):
                # Ajouter .html si ce n'est pas déjà présent
                api_file = api_file.rstrip('/') + '.html'
            
            file_path = os.path.join(os.getcwd(), api_file.lstrip('/'))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    return
            else:
                # Fichier API non trouvé - retourner une réponse mock selon le type d'endpoint
                if '/admin/teachers' in path:
                    # Mock pour les professeurs
                    self._send_json_response({
                        "success": True,
                        "teachers": []
                    })
                    return
                elif '/admin/' in path:
                    # Mock générique pour les endpoints admin
                    self._send_json_response({
                        "success": True,
                        "data": []
                    })
                    return
                else:
                    # Mock générique pour les autres endpoints API
                    self._send_json_response({
                        "success": True,
                        "message": "Mock response - endpoint not found"
                    })
                    return
        
        # Gérer les fichiers i18n (fichiers .html dans /i18n/)
        if path.startswith('/i18n/'):
            # Chercher le fichier .html correspondant
            i18n_file = path
            if not i18n_file.endswith('.html'):
                # Ajouter .html si ce n'est pas déjà présent
                i18n_file = i18n_file.rstrip('/') + '.html'
            
            file_path = os.path.join(os.getcwd(), i18n_file.lstrip('/'))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    return
        
        # Gérer les fichiers manquants silencieusement (favicon, images, fonts, etc.)
        if path.startswith('/public/images/') or path.startswith('/public/fonts/'):
            # Retourner une réponse vide pour les fichiers manquants
            self.send_response(204)  # No Content
            self.end_headers()
            return
        
        # Pour tous les autres fichiers, utiliser le comportement par défaut
        return super().do_GET()

    def log_message(self, format, *args):
        # Filtrer les logs pour les requêtes socket.io, favicon et fonts manquants
        message = format % args
        if any(x in message for x in ['/socket.io/', '/public/images/favicon.png', '/public/fonts/fontawesome/fa-regular-400.woff2']):
            # Ne pas logger ces requêtes pour réduire le bruit
            return
        sys.stderr.write("%s - - [%s] %s\n" %
                        (self.address_string(),
                         self.log_date_time_string(),
                         message))

if __name__ == "__main__":
    # Changer vers le répertoire du script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Serveur démarré sur http://localhost:{PORT}")
        print(f"📁 Répertoire: {os.getcwd()}")
        print(f"🌐 Ouvrez votre navigateur à l'adresse: http://localhost:{PORT}")
        print("\nAppuyez sur Ctrl+C pour arrêter le serveur\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Serveur arrêté")
            sys.exit(0)
