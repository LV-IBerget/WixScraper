"""Main scraping logic for Wix Scraper."""
import json
import os
import asyncio
from urllib.parse import urlparse
from pyppeteer import launch
from page_fixes import fix_page


async def main():
    """Main function to scrape a Wix website."""
    # Load the data from the json file
    with open('config.json') as f:
        data = json.load(f)

    site = data['site']
    blockPrimaryFolder = data['blockPrimaryFolder']
    wait = data['wait']
    recursive = data['recursive'].lower() == 'true'
    darkWebsite = data['darkWebsite'].lower() == 'true'
    forceDownloadAgain = data['forceDownloadAgain'].lower() == 'true'
    metatags = data['metatags']
    mapData = data['mapData']

    # Get the hostname
    hostname = urlparse(site).hostname

    # Use microsoft edge as the browser, set width and height to 1920x1080
    browser = None
    try:
        browser = await launch(headless=False, defaultViewport=None, executablePath='C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', args=['--window-size=1920,1080'])
        
        page = await browser.newPage()
        await page.goto(site)
        
        print(site)

        # Fix the first page
        html = await fix_page(page, wait, hostname, blockPrimaryFolder, darkWebsite, forceDownloadAgain, metatags, mapData)

        if not os.path.exists(hostname):
            os.mkdir(hostname)

        with open(hostname + '/index.html', 'w', encoding="utf-8") as f:
            f.write(html)

        if(recursive): 
            seen = []
            # Recursively go through all the local links and save them to the directory
            async def save_links(page, links):
                # Delete all links that are not local
                links = [link for link in links if hostname in link]
                # Delete all links with hash
                links = [link for link in links if '#' not in link]
                links = set(links)
                errors = {}
                for link in links:
                    print(link)
                    if link in seen:
                        continue

                    try:
                        await page.goto(link)
                        
                        seen.append(link)

                        html = await fix_page(page, wait, hostname, blockPrimaryFolder, darkWebsite, forceDownloadAgain, metatags, mapData)

                        # Write each page as index.html to a folder named after the page
                        # Check if the hostname is nested inside another folder
                        # Count number of slashes
                        newlink = link.replace('https://', '').replace('http://', '')

                        if(newlink.count('/') > 1 and blockPrimaryFolder not in newlink.split('/')[1]):
                            # Create the folder
                            if not os.path.exists(hostname + '/' + '/'.join(newlink.split('/')[1:])):
                                os.makedirs(hostname + '/' + '/'.join(newlink.split('/')[1:]))
                            with open(hostname + '/' + '/'.join(newlink.split('/')[1:]) + '/index.html', 'w', encoding="utf-8") as f:
                                f.write(html)
                        else:
                            if not os.path.exists(hostname + '/' + link.split('/')[-1]):
                                os.makedirs(hostname + '/' + link.split('/')[-1])
                            with open(hostname + '/' + link.split('/')[-1] + '/index.html', 'w', encoding="utf-8") as f:
                                f.write(html)
                    
                        await save_links(page, await page.querySelectorAllEval('a', 'nodes => nodes.map(n => n.href)'))

                    except Exception as e:
                        # Check the error count, if over 3, add link to the seen list (ignore)
                        if(link in errors):
                            errors[link] += 1
                        else:
                            errors[link] = 1

                        if(errors[link] > 3):
                            seen.append(link)
                            print("Error: " + link + ". Giving up after 3 attempts. Added to seen list.")
                            continue

                        print(e)
                        print("Error: " + link + ". Try " + str(errors[link]) + " of 3")

                        continue

            await save_links(page, await page.querySelectorAllEval('a', 'nodes => nodes.map(n => n.href)'))
    finally:
        # Always close the browser, even if there's an error
        if browser:
            try:
                await browser.close()
                # Give pyppeteer time to clean up
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Warning: Error closing browser: {e}")
