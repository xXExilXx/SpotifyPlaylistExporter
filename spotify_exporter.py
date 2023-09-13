import requests
import time
import webbrowser
from selenium import webdriver
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class SpotifyExporter:
    def __init__(self):
        self.SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
        self.client_id = "3202554082f747cea5899a854a8959bb"
        self.client_secret = "fe10ca3b20c6483ebf8082394596b758"
        self.redirect_uri = "http://localhost:8080/callback"
        self.scopes = ["playlist-read-private", "playlist-read-collaborative"]
        self.access_token = None
        self.auth_server = self._start_authentication_server()

    def _start_authentication_server(self):
        class AuthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.server.auth_code = self.path.split('code=')[1]

        server = HTTPServer(('localhost', 8080), AuthHandler)
        server.auth_code = None
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server

    def _get_access_token(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)

        auth_url = f"https://accounts.spotify.com/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={'+'.join(self.scopes)}&response_type=code"

        # Open the web browser for the user to log in
        webbrowser.open(auth_url)

        while "code=" not in driver.current_url:
            time.sleep(1)

        authorization_code = driver.current_url.split('code=')[1]
        driver.quit()

        token_url = 'https://accounts.spotify.com/api/token'
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode(),
        }
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
        }
        response = requests.post(token_url, headers=headers, data=data)

        if response.status_code == 200:
            self.access_token = response.json()['access_token']
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def _make_api_call(self, url, params=None):
        if not self.access_token:
            self._get_access_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def export_playlist(self, playlist_id):
        playlist_response = self._make_api_call(f"{self.SPOTIFY_API_BASE_URL}/playlists/{playlist_id}")
        playlist_tracks_response = self._make_api_call(f"{self.SPOTIFY_API_BASE_URL}/playlists/{playlist_id}/tracks")
        playlist_tracks = playlist_tracks_response["items"]

        csv_data = ""
        csv_data += "Track Name, Artist(s), Album, Release Date, Duration (ms)\n"

        for track in playlist_tracks:
            track_data = [
                track["track"]["name"],
                ", ".join([artist["name"] for artist in track["track"]["artists"]]),
                track["track"]["album"]["name"],
                track["track"]["album"]["release_date"],
                track["track"]["duration_ms"]
            ]
            csv_data += ",".join(['"{}"'.format(item) for item in track_data]) + "\n"

        return csv_data
