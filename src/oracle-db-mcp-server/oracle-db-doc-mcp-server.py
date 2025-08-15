#
# Since: August 2025
# Author: Gerald Venzl
# Name: main.py
# Description: The Oracle Database Documentation MCP Server
#
# Copyright 2025 Oracle Corporation and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import hashlib
import html2text
import logging
from mcp.server.fastmcp import Context, FastMCP
import os
from pathlib import Path
from pydantic import Field
import shutil
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.fields import Schema, TEXT
import zipfile
from mcp.server.fastmcp import FastMCP


INDEX = None
INDEX_DIR = Path("index")
INDEX_CHECKSUM_FILE = Path(INDEX_DIR / "index.checksum")
INDEX_SCHEMA = Schema(content=TEXT(stored=True))
ZIP_TEMP_OUTPUT = "zip_temp"

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "oracle-doc",
    instructions="""
    # Oracle Database Documentation MCP Server.

    This server is used to search the Oracle Database documentation for information.
    It can be used to find information about SQL syntax, PL/SQL, database concepts, best practices, examples and many more.
    It is also used to search the offical Oracle Database documentation for additional information on a particular feature, its use cases, restrictions or interoperability with other features.
    The tool should be used to augment any existing knowledge or to find information that is not available in the current context.
    The server is desinged to search the Oracle Database documentation for search phrases and will return a list of results.

    You can use the following tools to search the documentation:
    - search: Search the documentation for a query string or search phrase.

    The search tool takes a search query as input and returns a list of results.
    The results are returned as a list of strings containing relevant information.

    ## Best Practices

    - Use the search tool to search for phrases or query strings.
    - Use the search tool to search for specific topics or features.
    - Always use the search tool to search for additional and official information for Oracle Database features.
    - If the search tool returns no results, try to rephrase the query.
    - If the search tool returns too few results, increase the max_results limit.
    - If the search tool returns too many results, reduce the max_results limit.
    - If the search tool returns results that are not relevant, try to refine the query.
    """,
    dependencies=[
        "html2text>=2025.4.15",
        "mcp>=1.12.3",
        "whoosh>=2.7.4",
        "pydantic>=2.10.6",
    ]
)


@mcp.tool()
def search(
    ctx: Context,
    search_query: str = Field(description="The serach phrase to search for."),
    max_results: int = Field(description="The maximum number of results to return.", default=20, gt=0),
    ) -> list[str]:
    """Search for information about how to use Oracle Database for a query string and return a list of results.

    Args:
        search_query: The search phrase to search for.
        max_results: The maximum number of results to return, defaults to 20.

    Usage:
        search(search_query="create table syntax")
        search(search_query="alter a parameter", max_results=13)
        search(search_query="database user concept", max_results=20
        search(search_query="data use case domains best practices", max_results=15)
        search(search_query="external table definition", max_results=100)

        Returns:
            A list of results.
            Each result a string in markdown format with the most relevant serach topic.

    """
    logger.info(f"query={search_query!r}")
    return search_index(search_query, max_results)


# Function to search the index
def search_index(query_str, limit=10) -> list[str]:
    """
    Search the index for the query string and return matching sections with context.
    Returns a list of content.
    """
    results = []
    with INDEX.searcher() as searcher:
        query = QueryParser("content", INDEX.schema).parse(query_str)
        hits = searcher.search(query, limit=limit)
        for hit in hits:
            results.append(hit['content'])
    return results


def maintain_index(path: str) -> None:
    """Creates or updates the index and opens it for the oracle-doc.
    This function checks if the index needs to be created or updated based on the
    contents of the provided location, which can be a directory or a zip file.

    Args:
        path (str): The path to the documentation directory or zip file.

    Returns:
        None
    """
    global INDEX
    logger.info("Maintaining index...")
    # Logic to create or update the index goes here

    # If no path was provided but index exists, open the index.
    if path is None and INDEX_DIR.exists():
        INDEX = open_dir(INDEX_DIR)
        return

    location = Path(path)
    if not location.exists():
        logger.error(f"Provided path does not exist: {location}")
        return

    # Get the old index checksum, if it exists
    index_checksum = "N/A"
    # If the checksum file exists, read the checksum
    if INDEX_CHECKSUM_FILE.exists():
        with INDEX_CHECKSUM_FILE.open("r") as f:
            index_checksum = f.read().strip()

    # Only directories and zip files are currently supported
    if location.is_file() and not location.suffix == '.zip':
        logger.error(f"Unsupported file type: {location}. Must be a zip file or directory.")
        return

    # Calculate the checksum of the input directory or zip file
    input_checksum = shasum_directory(location)
    logger.debug(f"Checksum is {input_checksum} for location '{location}'")

    # See whether checksum matches the old index checksum
    if input_checksum == index_checksum:
        logger.info("Index is up to date. No changes needed.")
        INDEX = open_dir(INDEX_DIR)
        return

    else:
        logger.info("Checksum has changed, updating index.")
        logger.debug(f"Old index checksum: {index_checksum}, New input checksum: {input_checksum}")

        # Extract the zip file to a temporary directory
        if location.is_file() and location.suffix == '.zip':

            # Check if temp output directory exists and remove it
            zip_output = Path(ZIP_TEMP_OUTPUT)
            if zip_output.exists():
                logger.debug(f"Removing existing zip output directory: {zip_output}")
                shutil.rmtree(zip_output)

            logger.debug(f"Creating zip output directory: {zip_output}")
            zip_output.mkdir()
            with zipfile.ZipFile(location, 'r') as zip_ref:
                logger.debug(f"Extracting zip file {location} to {zip_output}")
                zip_ref.extractall(ZIP_TEMP_OUTPUT)

            logger.debug(f"Done creating zip output directory: {zip_output}")
            # Set the location to the extracted output directory
            location = zip_output

        logger.debug("Indexing all html files in the directory...")
        # Also opens the index
        update_index(location)

        # Write the new checksum to the checksum file
        with INDEX_CHECKSUM_FILE.open("w") as f:
            logger.debug(f"Writing new checksum {input_checksum} to {INDEX_CHECKSUM_FILE}")
            f.write(input_checksum)


        # Delete temporary zip output directory if it exists
        if Path(ZIP_TEMP_OUTPUT).exists():
            logger.debug(f"Removing temporary zip output directory: {zip_output}")
            shutil.rmtree(zip_output)


def update_index(location: Path) -> None:
    """Update the index with all HTML files in the directory.

    Args:
        location (Path): The path to the documentation directory.
    Returns:
        None
    """

    global INDEX

    logger.debug("Updating index...")

    if not INDEX_DIR.exists():
        logger.debug(f"Creating index directory: {INDEX_DIR}")
        os.makedirs(INDEX_DIR)

    INDEX = create_in(INDEX_DIR, INDEX_SCHEMA)
    writer = INDEX.writer()

    files_indexes = 0
    for ext in ("*.html", "*.htm"):
        for file in location.rglob(ext):
            logger.debug(f"Indexing file: {file}")
            content = convert_to_markdown(file)
            writer.add_document(content=content)
            files_indexes += 1

    logger.info(f"Indexed {files_indexes} html files from '{location}'.")
    logger.debug("Committing changes to the index.")
    writer.commit()
    logger.info("Indexing complete.")


def shasum_directory(directory: Path) -> str:
    """Calculate the SHA256 checksum of all files in a directory."""
    sha256 = hashlib.sha256()
    for file in sorted(directory.rglob("*")):
        if file.is_file():
            # Include relative path for uniqueness
            sha256.update(str(file.relative_to(directory)).encode())
            with file.open("rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
    return sha256.hexdigest()


def convert_to_markdown(file: Path) -> str:
    """Convert an HTML file to Markdown format.

    Args:
        file (Path): The path to the HTML file.

    Returns:
        str: The converted Markdown content.
    """
    # Placeholder for conversion logic
    logger.debug(f"Converting {file} to Markdown format.")

    # Initialize html2text converter
    converter = html2text.HTML2Text()

    # Configure the converter
    converter.ignore_links = False  # Keep links in the output
    converter.body_width = 0  # Disable line wrapping (optional)
    converter.bypass_tables = False # Converts tables to Markdown

    with file.open("r", encoding="utf-8") as f:
        html = f.read()

        # Convert HTML to Markdown
        return converter.handle(html)


def main():
    """Main entrypoint for the Oracle Documentation MCP server."""

    # Set up logging
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Oracle Documentation MCP Server.")
    parser.add_argument("--doc", type=str, help="Path to the documentation input directory.")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve the MCP server on.")
    parser.add_argument("-mcp", "--mcp", action="store_true", help="Run the MCP server.")
    parser.add_argument("--log-level", type=str, default="ERROR", help="Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).")
    args = parser.parse_args()

    # Set log level
    logger.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    maintain_index(args.doc)

    if INDEX is None:
        logger.error(f"Index does not exist. Please run the server with a valid doc directory to index.")
        return

    if args.mcp:
        logger.info("Serving MCP server for Oracle documentation.")
        mcp.run()


if __name__ == "__main__":
    main()
