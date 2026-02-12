#!/usr/bin/env python3
"""
Lens API Configuration Module

Handles HTTP client initialization and configuration for lens API.
"""

import os
import logging
from typing import Optional
import requests
from urllib.parse import urljoin

# Module-level logger
logger = logging.getLogger("lens-mcp.config")

# Global HTTP session
http_session: Optional[requests.Session] = None
base_url: Optional[str] = None

def init_lens_client():
    """Initialize lens HTTP client with configuration."""
    global http_session, base_url
    logger.info("🔧 Initializing lens HTTP client...")
    
    try:
        # Get base URL from environment variable or use default
        base_url = os.getenv('LENS_API_BASE_URL', 'http://localhost:8000')
        
        # Create HTTP session with authentication
        http_session = requests.Session()
        
        # Add authentication if API key is provided
        api_key = os.getenv('LENS_API_KEY')
        if api_key:
            http_session.headers.update({
                'Authorization': f'Token {api_key}',
                'Content-Type': 'application/json'
            })
            logger.info("✅ API key authentication configured")
        else:
            logger.warning("⚠️  No API key found. Set LENS_API_KEY environment variable if required")
            http_session.headers.update({
                'Content-Type': 'application/json'
            })
        
        # Test connectivity
        try:
            logger.debug("🧪 Testing lens API connectivity...")
            test_url = urljoin(base_url, '/instances/')
            response = http_session.get(test_url, timeout=10)
            if response.status_code in [200, 401, 403]:  # 401/403 means API is reachable but auth might be needed
                logger.info(f"✅ Lens API connectivity test passed. Base URL: {base_url}")
            else:
                logger.warning(f"⚠️  Lens API connectivity test returned status {response.status_code}")
        except Exception as test_e:
            logger.warning(f"⚠️  Lens API connectivity test failed: {test_e}")
            
        logger.info("✅ Lens HTTP client initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize lens HTTP client: {e}")
        logger.error("Please ensure LENS_API_BASE_URL environment variable is set")

def get_http_session() -> Optional[requests.Session]:
    """Get the initialized HTTP session."""
    return http_session

def get_base_url() -> Optional[str]:
    """Get the configured base URL."""
    return base_url

def is_initialized() -> bool:
    """Check if lens client is initialized."""
    return http_session is not None and base_url is not None

def make_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make an authenticated HTTP request to the lens API."""
    if not is_initialized():
        raise RuntimeError("Lens client not initialized. Call init_lens_client() first.")
    
    url = urljoin(base_url, endpoint)
    logger.debug(f"🌐 Making {method.upper()} request to: {url}")
    
    response = http_session.request(method, url, **kwargs)
    logger.debug(f"📡 Response status: {response.status_code}")
    
    return response
