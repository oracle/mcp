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
from bs4 import BeautifulSoup
import hashlib
from fastmcp import FastMCP
import logging
import markdownify as md
from pathlib import PurePath, Path
from pocketsearch import PocketSearch, PocketWriter
import re
import shutil
import zipfile

# Working home directory
HOME_DIR = Path.home().joinpath(PurePath(".oracle/oracle-db-mcp-server"))

# Index
INDEX = None
INDEX_FILE = HOME_DIR.joinpath(PurePath("index.db"))
INDEX_VERSION="1.0.0"
INDEX_VERSION_FILE = HOME_DIR.joinpath(PurePath("index.version"))
CONTENT_CHECKSUM_FILE = HOME_DIR.joinpath(PurePath("content.checksum"))

# Resources folder
RESOURCES_DIR = HOME_DIR.joinpath(PurePath("resources"))

# Temp directory for zip file extraction
ZIP_TEMP_OUTPUT = HOME_DIR.joinpath("zip_temp")

PREPROCESS = "BASIC"

logger = logging.getLogger(__name__)


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
    """
)


@mcp.tool()
def search_oracle_database_documentation(
        search_query: str,
        max_results: int = 4,
) -> list[str]:
    """Search for information about how to use Oracle Database for a query string and return a list of results.

    Args:
        search_query: The search phrase to search for.
        max_results: The maximum number of results to return, defaults to 4.

    Usage:
        search_oracle_database_documentation(search_query="create table syntax")
        search_oracle_database_documentation(search_query="alter a parameter", max_results=13)
        search_oracle_database_documentation(search_query="database user concept", max_results=20)
        search_oracle_database_documentation(search_query="data use case domains best practices", max_results=15)
        search_oracle_database_documentation(search_query="external table definition", max_results=100)
        Returns:
            A list of results.
            Each result a string in Markdown format with the most relevant search topic.

    """
    logger.info(f"query={search_query!r}")
    return search_index(search_query, max_results)


# Function to search the index
def search_index(query_str: str, limit: int = 4) -> list[str]:
    """
    Search the index for the query string and return matching sections with context.
    Returns a list of content.
    """
    results = []
    hits = INDEX.search(text=query_str)
    finds = 0
    for hit in hits:
        results.append(hit.text)
        finds += 1
        if finds >= limit:
            break
    return results


def maintain_content(path: str) -> None:
    """Maintains the content for the MCP server.
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

    location = Path(path)
    if not location.exists():
        logger.error(f"Provided path does not exist: {location}")
        return

    # Get the old index checksum, if it exists
    content_checksum = get_file_content(CONTENT_CHECKSUM_FILE)

    # Get the old index version, if it exists
    index_version = get_file_content(INDEX_VERSION_FILE)

    # Only directories and zip files are currently supported
    if location.is_file() and not location.suffix == '.zip':
        logger.error(f"Unsupported file type: {location}. Must be a zip file or directory.")
        return

    # Calculate the checksum of the input directory or zip file
    logger.debug(f"Calculating checksum for location: {location}")
    input_checksum = shasum_directory(location)
    logger.debug(f"Checksum is {input_checksum} for location '{location}'")

    # See whether checksum matches the old index checksum and the index has not changed
    if input_checksum == content_checksum and index_version == INDEX_VERSION:
        logger.info("Index is up to date, no changes needed.")
        return
    # Data has changed, re-index
    else:
        if input_checksum != content_checksum:
            logger.info("Checksum has changed.")
            logger.debug(f"Old index checksum: {content_checksum}, New input checksum: {input_checksum}")

        if index_version != INDEX_VERSION:
            logger.info("Index version has changed.")
            logger.debug(f"Old index version: {index_version}, New index version: {INDEX_VERSION}")

        INDEX_FILE.unlink(missing_ok=True)
        logger.info("Recreating index...")
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

        update_content(location)

        # Write the new checksum to the checksum file
        logger.debug(f"Writing new checksum {input_checksum} to {CONTENT_CHECKSUM_FILE}")
        write_file_content(CONTENT_CHECKSUM_FILE, input_checksum)

        if index_version != INDEX_VERSION:
            # Write index version to version file
            logger.debug(f"Writing index version {INDEX_VERSION} to {INDEX_VERSION_FILE}")
            write_file_content(INDEX_VERSION_FILE, INDEX_VERSION)

        # Delete temporary zip output directory if it exists
        if Path(ZIP_TEMP_OUTPUT).exists():
            logger.debug(f"Removing temporary zip output directory: {zip_output}")
            shutil.rmtree(zip_output)


def update_content(location: Path) -> None:
    """Updates the stored content with the source provided.

    Args:
        location (Path): The path to the documentation directory.
    Returns:
        None
    """
    logger.debug("Updating content")

    files_processed = 0
    for file in location.rglob("*"):
        process_file(file)
        files_processed += 1
    logger.info(f"Processed {files_processed} files from '{location}'.")

    logger.debug("Optimizing index...")
    optimize_index()
    logger.debug("Index optimized")


def process_file(file: Path) -> None:
    """Process the file."""
    # Only index html file
    if file.suffix == ".html" or file.suffix == ".htm":
        name = file.stem.lower()
        # Ignore ReadMes, table of contents, indexes
        if name not in ("readme", "toc", "index"):
            content_chunks = convert_to_markdown_chunks(file)
            update_index(content_chunks)


def optimize_index() -> None:
    """Optimizes index."""
    ps = PocketSearch(db_name=INDEX_FILE, writeable=True)
    ps.optimize()


def update_index(content: list[str]) -> None:
    """Update the index with content.

    Args:
        content list[str]: The list of HTML content to index.
    Returns:
        None
    """
    global INDEX
    with PocketWriter(db_name=INDEX_FILE) as writer:
        for segment in content:
            writer.insert(text=segment)


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


def convert_to_markdown_chunks(file: Path) -> list[str]:
    """Convert an HTML file to Markdown format.

    Args:
        file (Path): The path to the HTML file.

    Returns:
        str: The converted Markdown content.
    """
    logger.debug(f"Converting {file} to Markdown format.")

    with file.open("r", encoding="utf-8") as f:
        html = f.read()

        if PREPROCESS == "ADVANCED":
            # Preprocess HTML to remove boilerplate and navigation
            html = preprocess_html(html)

        # Convert HTML to Markdown
        markdown = md.markdownify(html)
        if PREPROCESS != "NONE":
            markdown = remove_markdown_urls(markdown)

        pattern = r'(^#{1,6}\s+[^\n]*\n?)(.*?)(?=(?:^#{1,6}\s+|\Z))'

        # Find all matches with re.MULTILINE and re.DOTALL flags
        matches = re.finditer(pattern, markdown, re.MULTILINE | re.DOTALL)

        # Create sections list
        sections = []
        for match in matches:
            # Get heading without the leading "### "
            heading = re.sub("^#{1,6}\\s+", "", match.group(1).strip())
            # Get content without URLs within them
            content = match.group(2).strip()
            sections.append(heading + "\n\n" + content)

        if len(sections) == 0:
            return [markdown]
        else:
            return sections


def remove_markdown_urls(text):
    # Remove Markdown links [text](url) and replace with just the text
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)

    # Remove URLs with GUIDs (32-char hex with hyphens)
    text = re.sub(r'https?://[^\s]*[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}[^\s]*', '', text)

    # Remove URLs with long hex strings (likely file hashes or identifiers)
    text = re.sub(r'https?://[^\s]*[a-f0-9]{16,}[^\s]*', '', text)

    # Remove standalone URLs that start with http/https
    text = re.sub(r'https?://[^\s]+', '', text)

    # Clean up extra whitespace left by removed URLs
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    return text.strip()


def preprocess_html(html_content: str) -> str:
    """Preprocess HTML to remove boilerplate and navigation elements.

    Args:
        html_content (str): The raw HTML content.

    Returns:
        str: Cleaned HTML content ready for markdown conversion.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style tags
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()

    # Remove navigation elements
    for tag in soup.find_all(['nav', 'header', 'footer']):
        tag.decompose()

    # Remove elements with navigation-related classes/ids
    nav_classes = [
        'noscript', 'alert', 'pull-left', 'pull-right', 'skip', 'navigation',
        'breadcrumb', 'nav-', 'header-', 'footer-', 'menu', 'sidebar', 'toc'
    ]
    for nav_class in nav_classes:
        for tag in soup.find_all(attrs={'class': lambda x: x and any(nav_class in str(cls).lower() for cls in (x if isinstance(x, list) else [x]))}):
            tag.decompose()
        for tag in soup.find_all(attrs={'id': lambda x: x and nav_class in str(x).lower()}):
            tag.decompose()

    # Remove common Oracle doc boilerplate text patterns
    boilerplate_patterns = [
        r'JavaScript.*(?:disabled|enabled).*browser',
        r'Skip navigation.*',
        r'Oracle®.*(?:Database.*)?(?:Reference|Guide|Manual|Documentation)',
        r'Release \d+[a-z]*[\s-]*[A-Z0-9-]*',
        r'Previous.*Next',
        r'All Classes.*',
        r'Overview.*Package.*Class.*Use.*Tree.*Deprecated.*Index.*Help'
    ]

    for pattern in boilerplate_patterns:
        for tag in soup.find_all(string=re.compile(pattern, re.IGNORECASE)):
            parent = tag.parent if hasattr(tag, 'parent') else None
            if parent:
                parent.decompose()

    # Remove elements likely to be navigation by common Oracle doc structure
    # Remove elements with common Oracle navigation text content
    nav_text_patterns = [
        'Skip navigation links',
        'JavaScript is disabled on your browser',
        'All Classes',
        'SEARCH:'
    ]

    for pattern in nav_text_patterns:
        for element in soup.find_all(string=lambda text: text and pattern in text):
            parent = element.parent if hasattr(element, 'parent') else None
            if parent:
                parent.decompose()

    return str(soup)


def build_folder_structure() -> None:
    """Builds the home directory structure."""
    if not RESOURCES_DIR.exists():
        RESOURCES_DIR.mkdir(parents=True)


def get_file_content(path: str) -> str:
    """Reads the content of a file and returns it or 'N/A' if the file does not exist.

        Args:
            file (Path): The path to the file.
    """
    if Path(path).exists():
        with Path(path).open("r") as f:
            return f.read().strip()
    else:
        return "N/A"


def write_file_content(path: str, content: str) -> None:
    """Writes the content to a file."""
    with Path(path).open("w") as f:
        f.write(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Oracle Database Documentation MCP Server.")
    parser.add_argument("-doc", type=str,
                        help="Path to the documentation input zip file or extracted directory.")
    parser.add_argument("-mcp", action="store_true", help="Run the MCP server.")
    parser.add_argument("-log-level", type=str, default="ERROR",
                        help="Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).")
    parser.add_argument("-mode", choices=["stdio", "http"], default="stdio")
    parser.add_argument("-host", type=str, default="0.0.0.0",
                        help="The IP address that the MCP server is reachable at.")
    parser.add_argument("-port", type=int, default="8000",
                        help="The port that the MCP server is reachable at.")
    parser.add_argument("-preprocess", type=str, default="BASIC",
                        help="Preprocessing level of documentation (NONE, BASIC, ADVANCED).")
    args = parser.parse_args()

    return args


def main():
    """Main entrypoint for the Oracle Documentation MCP server."""

    # Parse command line arguments
    args = parse_args()

    # Build the home directory structure, needed also for the log file
    build_folder_structure()

    # Set up logging
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Set log level
    logging.basicConfig(filename=HOME_DIR.joinpath(Path('oracle-db-doc.log')), filemode='w', level=logging.ERROR)
    logger.setLevel(getattr(logging, args.log_level.upper(), logging.ERROR))

    if args.doc and args.mcp:
        logger.error("Cannot specify both -doc and -mcp options at the same time.")
        return

    if args.doc:
        global PREPROCESS
        PREPROCESS = args.preprocess.upper()
        maintain_content(args.doc)

    if args.mcp:

        # If no index is present (not index was built), refuse to start the server.
        if not INDEX_FILE.exists():
            logger.error(f"Index does not exist. Please create the index first via the '-doc' option.")
            return

        global INDEX
        logger.debug("Opening index file.")
        INDEX = PocketSearch(db_name=INDEX_FILE)

        logger.info("Serving MCP server for Oracle documentation.")
        if args.mode == "stdio":
            mcp.run(transport="stdio", show_banner=False)
        elif args.mode == "http":
            mcp.run(transport="http", host=args.host, port=args.port, show_banner=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        None
