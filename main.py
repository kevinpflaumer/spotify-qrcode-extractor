from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify, SpotifyException
from tomllib import load as tomllib_load
from tomllib import TOMLDecodeError
from re import sub
from os import path, makedirs
from qrcode import make as qrcode_make
from sys import exit


def remove_forbidden_characters(name):
    # Replace invalid filename characters with underscores
    return sub(r'[\\/*?:"<>|]', '_', name)


def main():
    # Load config from config.toml
    try:
        with open("config.toml", "rb") as f:
            config = tomllib_load(f)
    except FileNotFoundError:
        print("❌ Error: 'config.toml' file not found. Please make sure it exists in the working directory.")
        exit(1)
    except TOMLDecodeError as e:
        print(f"❌ Error: Failed to parse 'config.toml': {e}")
        exit(1)

    spotify_config = config["spotify"]
    output_config = config["output"]

    playlist_id = config.get("spotify", {}).get("playlist_id")

    if not playlist_id:
        playlist_id = input("Enter Spotify Playlist ID (format: 3rsWc7Z7Ai3cP3UfJNjhp4): ")

    # Creates spotify API instance
    spotify = Spotify(auth_manager=SpotifyOAuth(
        client_id=spotify_config["client_id"],
        client_secret=spotify_config["client_secret"],
        redirect_uri=spotify_config["redirect_url"])
    )

    # Fetch tracks from playlist
    try:
        results = spotify.playlist_items(playlist_id)
    except SpotifyException as e:
        results = {}
        if e.http_status == 400:
            print(f"❌ Error: '{playlist_id}' is not a valid playlist ID.")
        elif e.http_status == 404:
            print(f"❌ Error: Playlist with ID '{playlist_id}' not found.")
        else:
            print(f"❌ Error: Uknown Spotify error: '{e}'")
        exit(1)

    # Creates output directory if it does not exist
    if not path.exists(output_config["folder"]):
        makedirs(output_config["folder"])

    # For each track, generate a qr code and save it
    for idx, item in enumerate(results['items']):
        track = item['track']
        track_url = track['external_urls']['spotify']

        # Get clean track name
        track_name_raw = track['name']
        track_name = remove_forbidden_characters(track_name_raw)

        # Get clean artists (joined with commas) names
        artist_names_raw = ', '.join([artist['name'] for artist in track['artists']])
        artist_names = remove_forbidden_characters(artist_names_raw)

        # Saves the qr code to disk
        filename = f"{artist_names} - {track_name}.png"
        qr = qrcode_make(track_url)
        qr.save(path.join(output_config["folder"], filename))

    print("------ Successfully extracted all QR-Codes ------")


if __name__ == '__main__':
    main()
