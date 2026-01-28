"""Wix Scraper - Entry point.

This script scrapes Wix websites and converts them to offline static sites.
"""
import asyncio
from scraper import main


if __name__ == "__main__":
    asyncio.run(main())
