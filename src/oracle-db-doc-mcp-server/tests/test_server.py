"""Tests for indexing and serving local Oracle Database documentation."""

# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import gc
import os
import runpy
import socket
import subprocess
import sys
import warnings
from contextlib import closing
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pocketsearch import PocketSearch

PACKAGE = Path(__file__).resolve().parents[1]
SERVER = PACKAGE / "oracle-db-doc-mcp-server.py"
INDEX_DIRECTORY = Path(".oracle/oracle-db-doc-mcp-server")
TOOL_NAME = "search_oracle_database_documentation"


@pytest.fixture
def home(tmp_path):
    directory = tmp_path / "home"
    directory.mkdir()
    return directory


@pytest.fixture
def documentation(tmp_path):
    directory = tmp_path / "manual"
    directory.mkdir()
    (directory / "queries.html").write_text(
        "<h3>Indexes</h3><p>A synthetic document includes a "
        '<a href="https://example.test/">bitmap index</a>.</p>'
        "<h3>Partitions</h3><p>A partition can contain another bitmap index.</p>",
        encoding="utf-8",
    )
    (directory / "toc.htm").write_text("<p>unindexedtoken</p>", encoding="utf-8")
    (directory / "notes.txt").write_text("unindexedtoken", encoding="utf-8")
    return directory


def script_env(home):
    return {
        **os.environ,
        "HOME": str(home),
        "FASTMCP_CHECK_FOR_UPDATES": "off",
        "UV_LOCKED": "1",
        "UV_OFFLINE": "1",
    }


def run_script(home, *args):
    return subprocess.run(
        [sys.executable, str(SERVER), *args],
        env=script_env(home),
        check=True,
        text=True,
        capture_output=True,
        timeout=15,
    )


def search(home, term):
    index = PocketSearch(db_name=home / INDEX_DIRECTORY / "index.db")
    with closing(index.connection):
        return [hit.text for hit in index.search(text=term)]


def test_directory_maintenance_rebuilds_only_when_content_or_version_changes(home, documentation):
    run_script(home, "idx", "-path", str(documentation))
    index_dir = home / INDEX_DIRECTORY
    state = index_dir / "content.checksum"
    first_checksum = state.read_text()
    assert (index_dir / "index.version").read_text() == "1.0.0"
    assert len(search(home, "bitmap")) == 2
    assert search(home, "unindexedtoken") == []

    unchanged = run_script(home, "-log-level", "INFO", "idx", "-path", str(documentation))
    assert "Index is up to date" in unchanged.stderr
    assert state.read_text() == first_checksum

    (documentation / "queries.html").write_text("<p>Compression works here.</p>", encoding="utf-8")
    run_script(home, "idx", "-path", str(documentation))
    changed_checksum = state.read_text()
    assert changed_checksum != first_checksum
    assert search(home, "bitmap") == []
    assert search(home, "compression") == ["Compression works here."]

    (index_dir / "index.version").write_text("0.0.0")
    stale_version = run_script(home, "-log-level", "INFO", "idx", "-path", str(documentation))
    assert "Index version has changed" in stale_version.stderr
    assert state.read_text() == changed_checksum
    assert (index_dir / "index.version").read_text() == "1.0.0"


def test_archive_is_extracted_and_preprocessed(home, tmp_path):
    archive = tmp_path / "manual.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "guide/queries.htm",
            """<script>javascripttoken</script><style>styletoken</style>
            <nav>navigationtoken</nav><header>headertoken</header><footer>footertoken</footer>
            <p class="breadcrumb">breadcrumbtoken</p><p id="sidebar">sidebartoken</p>
            <p>Release 26ai</p><p>SEARCH: searchtoken</p>
            <h3>Indexes</h3><p>A bitmap index is documented <a href="https://example.test/docs">here</a>.</p>""",
        )
    run_script(home, "idx", "-path", str(archive), "-preprocess", "advanced")

    assert search(home, "bitmap") == ["Indexes\n\nA bitmap index is documented here."]
    for term in (
        "javascripttoken",
        "styletoken",
        "navigationtoken",
        "headertoken",
        "footertoken",
        "breadcrumbtoken",
        "sidebartoken",
        "release",
        "searchtoken",
    ):
        assert search(home, term) == []


def test_none_preprocessing_preserves_links(home, tmp_path):
    directory = tmp_path / "pages"
    directory.mkdir()
    (directory / "page.html").write_text(
        '<p>A <a href="https://example.test/">bitmap index</a>.</p>',
        encoding="utf-8",
    )
    run_script(home, "idx", "-path", str(directory), "-preprocess", "NONE")
    assert search(home, "bitmap") == ["A [bitmap index](https://example.test/)."]


def test_missing_or_unsupported_input_does_not_create_an_index(home, tmp_path):
    missing = run_script(home, "idx", "-path", str(tmp_path / "missing"))
    assert "Provided path does not exist" in missing.stderr
    invalid = tmp_path / "manual.txt"
    invalid.write_text("This is neither a directory nor a ZIP.")
    unsupported = run_script(home, "idx", "-path", str(invalid))
    assert "Unsupported file type" in unsupported.stderr
    assert not (home / INDEX_DIRECTORY / "index.db").exists()


def test_mcp_command_reports_missing_index(home):
    startup = run_script(home, "mcp")
    assert "Please create the index first via the 'idx' subcommand" in startup.stderr
    assert not startup.stdout
    assert not (home / INDEX_DIRECTORY / "index.db").exists()


def test_search_closes_the_sqlite_reader(home, documentation, monkeypatch):
    run_script(home, "idx", "-path", str(documentation))
    monkeypatch.setenv("HOME", str(home))
    search_index = runpy.run_path(str(SERVER))["search_index"]

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", ResourceWarning)
        assert len(search_index("bitmap")) == 2
        gc.collect()

    assert not any("unclosed database" in str(warning.message) for warning in captured)


async def assert_search_tool(client):
    async with client:
        (tool,) = await client.list_tools()
        assert tool.name == TOOL_NAME
        assert tool.input_schema["required"] == ["search_query"]
        assert tool.input_schema["properties"]["max_results"]["default"] == 4

        results = await client.call_tool(TOOL_NAME, {"search_query": "bitmap"})
        assert len(results.data) == 2
        assert all("bitmap index" in snippet for snippet in results.data)
        limited = await client.call_tool(TOOL_NAME, {"search_query": "bitmap", "max_results": 1})
        assert limited.data == results.data[:1]

        empty = await client.call_tool(TOOL_NAME, {"search_query": "unknownterm"})
        assert empty.data == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "command,args",
    [
        (sys.executable, [str(SERVER), "mcp"]),
        (str(Path(sys.executable).with_name("fastmcp")), ["run", "fastmcp.json", "--no-banner"]),
    ],
    ids=["script", "fastmcp-config"],
)
async def test_stdio_search(home, documentation, command, args):
    run_script(home, "idx", "-path", str(documentation))
    transport = StdioTransport(
        command=command,
        args=args,
        env=script_env(home),
        cwd=str(PACKAGE),
        keep_alive=False,
    )
    await assert_search_tool(Client(transport, timeout=10))


@pytest.mark.asyncio
async def test_search_does_not_recreate_removed_index(home, documentation):
    run_script(home, "idx", "-path", str(documentation))
    transport = StdioTransport(
        command=sys.executable,
        args=[str(SERVER), "mcp"],
        env=script_env(home),
        keep_alive=False,
    )
    async with Client(transport, timeout=10) as client:
        index_file = home / INDEX_DIRECTORY / "index.db"
        index_file.unlink()
        result = await client.call_tool(TOOL_NAME, {"search_query": "bitmap"}, raise_on_error=False)

        assert result.is_error
        assert not index_file.exists()


@pytest.mark.asyncio
async def test_http_search(home, documentation):
    run_script(home, "idx", "-path", str(documentation))
    with socket.socket() as address:
        address.bind(("127.0.0.1", 0))
        port = address.getsockname()[1]
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(SERVER),
        "mcp",
        "-mode",
        "http",
        "-host",
        "127.0.0.1",
        "-port",
        str(port),
        env=script_env(home),
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        # Wait for Uvicorn to bind before starting the MCP session.
        async with asyncio.timeout(15):
            while line := await process.stderr.readline():
                if b"Uvicorn running on" in line:
                    break
            else:
                pytest.fail(f"HTTP server exited during startup (status {await process.wait()})")
        await assert_search_tool(Client(f"http://127.0.0.1:{port}/mcp", timeout=10))
    finally:
        if process.returncode is None:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=10)
