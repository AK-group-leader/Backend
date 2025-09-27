from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from spotify_downloader import download_single_track, download_playlist_tracks

from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8000/callback")

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    print("ERROR: Missing Spotify API credentials!")
    print("Please set the following environment variables:")
    print("- SPOTIPY_CLIENT_ID: Your Spotify app client ID")
    print("- SPOTIPY_CLIENT_SECRET: Your Spotify app client secret")
    print("- SPOTIPY_REDIRECT_URI: http://localhost:8000/callback (optional)")
    print("\nGet these from: https://developer.spotify.com/dashboard")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI setup
app = FastAPI(title="Spotify Playlist App")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],  # Added Vercel support
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spotify OAuth
scope = "playlist-read-private playlist-read-collaborative"
sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=scope,
    cache_path=None
)

def get_token_from_header(request: Request) -> str:
    """Extract token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid authorization header")
    return auth_header.split(" ")[1]

def warn_frontend(message: str, *, code: str = "DOWNLOAD_FAILED", entity: str = "item", entity_id: str = "", extra: dict | None = None) -> dict:
    """Create and log a structured warning payload for the frontend.

    Returns a dict suitable for HTTPException.detail or direct JSON responses.
    """
    payload = {
        "warning": {
            "code": code,
            "message": message,
            "entity": entity,
            "entity_id": entity_id,
            "extra": extra or {}
        }
    }
    logger.warning(f"{code}: {message} | entity={entity} id={entity_id} extra={extra}")
    return payload

@app.get("/")
def root():
    return {
        "message": "Spotify Playlist API is running",
        "status": "Server is healthy",
        "endpoints": {
            "login": "/login",
            "playlists": "/playlists",
            "playlist": "/playlist/{id}",
            "download_track_get": "GET /download/track/{track_id}",
            "download_track_post": "POST /download/track/{track_id}",
            "download_playlist_get": "GET /download/playlist/{playlist_id}",
            "download_playlist_post": "POST /download/playlist/{playlist_id}",
            "download_playlist_stream": "POST /download/playlist/{playlist_id}/stream"
        }
    }

@app.get("/login")
def login(request: Request):
    """Redirect to Spotify login"""
    auth_url = sp_oauth.get_authorize_url()

    if "Postman" in request.headers.get("user-agent", ""):
        return {"login_url": auth_url}

    return RedirectResponse(url=auth_url)

@app.get("/callback")
def callback(code: str = None):
    """Handle Spotify OAuth callback"""
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        access_token = token_info["access_token"]
        print(f"Obtained access token: {access_token}")
        
        # Redirect to frontend with token
        return RedirectResponse(f"http://localhost:3000?access_token={access_token}")
    
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.get("/playlists")
def get_playlists(request: Request):
    """Get user's playlists"""
    token = get_token_from_header(request)
    
    try:
        sp = Spotify(auth=token)
        result = sp.current_user_playlists(limit=50)
        
        playlists = []
        for playlist in result["items"]:
            playlists.append({
                "id": playlist["id"],
                "name": playlist["name"],
                "owner": playlist["owner"]["display_name"] or "Unknown",
                "tracks_total": playlist["tracks"]["total"],
                "image": playlist["images"][0]["url"] if playlist["images"] else None
            })
        
        return {"playlists": playlists}
    
    except SpotifyException as e:
        if e.http_status == 401:
            raise HTTPException(status_code=401, detail="Token expired")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch playlists")

@app.get("/playlist/{playlist_id}")
def get_playlist(playlist_id: str, request: Request):
    """Get playlist details with tracks"""
    token = get_token_from_header(request)
    
    try:
        sp = Spotify(auth=token)
        playlist = sp.playlist(playlist_id)
        
        tracks = []
        for item in playlist["tracks"]["items"]:
            if item["track"]:  # Skip null tracks
                track = item["track"]
                tracks.append({
                    "id": track["id"],
                    "name": track["name"],
                    "artists": [artist["name"] for artist in track["artists"]],
                    "album": track["album"]["name"],
                    "cover": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                    "duration_ms": track["duration_ms"]
                })
        
        return {
            "id": playlist["id"],
            "name": playlist["name"],
            "description": playlist.get("description", ""),
            "owner": playlist["owner"]["display_name"] or "Unknown",
            "tracks_total": playlist["tracks"]["total"],
            "image": playlist["images"][0]["url"] if playlist["images"] else None,
            "tracks": tracks
        }
    
    except SpotifyException as e:
        if e.http_status == 401:
            raise HTTPException(status_code=401, detail="Token expired")
        elif e.http_status == 404:
            raise HTTPException(status_code=404, detail="Playlist not found")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch playlist")
    
@app.get("/download/track/{track_id}")
def download_track_get(track_id: str):
    """Download a single track (GET method for testing)"""
    try:
        success = download_single_track(track_id)
        if success:
            return {
                "message": "Track download initiated successfully",
                "track_id": track_id,
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=warn_frontend(
                    "Failed to download track (no matching YouTube result or download error)",
                    code="TRACK_DOWNLOAD_FAILED",
                    entity="track",
                    entity_id=track_id
                )
            )
    except Exception as e:
        logger.error(f"Error downloading track {track_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=warn_frontend(
                f"Unexpected error while downloading track: {str(e)}",
                code="TRACK_DOWNLOAD_EXCEPTION",
                entity="track",
                entity_id=track_id
            )
        )

@app.post("/download/track/{track_id}")
def download_track(track_id: str, request: Request):
    """Download a single track"""
    token = get_token_from_header(request)
    
    try:
        # Verify track exists
        sp = Spotify(auth=token)
        track = sp.track(track_id)
        
        # Download the track
        success = download_single_track(track_id)
        
        if success:
            return {
                "message": "Track download initiated successfully",
                "track_id": track_id,
                "track_name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to download track")
            
    except SpotifyException as e:
        if e.http_status == 404:
            raise HTTPException(status_code=404, detail="Track not found")
        elif e.http_status == 401:
            raise HTTPException(status_code=401, detail="Token expired")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading track {track_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download track")

@app.post("/download/playlist/{playlist_id}")
def download_playlist(playlist_id: str, request: Request):
    """Download all tracks from a playlist"""
    token = get_token_from_header(request)
    
    try:
        # Verify playlist exists
        sp = Spotify(auth=token)
        playlist = sp.playlist(playlist_id)
        
        # Download the playlist
        success = download_playlist_tracks(playlist_id)
        
        if success:
            return {
                "message": "Playlist download completed successfully",
                "playlist_id": playlist_id,
                "playlist_name": playlist["name"],
                "tracks_total": playlist["tracks"]["total"],
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=warn_frontend(
                    "Failed to download one or more tracks from the playlist",
                    code="PLAYLIST_DOWNLOAD_FAILED",
                    entity="playlist",
                    entity_id=playlist_id
                )
            )
            
    except SpotifyException as e:
        if e.http_status == 404:
            raise HTTPException(status_code=404, detail="Playlist not found")
        elif e.http_status == 401:
            raise HTTPException(status_code=401, detail="Token expired")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading playlist {playlist_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=warn_frontend(
                f"Unexpected error while downloading playlist: {str(e)}",
                code="PLAYLIST_DOWNLOAD_EXCEPTION",
                entity="playlist",
                entity_id=playlist_id
            )
        )

@app.post("/download/playlist/{playlist_id}/stream")
async def download_playlist_stream(playlist_id: str, request: Request):
    """Download all tracks from a playlist with real-time progress updates"""
    token = get_token_from_header(request)
    
    try:
        # Verify playlist exists
        sp = Spotify(auth=token)
        playlist = sp.playlist(playlist_id)
        
        async def generate_progress_updates():
            from spotify_downloader.downloader import SpotifyDownloader
            import queue
            import threading
            
            downloader = SpotifyDownloader()
            progress_queue = queue.Queue()
            
            # Send initial info
            initial_data = {
                'type': 'started', 
                'message': f'Starting download of playlist: {playlist["name"]}', 
                'playlist_name': playlist['name'], 
                'total_tracks': playlist['tracks']['total']
            }
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            # Create progress callback that puts data in queue
            def progress_callback(update_data):
                progress_queue.put(update_data)
            
            # Start download in thread
            download_thread = threading.Thread(
                target=lambda: downloader.download_playlist(playlist_id, progress_callback)
            )
            download_thread.start()
            
            # Stream updates while download is running
            while download_thread.is_alive() or not progress_queue.empty():
                try:
                    # Get update from queue with timeout
                    update_data = progress_queue.get(timeout=0.1)
                    yield f"data: {json.dumps(update_data)}\n\n"
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    await asyncio.sleep(0.1)
            
            # Wait for download to complete
            download_thread.join()
            
            # Send final result
            final_result = {
                'type': 'finished',
                'success': True,  # We'll get the actual result from the progress updates
                'playlist_id': playlist_id,
                'playlist_name': playlist['name'],
                'message': 'Playlist download completed'
            }
            yield f"data: {json.dumps(final_result)}\n\n"
            
        return StreamingResponse(
            generate_progress_updates(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
            
    except SpotifyException as e:
        if e.http_status == 404:
            raise HTTPException(status_code=404, detail="Playlist not found")
        elif e.http_status == 401:
            raise HTTPException(status_code=401, detail="Token expired")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading playlist {playlist_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=warn_frontend(
                f"Unexpected error while downloading playlist: {str(e)}",
                code="PLAYLIST_DOWNLOAD_EXCEPTION",
                entity="playlist",
                entity_id=playlist_id
            )
        )

if __name__ == "__main__":
    import uvicorn
    print("Starting Spotify Playlist API server...")
    print(f"Server will run at: http://localhost:8000")
    print(f"Frontend should be at: http://localhost:3000")
    print("Make sure you have set your Spotify API credentials!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
