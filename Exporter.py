import csv
import argparse
import yt_dlp
from spotify_exporter import SpotifyPlaylistCSV

def export_spotify_playlist(playlist_id):
    # Create an instance of the SpotifyExporter
    exporter = SpotifyPlaylistCSV("3202554082f747cea5899a854a8959bb", "fe10ca3b20c6483ebf8082394596b758")

    #Get Acces Token
    exporter.authorize()

    # Export the playlist data as CSV
    playlist_data = exporter.get_playlist_csv(playlist_id)

    return playlist_data

def download_songs_from_csv(csv_data):
    # Initialize yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
    }

    # Create a yt-dlp instance
    ydl = yt_dlp.YoutubeDL(ydl_opts)

    # Read the CSV data and download each song
    csv_reader = csv.reader(csv_data.splitlines())
    next(csv_reader)  # Skip the header row
    for row in csv_reader:
        song_name = row[0]
        artist_name = row[1]
        query = f"{song_name} {artist_name} audio"

        # Download the song using yt-dlp
        try:
            ydl.download([query])
            print(f"Downloaded: {query}")
        except yt_dlp.DownloadError:
            print(f"Failed to download: {query}")

if __name__ == "__main__":
    # Create a command-line argument parser
    print('Spotify Playlist Download')
    print('ver. 0.0.1')
    playlist_id = input('Enter Playlist ID: ')

    # Export Spotify playlist data to a CSV data string
    playlist_data = export_spotify_playlist(playlist_id)

    # Download songs from YouTube using yt-dlp
    download_songs_from_csv(playlist_data)
