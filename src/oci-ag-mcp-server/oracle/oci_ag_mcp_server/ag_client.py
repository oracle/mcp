"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import time
import aiohttp

from .consts import REQUEST_TIMEOUT, AG_API_VERSION


class AccessGovernanceClient:
    def __init__(self):
        self.base_url = os.getenv("AG_BASE_URL")
        self.token_url = os.getenv("OCI_TOKEN_URL")
        self.client_id = os.getenv("OCI_AG_CLIENT_ID")
        self.client_secret = os.getenv("OCI_AG_CLIENT_SECRET")
        self.scope = os.getenv("AG_SCOPE")

        self._token: str | None = None
        self._token_expiry: float = 0

    # ---------- INIT ----------

    def _validate_env(self):
        required = {
            "AG_BASE_URL": self.base_url,
            "OCI_TOKEN_URL": self.token_url,
            "OCI_AG_CLIENT_ID": self.client_id,
            "OCI_AG_CLIENT_SECRET": self.client_secret,
            "AG_SCOPE": self.scope,
        }

        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    # ---------- SESSION ----------

    def _session(self):
        return aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        )

    # ---------- TOKEN ----------

    async def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 30:
            return self._token

        async with self._session() as session:
            async with session.post(
                self.token_url,
                data={"grant_type": "client_credentials", "scope": self.scope},
                auth=aiohttp.BasicAuth(self.client_id, self.client_secret),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600)

        return self._token

    # ---------- REQUEST ----------

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
    ):
        token = await self._get_token()

        async with self._session() as session:
            async with session.request(
                method,
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {token}"},
                json=json,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    # ---------- PATH ----------

    def _path(self, service: str, resource: str) -> str:
        return f"/access-governance/{service}/{AG_API_VERSION}/{resource}"

    # ---------- API METHODS ----------

    async def list_identities(self):
        return await self._request(
            "GET",
            self._path("identities", "identities"),
        )

    async def get_identity(self, identity_id: str):
        return await self._request(
            "GET",
            self._path("identities", f"identities/{identity_id}"),
        )

    async def list_identity_collections(self):
        return await self._request(
            "GET",
            self._path("access-controls", "identityCollections"),
        )

    async def create_identity_collection(self, payload: dict):
        return await self._request(
            "POST",
            self._path("access-controls", "identityCollections"),
            json=payload,
        )

    async def list_access_reviews(self):
        return await self._request(
            "GET",
            self._path("access-reviews", "accessReviews/identity"),
        )

    async def get_access_review(self, review_id: str):
        return await self._request(
            "GET",
            self._path("access-reviews", f"accessReviews/{review_id}"),
        )

    async def list_orchestrated_systems(self):
        return await self._request(
            "GET",
            self._path("service-administration", "orchestratedSystems"),
        )

    async def list_access_requests(self):
        return await self._request(
            "GET",
            self._path("access-controls", "accessRequests"),
        )

    async def list_access_bundles(self):
        return await self._request(
            "GET",
            self._path("access-controls", "accessBundles"),
        )

    async def create_access_request(self, payload: dict):
        return await self._request(
            "POST",
            self._path("access-controls", "accessRequests"),
            json=payload,
        )