"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio
import threading
from unittest.mock import MagicMock, Mock

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import oracle.oci_postgresql_runtime_mcp_server.server as server_module


class BlockingQuery:
    def __init__(self, value, *, error=None):
        self.value = value
        self.error = error
        self.started = threading.Event()
        self.release = threading.Event()
        self.wait_expired = False
        self.thread_id = None
        self.cursor = MagicMock()
        self.cursor.__enter__.return_value = self.cursor
        self.result_cursor = MagicMock()
        self.result_cursor.__enter__.return_value = self.result_cursor
        self.result_cursor.description = [("value",)]
        self.result_cursor.statusmessage = "SELECT 1"
        self.result_cursor.fetchmany.return_value = [(value,)]
        self.result_cursor.execute.side_effect = self.execute
        self.connection = MagicMock()
        self.connection.__enter__.return_value = self.connection
        self.connection.cursor.side_effect = self.open_cursor

    def open_cursor(self, name="", **kwargs):
        return self.result_cursor if name else self.cursor

    def execute(self, sql, params=None):
        self.thread_id = threading.get_ident()
        self.started.set()
        # Bound failures even if an older framework blocks the event loop.
        if not self.release.wait(timeout=5):
            self.wait_expired = True
            raise RuntimeError("SQL blocked the event loop until the test gate expired")
        if self.error:
            raise self.error

    def assert_cleaned_up(self):
        assert self.connection.read_only is True
        self.connection.__enter__.assert_called_once_with()
        self.connection.__exit__.assert_called_once()
        self.connection.rollback.assert_called_once_with()
        self.connection.commit.assert_not_called()
        self.cursor.__exit__.assert_called_once()
        self.result_cursor.__exit__.assert_called_once()


def configure_queries(monkeypatch, *queries):
    monkeypatch.setattr(
        server_module,
        "config",
        {"connections": {"app-db": {"dbname": "app_db"}}},
    )
    monkeypatch.setattr(server_module, "config_error_msg", None)
    connect = Mock(side_effect=[query.connection for query in queries])
    monkeypatch.setattr(server_module.psycopg, "connect", connect)
    return connect


async def wait_for_execution(query):
    assert await asyncio.to_thread(query.started.wait, 5), "SQL did not start"
    assert not query.wait_expired, "SQL blocked the event loop"


def start_query(client, value):
    return asyncio.create_task(
        client.call_tool(
            "execute_query",
            {"connection_name": "app-db", "sql": f"select {value} as value"},
        )
    )


@pytest.mark.asyncio
async def test_blocking_query_keeps_runtime_info_responsive(monkeypatch):
    query = BlockingQuery(11)
    configure_queries(monkeypatch, query)
    async with Client(server_module.mcp) as client:
        task = start_query(client, query.value)
        try:
            await wait_for_execution(query)
            info = await asyncio.wait_for(client.call_tool("get_runtime_info", {}), 2)
            assert info.data["project"] == "oracle.oci-postgresql-runtime-mcp-server"
            assert not task.done()
            assert not query.release.is_set()
            assert query.thread_id != threading.get_ident()
        finally:
            query.release.set()
            await asyncio.gather(task, return_exceptions=True)
        assert (await task).data["rows"] == [{"value": 11}]
    query.assert_cleaned_up()


@pytest.mark.asyncio
@pytest.mark.parametrize("first_fails", [False, True])
async def test_overlapping_queries_keep_resources_independent(monkeypatch, first_fails):
    if first_fails:
        # Traceback rendering for this expected error is outside the concurrency check.
        monkeypatch.setattr("fastmcp.server.server.logger.exception", Mock())
    first = BlockingQuery(11, error=RuntimeError("first query failed") if first_fails else None)
    second = BlockingQuery(22)
    connect = configure_queries(monkeypatch, first, second)
    async with Client(server_module.mcp) as client:
        first_task = start_query(client, first.value)
        second_task = None
        try:
            await wait_for_execution(first)
            second_task = start_query(client, second.value)
            await wait_for_execution(second)
            assert first.thread_id != second.thread_id
            assert not first_task.done()
            assert not second_task.done()
            first.release.set()
            if first_fails:
                with pytest.raises(ToolError, match="first query failed"):
                    await asyncio.wait_for(asyncio.shield(first_task), 2)
            else:
                first_result = await asyncio.wait_for(asyncio.shield(first_task), 2)
                assert first_result.data["rows"] == [{"value": 11}]
            first.assert_cleaned_up()
            assert not second_task.done()
            second.connection.rollback.assert_not_called()
            second.connection.__exit__.assert_not_called()
            second.result_cursor.__exit__.assert_not_called()
            second.release.set()
            second_result = await asyncio.wait_for(asyncio.shield(second_task), 2)
            assert second_result.data["rows"] == [{"value": 22}]
        finally:
            first.release.set()
            second.release.set()
            await asyncio.gather(
                *(task for task in (first_task, second_task) if task is not None),
                return_exceptions=True,
            )
    assert connect.call_count == 2
    second.assert_cleaned_up()
