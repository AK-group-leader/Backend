# Spotify Downloader Backend

A FastAPI backend service that downloads Spotify tracks and playlists by searching for them on YouTube and converting the audio to MP3 format.

## Features

- Download individual Spotify tracks as MP3 files
- Download entire Spotify playlists as MP3 files
- High-quality audio (320 kbps MP3)
- Automatic YouTube search and matching
- RESTful API endpoints
- Progress tracking and error handling

## Prerequisites

### Required Software
1. **Python 3.8+**
2. **FFmpeg** - Required for audio conversion to MP3 format
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from https://ffmpeg.org/download.html

### Spotify API Setup
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note down your `Client ID` and `Client Secret`
4. Add `http://localhost:8000/callback` as a redirect URI

## Installation

1. **Clone and navigate to the project:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Create environment file:**
   Create a `.env` file in the project root:
   ```env
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://localhost:8000/callback
   ```

## Usage

### Start the Server
```bash
python3 main.py
```

The server will start at `http://localhost:8000`

### API Endpoints

#### Authentication
- `GET /login` - Redirect to Spotify OAuth login
- `GET /callback` - OAuth callback handler

#### Playlists
- `GET /playlists` - Get user's playlists (requires Bearer token)
- `GET /playlist/{id}` - Get playlist details with tracks (requires Bearer token)

#### Downloads
- `GET /download/track/{track_id}` - Download single track (testing)
- `POST /download/track/{track_id}` - Download single track (requires Bearer token)
- `POST /download/playlist/{playlist_id}` - Download entire playlist (requires Bearer token)
- `POST /download/playlist/{playlist_id}/stream` - Download entire playlist with real-time progress updates (Server-Sent Events)

### Example Usage

1. **Get access token:**
   ```bash
   curl http://localhost:8000/login
   ```

2. **Download a track:**
   ```bash
   curl -X POST "http://localhost:8000/download/track/4iV5W9uYEdYUVa79Axb7Rh" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

3. **Download a playlist (standard):**
   ```bash
   curl -X POST "http://localhost:8000/download/playlist/37i9dQZF1DXcBWIGoYBM5M" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

4. **Download a playlist with real-time progress (Server-Sent Events):**
   ```bash
   curl -X POST "http://localhost:8000/download/playlist/37i9dQZF1DXcBWIGoYBM5M/stream" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        -H "Accept: text/event-stream"
   ```

## Output Format

All downloaded files are saved as **MP3 files** in the `downloads/` directory with:
- **Quality**: 320 kbps
- **Format**: MP3
- **Naming**: `{Track Name} - {Artist Name}.mp3`

## Real-time Progress Updates

The `/stream` endpoint provides real-time progress updates using Server-Sent Events (SSE). The frontend can listen to these events to show:

- **Current song being downloaded**
- **Progress percentage** (e.g., "Downloading 3/10")
- **Success/failure status** for each track
- **Final completion summary**

### Event Types

The stream sends JSON events with the following types:

- `started` - Download process initiated
- `downloading` - Currently downloading a track
- `completed` - Track successfully downloaded
- `error` - Track download failed
- `finished` - All downloads completed
- `heartbeat` - Keep connection alive

### Frontend Integration

```javascript
// Example JavaScript code to consume the stream
const eventSource = new EventSource('/download/playlist/PLAYLIST_ID/stream', {
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
});

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'downloading':
            updateProgress(data.progress, data.total);
            showCurrentTrack(data.current_track);
            break;
        case 'completed':
            showSuccess(data.current_track);
            break;
        case 'finished':
            showFinalResults(data);
            eventSource.close();
            break;
    }
};
```

## File Structure

```
backend/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── downloads/             # Downloaded MP3 files
└── spotify_downloader/
    ├── __init__.py
    └── downloader.py      # Core download logic
```

## Troubleshooting

### Common Issues

1. **"FFmpeg not found" error:**
   - Install FFmpeg (see Prerequisites)
   - Ensure FFmpeg is in your system PATH

2. **"No module named 'yt_dlp'" error:**
   - Run: `pip3 install -r requirements.txt`

3. **Spotify API errors:**
   - Verify your credentials in `.env` file
   - Check if your Spotify app has the correct redirect URI

4. **Downloads not working:**
   - Check internet connection
   - Verify YouTube is accessible
   - Check logs for specific error messages

### Logs

The application provides detailed logging. Check the console output for:
- Download progress
- Error messages
- Success confirmations

## Legal Notice

This tool is for personal use only. Please respect copyright laws and terms of service of both Spotify and YouTube. Only download content you have the right to download.
