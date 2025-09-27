"""
Spotify Downloader Package

This package provides functionality to download Spotify tracks and playlists
by searching for them on YouTube and downloading the audio files.
"""

from .downloader import SpotifyDownloader, download_single_track, download_playlist_tracks

__version__ = "1.0.0"
__author__ = "Your Name"

__all__ = [
    "SpotifyDownloader",
    "download_single_track", 
    "download_playlist_tracks"
]

