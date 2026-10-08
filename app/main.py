from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.torrentio import TorrentioManager, TorrentOption

load_dotenv()

app = FastAPI(title="Sagoon Flixer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w342"


class SearchResult(BaseModel):
    id: int
    title: str
    name: str
    poster_path: Optional[str]
    release_date: Optional[str]
    first_air_date: Optional[str]
    overview: str
    media_type: str


class TorrentOptionResponse(BaseModel):
    name: str
    info_hash: str
    magnet_uri: str
    file_idx: int
    size: int
    seeders: int
    quality: str
    source: str
    language: str


@app.get("/api/search")
async def search(q: str = Query(..., min_length=2)):
    """Search TMDB for movies and TV shows."""
    import httpx
    async with httpx.AsyncClient() as client:
        movies_res = await client.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={"api_key": TMDB_API_KEY, "query": q}
        )
        tv_res = await client.get(
            f"{TMDB_BASE_URL}/search/tv",
            params={"api_key": TMDB_API_KEY, "query": q}
        )
    
    movies = movies_res.json().get("results", [])
    tv_shows = tv_res.json().get("results", [])
    
    return {
        "movies": [
            {
                "id": m["id"],
                "title": m["title"],
                "poster_path": m.get("poster_path"),
                "release_date": m.get("release_date"),
                "overview": m.get("overview", ""),
                "media_type": "movie"
            }
            for m in movies
        ],
        "tv_shows": [
            {
                "id": t["id"],
                "title": t["name"],
                "poster_path": t.get("poster_path"),
                "first_air_date": t.get("first_air_date"),
                "overview": t.get("overview", ""),
                "media_type": "tv"
            }
            for t in tv_shows
        ]
    }


@app.get("/api/torrents/{content_type}/{tmdb_id}")
async def get_torrents(
    content_type: str,
    tmdb_id: str,
    season: Optional[int] = None,
    episode: Optional[int] = None
):
    """Get torrent options from Torrentio for a TMDB ID."""
    if content_type not in ("movie", "series"):
        raise HTTPException(400, "content_type must be 'movie' or 'series'")
    
    if content_type == "series" and (season is None or episode is None):
        raise HTTPException(400, "season and episode required for series")
    
    manager = TorrentioManager()
    try:
        options = await manager.get_streams(content_type, tmdb_id, season, episode)
        return [
            {
                "name": opt.name,
                "info_hash": opt.info_hash,
                "magnet_uri": opt.magnet_uri,
                "file_idx": opt.file_idx,
                "size": opt.size,
                "seeders": opt.seeders,
                "quality": opt.quality,
                "source": opt.source,
                "language": opt.language
            }
            for opt in options
        ]
    finally:
        await manager.close()


@app.get("/api/stream/{info_hash}")
async def stream_torrent(info_hash: str, file_idx: int = 0):
    """Stream a torrent file via HTTP (placeholder - requires libtorrent integration)."""
    # This would use libtorrent to download and stream the file
    # For now, return a placeholder
    return {"message": "Streaming endpoint - requires libtorrent implementation", "info_hash": info_hash, "file_idx": file_idx}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)