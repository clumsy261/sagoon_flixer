import httpx
from typing import List, Optional
from pydantic import BaseModel
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

TORRENTIO_BASE_URL = os.getenv("TORRENTIO_BASE_URL", "https://torrentio.strem.fun")
TORRENTIO_TIMEOUT = float(os.getenv("TORRENTIO_TIMEOUT", "30"))


@dataclass
class TorrentOption:
    name: str
    info_hash: str
    magnet_uri: str
    file_idx: int
    size: int
    seeders: int
    quality: str
    source: str
    language: str


class TorrentioManager:
    def __init__(self, base_url: str = None, timeout: float = None):
        self.base_url = base_url or TORRENTIO_BASE_URL
        self.timeout = timeout or TORRENTIO_TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        await self.client.aclose()

    async def get_streams(self, content_type: str, tmdb_id: str, season: int = None, episode: int = None) -> List[TorrentOption]:
        """
        Fetch torrent streams from Torrentio for a given TMDB ID.
        
        Args:
            content_type: "movie" or "series"
            tmdb_id: TMDB ID (numeric, e.g., "550" for Fight Club)
            season: Season number (for series)
            episode: Episode number (for series)
        """
        if content_type == "movie":
            endpoint = f"{self.base_url}/stream/movie/{tmdb_id}.json"
        elif content_type == "series":
            if season is None or episode is None:
                raise ValueError("Season and episode required for series")
            endpoint = f"{self.base_url}/stream/series/{tmdb_id}:{season}:{episode}.json"
        else:
            raise ValueError(f"Invalid content_type: {content_type}")

        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_streams(data.get("streams", []))
        except httpx.HTTPError as e:
            print(f"Torrentio request failed: {e}")
            return []

    def _parse_streams(self, streams: List[dict]) -> List[TorrentOption]:
        options = []
        for stream in streams:
            try:
                name = stream.get("name", "")
                info_hash = stream.get("infoHash", "")
                file_idx = stream.get("fileIdx", 0)
                
                if not info_hash:
                    continue
                
                magnet_uri = f"magnet:?xt=urn:btih:{info_hash}"
                
                behavior_hints = stream.get("behaviorHints", {})
                size = 0
                if "videoSize" in behavior_hints:
                    size = behavior_hints["videoSize"]
                
                quality = "Unknown"
                if "🎬" in name:
                    parts = name.split("🎬")
                    if len(parts) > 1:
                        quality = parts[1].split("👤")[0].strip()
                
                source = "Unknown"
                if "🔗" in name:
                    parts = name.split("🔗")
                    if len(parts) > 1:
                        source = parts[1].split("🎬")[0].strip()
                
                language = "Unknown"
                if "🌐" in name:
                    parts = name.split("🌐")
                    if len(parts) > 1:
                        language = parts[1].split("🔗")[0].strip()
                
                seeders = 0
                if "⬇️" in name:
                    try:
                        seeders = int(name.split("⬇️")[1].split(" ")[0])
                    except:
                        pass
                
                options.append(TorrentOption(
                    name=name,
                    info_hash=info_hash,
                    magnet_uri=magnet_uri,
                    file_idx=file_idx,
                    size=size,
                    seeders=seeders,
                    quality=quality,
                    source=source,
                    language=language
                ))
            except Exception as e:
                print(f"Failed to parse stream: {e}")
                continue
        
        return options

    async def search_content(self, query: str) -> dict:
        """
        Search Torrentio for content (returns both movies and series).
        This uses the Torrentio catalog endpoints.
        """
        # Torrentio doesn't have a direct search API, but we can use the manifest
        # For actual search, we'd typically use TMDB first, then get streams by ID
        pass


async def get_torrent_options(content_type: str, tmdb_id: str, season: int = None, episode: int = None) -> List[TorrentOption]:
    """Convenience function to get torrent options."""
    manager = TorrentioManager()
    try:
        return await manager.get_streams(content_type, tmdb_id, season, episode)
    finally:
        await manager.close()


if __name__ == "__main__":
    import asyncio
    import sys
    
    async def test():
        if len(sys.argv) < 3:
            print("Usage: python torrentio.py <movie|series> <tmdb_id> [season] [episode]")
            return
        
        content_type = sys.argv[1]
        tmdb_id = sys.argv[2]
        season = int(sys.argv[3]) if len(sys.argv) > 3 else None
        episode = int(sys.argv[4]) if len(sys.argv) > 4 else None
        
        options = await get_torrent_options(content_type, tmdb_id, season, episode)
        for opt in options:
            print(f"{opt.name}")
            print(f"  Hash: {opt.info_hash}")
            print(f"  Quality: {opt.quality} | Source: {opt.source} | Lang: {opt.language}")
            print(f"  Size: {opt.size} bytes | Seeders: {opt.seeders}")
            print(f"  Magnet: {opt.magnet_uri[:80]}...")
            print()
    
    asyncio.run(test())