#!/usr/bin/env python3
"""Seed script for Drishti demo (US-12.01).

This script:
1. Clones a sample repository
2. Indexes it using the Drishti API
3. Runs a verification query
4. Prints a summary report

Usage:
    python scripts/seed_demo.py [--api-url URL] [--repo URL]

Example:
    python scripts/seed_demo.py --api-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_SAMPLE_REPO = "https://github.com/pallets/flask"
SAMPLE_REPOS = {
    "flask": "https://github.com/pallets/flask",
    "fastapi": "https://github.com/tiangolo/fastapi",
    "requests": "https://github.com/psf/requests",
    "httpx": "https://github.com/encode/httpx",
}

SAMPLE_QUERIES = [
    "How does the application handle routing?",
    "What is the main entry point of this application?",
    "How are configuration settings loaded?",
]


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'═' * 60}")
    print(f"  {text}")
    print(f"{'═' * 60}\n")


def print_step(step: int, text: str) -> None:
    """Print a step indicator."""
    print(f"[{step}/4] {text}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"  ✓ {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"  ✗ {text}", file=sys.stderr)


def check_api_health(api_url: str) -> bool:
    """Check if the Drishti API is healthy."""
    try:
        req = Request(f"{api_url}/health/ready", method="GET")
        with urlopen(req, timeout=10) as response:
            return response.status == 200
    except (URLError, TimeoutError):
        return False


def clone_repository(repo_url: str, target_dir: Path) -> bool:
    """Clone a Git repository."""
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Git clone failed: {e.stderr}")
        return False


def ingest_repository(api_url: str, repo_path: str) -> dict | None:
    """Trigger repository ingestion via API."""
    try:
        data = json.dumps({"repo_root": repo_path, "force": False}).encode("utf-8")
        req = Request(
            f"{api_url}/api/v1/ingest",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError) as e:
        print_error(f"Ingestion failed: {e}")
        return None


def run_search_query(api_url: str, repo_path: str, query: str) -> dict | None:
    """Run a search query via API."""
    try:
        data = json.dumps({
            "query": query,
            "repo_root": repo_path,
            "top_k": 5,
        }).encode("utf-8")
        req = Request(
            f"{api_url}/api/v1/search",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError) as e:
        print_error(f"Search failed: {e}")
        return None


def run_ask_query(api_url: str, repo_path: str, question: str) -> str | None:
    """Run an ask query via API (non-streaming)."""
    try:
        data = json.dumps({
            "question": question,
            "repo_root": repo_path,
            "stream": False,
        }).encode("utf-8")
        req = Request(
            f"{api_url}/api/v1/ask",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("answer", "")
    except (URLError, TimeoutError) as e:
        print_error(f"Ask query failed: {e}")
        return None


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed Drishti with a sample repository for demo purposes."
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Drishti API URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--repo",
        default="flask",
        choices=list(SAMPLE_REPOS.keys()) + ["custom"],
        help="Sample repository to use (default: flask)",
    )
    parser.add_argument(
        "--repo-url",
        default=None,
        help="Custom repository URL (use with --repo custom)",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the cloned repository after seeding",
    )
    args = parser.parse_args()

    if args.repo == "custom" and not args.repo_url:
        print_error("--repo-url required when using --repo custom")
        return 1

    repo_url = args.repo_url if args.repo == "custom" else SAMPLE_REPOS[args.repo]

    print_header("Drishti Demo Seeding")
    print(f"API URL: {args.api_url}")
    print(f"Repository: {repo_url}")

    print_step(1, "Checking API health...")
    if not check_api_health(args.api_url):
        print_error("Drishti API is not responding. Is it running?")
        print("\nStart the API with:")
        print("  docker compose up -d")
        print("  # or")
        print("  uv run uvicorn drishti.main:app --reload")
        return 1
    print_success("API is healthy")

    temp_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="drishti-demo-"))
        repo_dir = temp_dir / "repo"

        print_step(2, f"Cloning {args.repo} repository...")
        if not clone_repository(repo_url, repo_dir):
            return 1
        
        file_count = sum(1 for _ in repo_dir.rglob("*") if _.is_file())
        print_success(f"Cloned to {repo_dir} ({file_count} files)")

        print_step(3, "Indexing repository...")
        start_time = time.time()
        result = ingest_repository(args.api_url, str(repo_dir))
        elapsed = time.time() - start_time

        if not result:
            return 1

        chunks = result.get("total_chunks", 0)
        files = result.get("files_indexed", result.get("total_files", 0))
        print_success(f"Indexed {chunks} chunks from {files} files in {elapsed:.1f}s")

        print_step(4, "Running verification queries...")
        
        query = SAMPLE_QUERIES[0]
        print(f"\n  Query: \"{query}\"")
        
        search_result = run_search_query(args.api_url, str(repo_dir), query)
        if search_result:
            results_count = len(search_result.get("results", []))
            print_success(f"Search returned {results_count} results")

        print("\n  Generating answer (this may take a moment)...")
        answer = run_ask_query(args.api_url, str(repo_dir), query)
        if answer:
            preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"\n  Answer preview:\n  {preview}")

        print_header("Demo Seeding Complete!")
        print(f"Repository indexed: {repo_dir}")
        print(f"Total chunks: {chunks}")
        print(f"Total files: {files}")
        print(f"\nYou can now use the Drishti UI at: http://localhost:3000")
        print(f"Or query the API directly at: {args.api_url}/api/v1/ask")

        if args.keep:
            print(f"\nRepository kept at: {repo_dir}")
        
        return 0

    finally:
        if temp_dir and not args.keep:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
