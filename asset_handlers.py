"""Asset handling functions for downloading and processing images and fonts."""
import os
import json
import base64
import hashlib
import requests
from PIL import Image


async def makeLocalImages(page, hostname, forceDownloadAgain):
    """Download all images from the page and convert them to local WebP files."""
    # Create images folder if it doesn't exist in hostname folder
    if not os.path.exists(hostname + '/images'):
        os.makedirs(hostname + '/images')

    # Download all images
    imageLinks = await page.querySelectorAllEval('img', 'nodes => nodes.map(n => n.src)')
    
    # Track mapping of original src to local filename
    image_mapping = {}

    for link in imageLinks:
        # Skip empty links
        if not link:
            continue

        # Handle data URIs (data:image/...)
        if link.startswith('data:'):
            try:
                # Extract the data URI parts: data:image/png;base64,<data>
                header, data = link.split(',', 1)
                # Get the image format from the header
                if 'base64' in header:
                    # Decode base64 data
                    image_data = base64.b64decode(data)
                    # Generate a filename from the hash of the data
                    image_hash = hashlib.md5(image_data).hexdigest()
                    # Try to get format from header (e.g., image/png, image/svg+xml)
                    if 'svg' in header:
                        imageName = image_hash + '.svg'
                        ext = 'svg'
                    elif 'png' in header:
                        imageName = image_hash + '.png'
                        ext = 'png'
                    elif 'jpeg' in header or 'jpg' in header:
                        imageName = image_hash + '.jpg'
                        ext = 'jpg'
                    elif 'gif' in header:
                        imageName = image_hash + '.gif'
                        ext = 'gif'
                    elif 'webp' in header:
                        imageName = image_hash + '.webp'
                        ext = 'webp'
                    else:
                        # Default to png if format unknown
                        imageName = image_hash + '.png'
                        ext = 'png'
                    
                    # Check if already exists
                    if not forceDownloadAgain and os.path.exists(hostname + '/images/' + image_hash + '.webp'):
                        image_mapping[link] = image_hash + '.webp'
                        continue
                    
                    # Save the decoded image
                    with open(hostname + '/images/' + imageName, 'wb') as f:
                        f.write(image_data)
                    
                    # Convert to WebP if not already WebP and not SVG (SVG can't be converted)
                    if ext != 'webp' and ext != 'svg':
                        try:
                            im = Image.open(hostname + '/images/' + imageName)
                            im.save(hostname + '/images/' + image_hash + '.webp', 'webp')
                            # Delete the original
                            os.remove(hostname + '/images/' + imageName)
                            image_mapping[link] = image_hash + '.webp'
                        except Exception as e:
                            print(f"Warning: Could not convert data URI image to WebP: {e}")
                            # Keep the original format if conversion fails
                            image_mapping[link] = imageName
                    elif ext == 'svg':
                        # SVG files can't be converted to WebP, keep as SVG
                        image_mapping[link] = imageName
                    else:
                        image_mapping[link] = image_hash + '.webp'
                else:
                    # Non-base64 data URI, skip for now
                    print(f"Warning: Skipping non-base64 data URI: {link[:50]}...")
                    continue
            except Exception as e:
                print(f"Warning: Error processing data URI image: {e}")
                continue
        else:
            # Regular HTTP/HTTPS image URL
            try:
                # Get the image name
                imageName = link.split('/')[-1].split('?')[0].split('#')[0]  # Remove query params and fragments
                if not imageName or '.' not in imageName:
                    # Generate name from URL hash if no filename
                    image_hash = hashlib.md5(link.encode()).hexdigest()
                    imageName = image_hash + '.jpg'  # Default extension
                
                # If a webp version of the image already exists, skip it
                image_base = imageName.rsplit('.', 1)[0] if '.' in imageName else imageName
                if not forceDownloadAgain and os.path.exists(hostname + '/images/' + image_base + '.webp'):
                    image_mapping[link] = image_base + '.webp'
                    continue

                # Fetch each image and save it to the images folder
                # Download using requests
                r = requests.get(link, allow_redirects=True, timeout=10)
                r.raise_for_status()  # Raise an exception for bad status codes
                
                with open(hostname + '/images/' + imageName, 'wb') as f:
                    f.write(r.content)

                # Convert each image to WebP (skip SVG files)
                file_ext = imageName.rsplit('.', 1)[-1].lower() if '.' in imageName else ''
                if file_ext == 'svg':
                    # SVG files can't be converted to WebP, keep as SVG
                    image_mapping[link] = imageName
                else:
                    try:
                        im = Image.open(hostname + '/images/' + imageName)
                        im.save(hostname + '/images/' + image_base + '.webp', 'webp')
                        # Delete the original image
                        os.remove(hostname + '/images/' + imageName)
                        image_mapping[link] = image_base + '.webp'
                    except Exception as e:
                        print(f"Warning: Could not convert {imageName} to WebP: {e}")
                        # Keep original if conversion fails
                        image_mapping[link] = imageName
            except Exception as e:
                print(f"Warning: Error downloading image {link}: {e}")
                continue

    # Replace all image links with the local image links, using the webp format
    # Convert mapping to JSON for JavaScript
    mapping_json = json.dumps(image_mapping)
    
    await page.evaluate(f'''() => {{
        const imageMapping = {mapping_json};
        const elements = document.querySelectorAll('img');
        for (const element of elements) {{
            const originalSrc = element.src;
            if (imageMapping[originalSrc]) {{
                element.src = '/images/' + imageMapping[originalSrc];
            }} else {{
                // Fallback for images not in mapping (shouldn't happen, but handle gracefully)
                try {{
                    const filename = originalSrc.split('/').slice(-1)[0].split('.')[0];
                    if (filename && filename !== '') {{
                        element.src = '/images/' + filename + '.webp';
                    }}
                }} catch (e) {{
                    console.warn('Could not process image src:', originalSrc);
                }}
            }}
            // remove any srcset
            element.removeAttribute('srcset');
        }}
    }}''')


async def makeFontsLocal(page, hostname, forceDownloadAgain):
    """Download all fonts from the page and make them local."""
    # Make all fonts local
    # Create a fonts folder if it doesn't exist in hostname folder
    if not os.path.exists(hostname + '/fonts'):
        os.makedirs(hostname + '/fonts')

    # Download all fonts, which are parastorage links
    fontLinks = await page.querySelectorAllEval('style', 'nodes => nodes.map(n => n.innerText.match(/url\\((.*?)\\)/g)).flat()')

    # Get all url("//static.parastorage.com...") links
    fontLinks = [link for link in fontLinks if link is not None and 'static.parastorage.com' in link]

    for link in fontLinks:
        # Only get if the link is a font
        if('woff' not in link and 'woff2' not in link and 'ttf' not in link and 'eot' not in link and 'otf' not in link and 'svg' not in link):
            continue
        
        # Remove anything before the link
        link = link.split('static.parastorage.com')[1]
        link = 'static.parastorage.com' + link
        # Get the font name
        fontName = link.split('/')[-1].split(')')[0]
        # Remove any ? parameters
        fontName = fontName.split('?')[0]
        # Remove any # parameters
        fontName = fontName.split('#')[0]
        # Remove any "
        fontName = fontName.replace('"', '')
        
        # If the font already exists, skip it
        if(not forceDownloadAgain and os.path.exists(hostname + '/fonts/' + fontName)):
            continue
        
        r = requests.get("https://" + link, allow_redirects=True)
        open(hostname + '/fonts/' + fontName, 'wb').write(r.content)

    # Replace all font links with the local font links where the font file name is the last item after the last slash
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            if (element.innerText.includes('static.parastorage.com')) {
                // Get all occurences of url("//static.parastorage.com...") links
                var fontLinks = element.innerText.match(/url\\((.*?)\\)/g);

                for (const link of fontLinks) {
                    // Only get if the link is a font
                    // in javascript
                    if(link.includes('woff') || link.includes('woff2') || link.includes('ttf') || link.includes('eot') || link.includes('otf') || link.includes('svg')) {
                            
                        // Get the font name
                        // in javascript, not using split
                        var fontName = link.substring(link.lastIndexOf('/') + 1, link.lastIndexOf(')')); 

                        // Redo the src link
                        element.innerText = element.innerText.replace(link, 'url("/fonts/' + fontName + '")');
                    }
                }

            }
        }
    }''')
