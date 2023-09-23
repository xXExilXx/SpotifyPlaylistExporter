import requests
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

class SpotifyPlaylistCSV:
    def __init__(self, client_id, client_secret, port=8888):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.redirect_uri = f"http://localhost:{port}/callback"
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.port = port
        self.server = None

    def authorize(self):
        server_address = ("", self.port)
        self.server = HTTPServer(server_address, AuthHandler(self))
        self.server.handle_request()

        auth_query_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "playlist-read-private playlist-read-collaborative",
        }

        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(auth_query_params)}"
        webbrowser.open(auth_url)

    def get_access_token(self, auth_code):
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(self.token_url, data=token_data)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            print("Authorization successful.")
        else:
            print("Authorization failed.")

    def api_call(self, url):
        if not self.access_token:
            raise Exception("Authorization token is missing. Please authorize.")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise Exception("Authorization token expired. Please reauthorize.")
        elif response.status_code == 429:
            raise Exception("Rate limiting error. Please try again later.")
        else:
            raise Exception(f"Failed to fetch data from Spotify API. Status code: {response.status_code}")

    def get_playlist_csv(self, playlist_id):
        try:
            playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            playlist_data = self.api_call(playlist_url)
            tracks = playlist_data.get("items", [])

            csv_data = "Spotify ID,Artist(s),Track Name,Album Name,Artist Name(s),Release Date,Duration (ms),Popularity,Added By,Added At\n"

            for item in tracks:
                track = item["track"]
                artists = ", ".join([artist["name"] for artist in track["artists"]])
                csv_data += (
                    f"{track['id']},{artists},{track['name']},{track['album']['name']},{artists},"
                    f"{track['album']['release_date']},{track['duration_ms']},{track['popularity']},"
                    f"{item['added_by']['uri']},{item['added_at']}\n"
                )

            return csv_data
        except Exception as e:
            return str(e)

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if "code" in query_params:
            auth_code = query_params["code"][0]
            self.spotify_exporter.get_access_token(auth_code)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authorization complete. You can close this window.")
            self.spotify_exporter.server.shutdown()
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Invalid request.")

