from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyOAuth
import yt_dlp
from dotenv import load_dotenv
import os
import logging
import re
from pathlib import Path

# Load environment variables
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv(
    "SPOTIPY_REDIRECT_URI", "http://localhost:8000/callback")

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    print("ERROR: Missing Spotify API credentials!")
    print("Please set the following environment variables:")
    print("- SPOTIPY_CLIENT_ID: Your Spotify app client ID")
    print("- SPOTIPY_CLIENT_SECRET: Your Spotify app client secret")
    print("- SPOTIPY_REDIRECT_URI: http://localhost:8000/callback (optional)")
    print("\nGet these from: https://developer.spotify.com/dashboard")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SpotifyDownloader:
    def __init__(self):
        """Initialize Spotify client and download settings"""
        self.sp = self._setup_spotify_client()
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)

    def _setup_spotify_client(self):
        """Setup Spotify client with OAuth"""
        scope = "playlist-read-private playlist-read-collaborative"
        sp_oauth = SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=scope,
            cache_path=None
        )

        # Get access token
        token_info = sp_oauth.get_access_token()
        if not token_info:
            logger.error("Failed to get access token")
            raise Exception("Authentication failed")

        return Spotify(auth=token_info['access_token'])

    def get_track_info(self, track_id):
        """Get track information from Spotify using track ID"""
        try:
            track = self.sp.track(track_id)
            return {
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'album': track['album']['name'],
                'duration': track['duration_ms'] // 1000,  # Convert to seconds
                'external_urls': track['external_urls']
            }
        except SpotifyException as e:
            logger.error(f"Spotify API error: {e}")
            return None

    def search_youtube(self, track_info):
        """Search for the track on YouTube"""
        # Try multiple search queries for better results
        queries = [
            f"{track_info['name']} by {' '.join(track_info['artists'])}",
            f"{track_info['name']} {' '.join(track_info['artists'])}",
            # Just first artist
            f"{track_info['name']} {track_info['artists'][0]}",
        ]

        yt_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        for query in queries:
            logger.info(f"Searching YouTube for: {query}")
            try:
                with yt_dlp.YoutubeDL(yt_opts) as ytdl:
                    info = ytdl.extract_info(
                        f"ytsearch1:{query}", download=False)
                    if "entries" in info and len(info["entries"]) > 0:
                        video = info["entries"][0]
                        # Additional validation: check if video is not too long (likely not a full album)
                        duration = video.get('duration', 0)
                        if duration == 0 or duration < 600:  # Less than 10 minutes
                            logger.info(
                                f"Found suitable video: {video.get('title', 'Unknown')}")
                            return f"https://www.youtube.com/watch?v={video['id']}"
                        else:
                            logger.warning(
                                f"Skipping long video ({duration}s): {video.get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"YouTube search error for '{query}': {e}")
                continue

        logger.error("No suitable YouTube video found for any search query")
        return None

    def download_track(self, track_id, quality='best'):
        """Download a Spotify track using its ID"""
        logger.info(f"Starting download for track ID: {track_id}")

        # Get track info from Spotify
        track_info = self.get_track_info(track_id)
        if not track_info:
            logger.error(f"Could not get track info for ID: {track_id}")
            return False

        logger.info(
            f"Track: {track_info['name']} by {', '.join(track_info['artists'])}")

        # Search for track on YouTube
        yt_url = self.search_youtube(track_info)
        if not yt_url:
            logger.error("Could not find track on YouTube")
            return False

        logger.info(f"Found YouTube URL: {yt_url}")

        # Download configuration - Force MP3 output
        safe_filename = self._sanitize_filename(
            f"{track_info['name']} - {', '.join(track_info['artists'])}")
        output_path = self.download_dir / f"{safe_filename}.%(ext)s"

        yt_dl_opts = {
            'format': 'bestaudio/best',  # Download best available audio quality
            'outtmpl': str(output_path),  # Output filename template
            'postprocessors': [{  # Convert to MP3 using FFmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',  # 320 kbps quality
            }],
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'audioformat': 'mp3',  # Fallback for older yt-dlp versions
            'ffmpeg_location': '/opt/homebrew/bin/ffmpeg',  # Explicit FFmpeg path
        }

        try:
            with yt_dlp.YoutubeDL(yt_dl_opts) as ytdl:
                ytdl.download([yt_url])

            # Verify the file was created and is MP3
            # The file should be created with .mp3 extension after postprocessing
            final_mp3_path = self.download_dir / f"{safe_filename}.mp3"
            if final_mp3_path.exists():
                logger.info(
                    f"Successfully downloaded: {track_info['name']} as MP3")
                return True
            else:
                # Check if file exists with different extension (fallback)
                for ext in ['.m4a', '.webm', '.ogg', '.opus']:
                    alt_path = self.download_dir / f"{safe_filename}{ext}"
                    if alt_path.exists():
                        logger.warning(
                            f"File downloaded as {ext}, converting to MP3...")
                        # Convert using FFmpeg directly
                        import subprocess
                        try:
                            subprocess.run([
                                '/opt/homebrew/bin/ffmpeg', '-i', str(
                                    alt_path),
                                '-acodec', 'mp3', '-ab', '320k',
                                str(final_mp3_path), '-y'
                            ], check=True, capture_output=True)
                            alt_path.unlink()  # Remove original file
                            logger.info(
                                f"Successfully converted and downloaded: {track_info['name']} as MP3")
                            return True
                        except subprocess.CalledProcessError as e:
                            logger.error(f"FFmpeg conversion failed: {e}")
                            return False

                logger.error(
                    f"Download completed but file not found: {final_mp3_path}")
                return False

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    def _sanitize_filename(self, filename):
        """Remove invalid characters from filename"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip()

    def download_playlist(self, playlist_id, progress_callback=None):
        """Download all tracks from a Spotify playlist with progress updates"""
        try:
            playlist = self.sp.playlist(playlist_id)
            tracks = playlist['tracks']['items']

            logger.info(
                f"Found {len(tracks)} tracks in playlist: {playlist['name']}")

            successful_downloads = 0
            failed_downloads = 0

            for i, item in enumerate(tracks, 1):
                track = item['track']
                if track is None:
                    logger.warning(f"Skipping null track at position {i}")
                    failed_downloads += 1
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'message': f'Skipping null track at position {i}',
                            'progress': i,
                            'total': len(tracks),
                            'current_track': None
                        })
                    continue

                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'album': track['album']['name']
                }

                # Send progress update - starting download
                if progress_callback:
                    progress_callback({
                        'type': 'downloading',
                        'message': f'Downloading {i}/{len(tracks)}: {track["name"]}',
                        'progress': i,
                        'total': len(tracks),
                        'current_track': track_info
                    })

                logger.info(
                    f"Downloading {i}/{len(tracks)}: {track['name']} by {', '.join(track_info['artists'])}")
                success = self.download_track(track['id'])

                if success:
                    successful_downloads += 1
                    logger.info(f"✅ Successfully downloaded: {track['name']}")
                    if progress_callback:
                        progress_callback({
                            'type': 'completed',
                            'message': f'Successfully downloaded: {track["name"]}',
                            'progress': i,
                            'total': len(tracks),
                            'current_track': track_info,
                            'success': True
                        })
                else:
                    failed_downloads += 1
                    logger.warning(f"❌ Failed to download: {track['name']}")
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'message': f'Failed to download: {track["name"]}',
                            'progress': i,
                            'total': len(tracks),
                            'current_track': track_info,
                            'success': False
                        })

            # Send final completion update
            if progress_callback:
                progress_callback({
                    'type': 'finished',
                    'message': f'Playlist download completed: {successful_downloads} successful, {failed_downloads} failed',
                    'progress': len(tracks),
                    'total': len(tracks),
                    'current_track': None,
                    'successful_downloads': successful_downloads,
                    'failed_downloads': failed_downloads,
                    'success': successful_downloads > 0
                })

            logger.info(
                f"Playlist download completed: {successful_downloads} successful, {failed_downloads} failed")
            return successful_downloads > 0

        except SpotifyException as e:
            logger.error(f"Playlist error: {e}")
            if progress_callback:
                progress_callback({
                    'type': 'error',
                    'message': f'Playlist error: {str(e)}',
                    'progress': 0,
                    'total': 0,
                    'current_track': None,
                    'success': False
                })
            return False


def download_single_track(track_id):
    """Download a single Spotify track by ID"""
    downloader = SpotifyDownloader()

    print("Spotify Single Track Downloader")
    print("=" * 50)

    success = downloader.download_track(track_id)
    if success:
        print(f"✅ Successfully downloaded track with ID: {track_id}")
    else:
        print(f"❌ Failed to download track with ID: {track_id}")

    return success


def download_playlist_tracks(playlist_id, progress_callback=None):
    """Download all tracks from a Spotify playlist by ID"""
    downloader = SpotifyDownloader()

    print("Spotify Playlist Downloader")
    print("=" * 50)

    try:
        success = downloader.download_playlist(playlist_id, progress_callback)
        if success:
            print(f"✅ Playlist download completed for ID: {playlist_id}")
        else:
            print(
                f"⚠️ Playlist download completed with some failures for ID: {playlist_id}")
        return success
    except Exception as e:
        print(f"❌ Failed to download playlist with ID: {playlist_id}")
        print(f"Error: {e}")
        return False
