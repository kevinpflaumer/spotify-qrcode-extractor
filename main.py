import tomllib
import click
from spotipy import Spotify, SpotifyException, SpotifyClientCredentials
from re import sub
from os import path, makedirs
from qrcode import make as qrcode_make
from sys import exit

CACHE_FILE = "appdata.cache"


def remove_forbidden_characters(name):
    return sub(r'[\\/*?:"<>|]', '_', name)


def load_cache():
    if path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            click.secho(f"🗃️ Loaded configuration file '{CACHE_FILE}'", fg="green")
            return tomllib.load(f)
    return {}


def save_cache(data: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        for key, value in data.items():
            f.write(f'{key} = "{value}"\n')


@click.command()
@click.option("--client-id", "-i", help="Spotify Client ID")
@click.option("--client-secret", "-s", help="Spotify Client Secret")
@click.option("--playlist", "-p", help="Spotify Playlist ID")
@click.option("--cache", "-c", is_flag=True, default=False, help="Stores the Configuration inside a cache file")
@click.option("--output", "-o", default="output", show_default=True, help="Output folder for QR codes")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def cli(client_id, client_secret, playlist, cache, output, verbose):
    """Generate QR codes for all tracks in a public Spotify playlist."""

    cache_data = load_cache()

    # Use CLI or fallback to cache
    client_id = client_id or cache_data.get("client_id")
    client_secret = client_secret or cache_data.get("client_secret")
    playlist = playlist or cache_data.get("playlist")
    verbose = verbose or cache_data.get("verbose")
    output = output or cache_data.get("output_directory")

    # Prompt if required values missing
    if not client_id:
        client_id = click.prompt("Enter your Spotify Client ID")
    if not client_secret:
        client_secret = click.prompt("Enter your Spotify Client Secret")
    if not playlist:
        playlist = click.prompt("Enter Spotify Playlist ID (format: 3rsWc7Z7Ai3cP3UfJNjhp4)", type=str)

    # Create Spotify API client
    spotify = Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
    ))

    # Fetch playlist items
    try:
        results = spotify.playlist_items(playlist)
    except SpotifyException as e:
        results = {}
        if e.http_status == 400:
            click.secho(f"❌ Error: '{playlist}' is not a valid playlist ID.", fg="red")
        elif e.http_status == 404:
            click.secho(f"❌ Error: Playlist with ID '{playlist}' not found.", fg="red")
        else:
            click.secho(f"❌ Unknown Spotify error: {e}", fg="red")
        exit(1)

    # Create output directory
    if not path.exists(output):
        makedirs(output)
        if verbose:
            click.secho(f"📁 Created output directory: {output}", fg="green")

    # Generate QR codes
    for idx, item in enumerate(results["items"]):
        track = item["track"]
        track_url = track["external_urls"]["spotify"]

        track_name = remove_forbidden_characters(track["name"])
        artist_names = remove_forbidden_characters(
            ', '.join(artist["name"] for artist in track["artists"])
        )

        filename = f"{artist_names} - {track_name}.png"
        filepath = path.join(output, filename)

        qr = qrcode_make(track_url)
        qr.save(filepath)

        if verbose:
            click.echo(f"✅ Extracted QR Code: {filepath}")

    click.secho("🎉 All QR codes generated successfully!", fg="cyan")

    # Save to appcache.toml if --cache is passed
    if cache:
        save_cache({
            "client_id": client_id,
            "client_secret": client_secret,
            "playlist": playlist,
            "verbose": output,
            "output": output,
        })
        click.secho(f"💾 Configuration stored in {CACHE_FILE}", fg="yellow")


if __name__ == "__main__":
    cli()
