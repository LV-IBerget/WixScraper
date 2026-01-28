"""Utility functions for Wix Scraper."""
import asyncio


async def scroll_to_bottom(page):
    """Scroll to the bottom of the page to load all content."""
    pageHeight = await page.evaluate('document.body.scrollHeight')
    for i in range(0, pageHeight, 100):
        await page.evaluate(f'window.scrollTo(0, {i})')
        await asyncio.sleep(0.1)
    await asyncio.sleep(1)
