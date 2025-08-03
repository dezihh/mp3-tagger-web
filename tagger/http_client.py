"""
HTTP Client Utilities für MP3 Tagger Web Application

Wiederverwendbare HTTP-Client-Funktionen für alle API-Services.
Zentralisiert Error-Handling, Rate-Limiting und Common Headers.
"""

import aiohttp
import asyncio
import time
import logging
from typing import Dict, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class APIRateLimiter:
    """Rate Limiting für API-Requests"""
    
    def __init__(self):
        self.last_requests: Dict[str, float] = {}
        self.rate_limits: Dict[str, float] = {
            'spotify': 0.1,      # 10 Requests pro Sekunde
            'lastfm': 0.2,       # 5 Requests pro Sekunde  
            'musicbrainz': 1.0,  # 1 Request pro Sekunde
            'discogs': 1.5,      # Streng limitiert
            'acoustid': 0.5      # 2 Requests pro Sekunde
        }
    
    async def wait_if_needed(self, service: str) -> None:
        """Wartet wenn Rate Limit überschritten"""
        if service not in self.rate_limits:
            return
            
        delay = self.rate_limits[service]
        last_request = self.last_requests.get(service, 0)
        time_since_last = time.time() - last_request
        
        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.debug(f"Rate limiting {service}: warte {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        self.last_requests[service] = time.time()


class HTTPClient:
    """Einheitlicher HTTP-Client für alle API-Services"""
    
    def __init__(self):
        self.rate_limiter = APIRateLimiter()
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, headers: Dict[str, str] = None, 
                  service: str = 'default', **kwargs) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        GET Request mit Rate Limiting und Error Handling
        
        Returns:
            Tuple[success: bool, data: Optional[Dict]]
        """
        return await self._request('GET', url, headers=headers, 
                                 service=service, **kwargs)
    
    async def post(self, url: str, data: Any = None, headers: Dict[str, str] = None,
                   service: str = 'default', **kwargs) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        POST Request mit Rate Limiting und Error Handling
        
        Returns:
            Tuple[success: bool, data: Optional[Dict]]
        """
        return await self._request('POST', url, data=data, headers=headers,
                                 service=service, **kwargs)
    
    async def _request(self, method: str, url: str, headers: Dict[str, str] = None,
                      data: Any = None, service: str = 'default', 
                      **kwargs) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Interne Request-Methode mit umfassendem Error Handling"""
        
        if not self.session:
            logger.error("HTTP Session nicht initialisiert")
            return False, None
        
        # Rate Limiting
        await self.rate_limiter.wait_if_needed(service)
        
        # Default Headers
        request_headers = {
            'User-Agent': 'MP3Tagger/1.0 (https://github.com/your-repo)',
            'Accept': 'application/json',
            **(headers or {})
        }
        
        try:
            async with self.session.request(
                method, url, headers=request_headers, 
                data=data, **kwargs
            ) as response:
                
                # Status Code Check
                if response.status == 429:  # Rate Limit
                    logger.warning(f"Rate limit exceeded for {service}: {url}")
                    # Warte länger und versuche nochmal
                    await asyncio.sleep(2.0)
                    return False, None
                
                if response.status == 401:  # Unauthorized
                    logger.error(f"Authorization failed for {service}: {url}")
                    return False, None
                
                if response.status == 404:  # Not Found
                    logger.debug(f"Resource not found for {service}: {url}")
                    return False, None
                
                if response.status >= 500:  # Server Error
                    logger.error(f"Server error {response.status} for {service}: {url}")
                    return False, None
                
                # Content Type Check
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    logger.warning(f"Non-JSON response from {service}: {content_type}")
                    return False, None
                
                # Parse Response
                if response.status == 200:
                    try:
                        data = await response.json()
                        return True, data
                    except Exception as e:
                        logger.error(f"JSON parse error for {service}: {e}")
                        return False, None
                else:
                    logger.warning(f"Unexpected status {response.status} for {service}: {url}")
                    return False, None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout for {service}: {url}")
            return False, None
        except aiohttp.ClientError as e:
            logger.error(f"Client error for {service}: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error for {service}: {e}")
            return False, None


class TokenManager:
    """Token-Management für OAuth APIs wie Spotify"""
    
    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
    
    def store_token(self, service: str, token: str, expires_at: float) -> None:
        """Speichert Access Token mit Ablaufzeit"""
        self.tokens[service] = {
            'token': token,
            'expires_at': expires_at
        }
        
    def get_token(self, service: str) -> Optional[str]:
        """Holt gültigen Token oder None wenn abgelaufen"""
        token_data = self.tokens.get(service)
        if not token_data:
            return None
            
        if datetime.now().timestamp() < token_data['expires_at']:
            return token_data['token']
        else:
            # Token ist abgelaufen
            del self.tokens[service]
            return None
    
    def is_token_valid(self, service: str) -> bool:
        """Prüft ob Token noch gültig ist"""
        return self.get_token(service) is not None


# Globale Instanzen
_http_client = None
_token_manager = TokenManager()


async def get_http_client() -> HTTPClient:
    """Factory für HTTP Client (Context Manager)"""
    return HTTPClient()


def get_token_manager() -> TokenManager:
    """Globaler Token Manager"""
    return _token_manager


# Convenience Functions für häufige API-Patterns
async def spotify_request(endpoint: str, token: str, **kwargs) -> Tuple[bool, Optional[Dict]]:
    """Spotify API Request mit Bearer Token"""
    headers = {'Authorization': f'Bearer {token}'}
    
    async with get_http_client() as client:
        return await client.get(
            f'https://api.spotify.com/v1/{endpoint}',
            headers=headers,
            service='spotify',
            **kwargs
        )


async def lastfm_request(method: str, api_key: str, **params) -> Tuple[bool, Optional[Dict]]:
    """Last.fm API Request"""
    url = 'https://ws.audioscrobbler.com/2.0/'
    params.update({
        'method': method,
        'api_key': api_key,
        'format': 'json'
    })
    
    async with get_http_client() as client:
        return await client.get(url, params=params, service='lastfm')


async def musicbrainz_request(endpoint: str, **params) -> Tuple[bool, Optional[Dict]]:
    """MusicBrainz API Request"""
    url = f'https://musicbrainz.org/ws/2/{endpoint}'
    params.update({'fmt': 'json'})
    
    async with get_http_client() as client:
        return await client.get(url, params=params, service='musicbrainz')
