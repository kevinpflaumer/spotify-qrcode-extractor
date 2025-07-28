from spotipy import Spotify, SpotifyException, SpotifyClientCredentials
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

    _SPOTIFY_CLIENT_ID = config["spotify"]["client_id"]
    _SPOTIFY_CLIENT_SECRET = config["spotify"]["client_secret"]
    _OUTPUT_FOLDER = config["output"]["folder"]

    _PLAYLIST_ID = config.get("spotify", {}).get("playlist_id")
    if not _PLAYLIST_ID:
        _PLAYLIST_ID = input("Enter Spotify Playlist ID (format: 3rsWc7Z7Ai3cP3UfJNjhp4): ")

    # Creates spotify API instance
    spotify = Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id=_SPOTIFY_CLIENT_ID,
        client_secret=_SPOTIFY_CLIENT_SECRET,
    ))

    # Fetch tracks from playlist
    try:
        results = spotify.playlist_items(_PLAYLIST_ID)
    except SpotifyException as e:
        results = {}
        if e.http_status == 400:
            print(f"❌ Error: '{_PLAYLIST_ID}' is not a valid playlist ID.")
        elif e.http_status == 404:
            print(f"❌ Error: Playlist with ID '{_PLAYLIST_ID}' not found.")
        else:
            print(f"❌ Error: Uknown Spotify error: '{e}'")
        exit(1)

    # Creates output directory if it does not exist
    if not path.exists(_OUTPUT_FOLDER):
        makedirs(_OUTPUT_FOLDER)

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
        qr.save(path.join(_OUTPUT_FOLDER, filename))

    print("------ Successfully extracted all QR-Codes ------")


if __name__ == '__main__':
    main()
