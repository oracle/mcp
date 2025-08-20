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
import markdownify as md
import logging
from fastmcp import FastMCP
from pathlib import Path
import shutil
from pocketsearch import Schema, Text, PocketSearch, PocketWriter
import zipfile

INDEX = None
INDEX_NAME = Path("index.db")
INDEX_CHECKSUM_FILE = Path("index.checksum")
ZIP_TEMP_OUTPUT = "zip_temp"

logger = logging.getLogger(__name__)
logging.basicConfig(filename='oracle-db-doc.log', filemode='w', level=logging.ERROR)


# Class for index structure
class IndexSchema(Schema):
    entry_name = Text(is_id_field=True)
    entry = Text(index=True)


mcp = FastMCP(
    "oracle-doc",
    instructions="""
    # Oracle Database Documentation MCP Server.

    This server is used to search the Oracle Database documentation for information.
    It can be used to find information about SQL syntax, PL/SQL, database concepts, best practices, examples and many more.
    It is also used to search the official Oracle Database documentation for additional information on a particular feature, its use cases, restrictions or interoperability with other features.
    The tool should be used to augment any existing knowledge or to find information that is not available in the current context.
    The server is designed to search the Oracle Database documentation for search phrases and will return a list of results.

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
        "markdownify>=1.2.0",
        "fastmcp>=2.11.3",
        "pocketsearch>=0.40.0",
    ]
)


@mcp.tool()
def search(
        search_query: str,
        max_results: int = 10,
) -> list[str]:
    """Search for information about how to use Oracle Database for a query string and return a list of results.

    Args:
        search_query: The search phrase to search for.
        max_results: The maximum number of results to return, defaults to 20.

    Usage:
        search(search_query="create table syntax")
        search(search_query="alter a parameter", max_results=13)
        search(search_query="database user concept", max_results=20)
        search(search_query="data use case domains best practices", max_results=15)
        search(search_query="external table definition", max_results=100)

        Returns:
            A list of results.
            Each result a string in Markdown format with the most relevant search topic.

    """
    logger.info(f"query={search_query!r}")
    return search_index(search_query, max_results)


def open_index() -> None:
    global INDEX
    logger.debug("Opening index file.")
    INDEX = PocketSearch(db_name=INDEX_NAME, schema=IndexSchema)


# Function to search the index
def search_index(query_str: str, limit: int = 10) -> list[str]:
    """
    Search the index for the query string and return matching sections with context.
    Returns a list of content.
    """
    results = []
    hits = INDEX.search(entry=query_str)
    finds = 0
    for hit in hits:
        results.append(hit.entry)
        finds += 1
        if finds >= limit:
            break
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
    if path is None and INDEX_NAME.exists():
        open_index()
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
    logger.debug(f"Calculating checksum for location: {location}")
    input_checksum = shasum_directory(location)
    logger.debug(f"Checksum is {input_checksum} for location '{location}'")

    # See whether checksum matches the old index checksum
    if input_checksum == index_checksum:
        logger.info("Index is up to date, no changes needed.")
        open_index()
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

        update_index(location)
        open_index()

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

    with PocketWriter(db_name=INDEX_NAME, schema=IndexSchema) as writer:

        files_indexes = 0
        for ext in ("*.html", "*.htm"):
            for file in location.rglob(ext):
                logger.debug(f"Indexing file: {file}")
                markdown_content = convert_to_markdown(file)
                writer.insert_or_update(entry_name=str(file.relative_to(location)), entry=markdown_content)
                files_indexes += 1

        logger.info(f"Indexed {files_indexes} html files from '{location}'.")

    # Optimize index for query performance
    index = PocketSearch(db_name=INDEX_NAME, schema=IndexSchema, writeable=True)
    logger.debug("Optimizing index...")
    index.optimize()

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

    with file.open("r", encoding="utf-8") as f:
        html = f.read()

        # Convert HTML to Markdown
        return md.markdownify(html)


def main():
    """Main entrypoint for the Oracle Documentation MCP server."""

    # Set up logging
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Oracle Database Documentation MCP Server.")
    parser.add_argument("-doc", type=str, help="Path to the documentation input zip file or extracted directory.")
    parser.add_argument("-mcp", action="store_true", help="Run the MCP server.")
    parser.add_argument("-log-level", type=str, default="ERROR",
                        help="Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).")
    args = parser.parse_args()

    # Set log level
    logger.setLevel(getattr(logging, args.log_level.upper(), logging.ERROR))

    maintain_index(args.doc)

    if INDEX is None:
        logger.error(f"Index does not exist. Please run the server with a valid doc directory to index.")
        return

    if args.mcp:
        logger.info("Serving MCP server for Oracle documentation.")
        mcp.run()


if __name__ == "__main__":
    main()
