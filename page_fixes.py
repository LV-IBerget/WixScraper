"""Page manipulation functions for fixing Wix pages."""
import asyncio
from utils import scroll_to_bottom
from asset_handlers import makeLocalImages, makeFontsLocal


# Only use this function in compliance with Wix Terms of Service. 
async def delete_wix(page):
    """Remove Wix-specific elements and branding from the page."""
    # Delete the wix header with id WIX_ADS
    await page.evaluate('''() => {
        const element = document.getElementById('WIX_ADS');
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }''')

    # Edit the in-line CSS defined in <style> tag
    # delete any string "--wix-ads"
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            if (element.innerText.includes('--wix-ads')) {
                element.innerText = element.innerText.replace('--wix-ads', '');
            }
        }
    }''')

    # delete any string "Made with Wix"
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('span');
        for (const element of elements) {
            if (element.innerText.includes('Made with Wix') && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }
    }''')

    # Remove all scripts 
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('script');
        for (const element of elements) {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }
    }''')

    # Remove all link tags
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('link');
        for (const element of elements) {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }
    }''')


async def fix_gallery(page):
    """Replace Wix gallery with slick carousel."""
    # If pro-gallery is a class on the page, then we need to fix the gallery
    # Get the gallery element
    gallery = await page.querySelector('.pro-gallery')

    if(gallery != None):
        print("Found gallery! Fixing..")
        
        # Import slick.carousel
        await page.addScriptTag(url='https://cdn.jsdelivr.net/npm/jquery@3.6.4/dist/jquery.min.js')
        await page.addStyleTag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.css')
        await page.addStyleTag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick-theme.css')
        await page.addScriptTag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.min.js')

        # Get all img links
        img_links = await gallery.querySelectorAllEval('img', 'nodes => nodes.map(n => n.src)')
    
        # Create the carousel and insert it two parents above the gallery
        await page.evaluate('''() => {
            const gallery = document.querySelector('.pro-gallery');
            if (gallery && gallery.parentNode && gallery.parentNode.parentNode) {
                const element = document.createElement('div');
                element.className = 'slick-carousel';
                gallery.parentNode.parentNode.insertBefore(element, gallery.parentNode);
            }
        }''')

        # Delete all siblings of the slick carousel
        await page.evaluate('''() => {
            const element = document.querySelector('.slick-carousel');
            if (element) {
                while (element.nextSibling && element.nextSibling.parentNode) {
                    element.nextSibling.parentNode.removeChild(element.nextSibling);
                }
            }
        }''')

        # Add the images to the carousel
        for link in img_links:
            await page.evaluate(f'''() => {{
                const element = document.createElement('img');
                element.src = '{link}';
                element.alt = 'Gallery Image';
                document.querySelector('.slick-carousel').appendChild(element);
            }}''')

        # Add the above evaluation as a script tag
        await page.addScriptTag(content='''
        window.addEventListener('DOMContentLoaded', function() {
        var $jq = jQuery.noConflict();
        $jq(document).ready(function () {
            $jq('.slick-carousel').slick({
                dots: true,
                infinite: true,
                speed: 300,
                slidesToShow: 2,
                responsive: [
                    {
                    breakpoint: 1024,
                    settings: {
                        slidesToShow: 1,
                    }
                    },
                    {
                    breakpoint: 600,
                    settings: {
                        slidesToShow: 1,
                    }
                    }
                ]
            });
        });
        });''')


async def fix_googlemap(page, mapData):
    """Replace Google Maps with Leaflet OpenStreetMap."""
    # Get the one titled = "Google Maps"
    googlemap = await page.querySelector('wix-iframe[title="Google Maps"]')

    if(googlemap != None):
        print("Found Google Maps! Fixing..")

        # Import leaflet
        await page.addStyleTag(url='https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/leaflet.css')

        await page.evaluate('''() => {
            const script = document.querySelector('script');
            if (script && script.parentNode) {
                const element = document.createElement('script');
                element.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/leaflet.js';
                script.parentNode.insertBefore(element, script.nextSibling);
            }
        }''')

        # Add new style tag to the page
        await page.addStyleTag(content='''
        #map { height: 100%; }

        html, body { height: 100%; margin: 0; padding: 0; }

        :root {
        
        --map-tiles-filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7);

        }

        @media (prefers-color-scheme: dark) {
            .map-tiles {
                filter:var(--map-tiles-filter, none);
            }
        }''')

        # Add a new map div next to the google map
        await page.evaluate('''() => {
            const iframe = document.querySelector('iframe[title="Google Maps"]');
            if (iframe && iframe.parentNode) {
                const element = document.createElement('div');
                element.id = 'map';
                iframe.parentNode.insertBefore(element, iframe.nextSibling);
            }
        }''')

        # Delete all siblings of the map div
        await page.evaluate('''() => {
            const element = document.querySelector('#map');
            if (element) {
                while (element.nextSibling && element.nextSibling.parentNode) {
                    element.nextSibling.parentNode.removeChild(element.nextSibling);
                }
            }
        }''')

        content = '''
        window.addEventListener('DOMContentLoaded', function() {

        var map = L.map('map').setView([''' + mapData['latitude'] + ',' + mapData['longitude'] + '],' + mapData['zoom'] + ''');

        // set tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
            className: 'map-tiles'
        }).addTo(map);

        // add marker
        L.marker([''' + mapData['mapMarker']['latitude'] + ',' + mapData['mapMarker']['longitude'] + ''']).addTo(map)
            .bindPopup(" ''' + mapData['mapMarker']['popup'] + ''' ")
            .openPopup();
            
        });'''

        # Instead of addScriptTag, append the entire above script as a <script> at the end of the body
        await page.evaluate('''() => {
            const element = document.createElement('script');
            element.innerHTML = `''' + content + '''`;
            document.querySelector('body').appendChild(element);
        }''')

        # Delete the google map iframe
        await page.evaluate('''() => {
            const element = document.querySelector('iframe[title="Google Maps"]');
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }''')      

        # Add preconnect to openstreetmap
        await page.evaluate('''() => {
            const element = document.createElement('link');
            element.rel = 'preconnect';
            element.href = 'https://a.tile.openstreetmap.org';
            document.querySelector('head').appendChild(element);
            element.href = 'https://b.tile.openstreetmap.org';
            document.querySelector('head').appendChild(element);
            element.href = 'https://c.tile.openstreetmap.org';
            document.querySelector('head').appendChild(element);
        }''')


async def fix_slideshow(page):
    """Replace Wix slideshow with slick carousel."""
    # Get the gallery element
    gallery = await page.querySelector('.wixui-slideshow')

    if(gallery != None):
        print("Found Slideshow! Fixing..")
        
        # Import slick.carousel
        await page.addScriptTag(url='https://cdn.jsdelivr.net/npm/jquery@3.6.4/dist/jquery.min.js')
        await page.addStyleTag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.css')
        await page.addStyleTag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick-theme.css')
        await page.addScriptTag(url='https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.min.js')

        # Create the carousel and insert it two parents above the gallery
        await page.evaluate('''() => {
            const slideshow = document.querySelector('.wixui-slideshow');
            if (slideshow && slideshow.parentNode && slideshow.parentNode.parentNode) {
                const element = document.createElement('div');
                element.className = 'slick-carousel-slides';
                slideshow.parentNode.parentNode.insertBefore(element, slideshow.parentNode);
            }
        }''')

        # Give all images inside slideshow alt tags
        await page.evaluate('''() => {
            const elements = document.querySelectorAll('nav[aria-label="Slides"] li img');
            for (const element of elements) {   
                element.alt = 'Slideshow Image';
            }
        }''')

        slides = await page.querySelectorAll('nav[aria-label="Slides"] li')

        # Ensure first slide is selected
        await asyncio.sleep(5)
        await slides[0].click()

        for slide in slides:
            await slide.click()
            await asyncio.sleep(5)

            slide_content = await page.querySelector('div[data-testid="slidesWrapper"] > div')

            # Get innerHTML of slide_content
            parent = await page.evaluate('(slide_content) => slide_content.innerHTML', slide_content)

            # Get all parents of img tags, iterate over and add them instead
            await page.evaluate(f'''(parent) => {{
                const element = document.createElement('div');
                element.innerHTML = parent;
                document.querySelector('.slick-carousel-slides').appendChild(element);
            }}''', parent)

        # Delete all children of slidesWrapper
        await page.evaluate('''() => {
            const element = document.querySelector('div[data-testid="slidesWrapper"]');
            while (element.firstChild) {
                element.removeChild(element.firstChild);
            }
        }''')

        # Move slick-carousel next to aria-label="Slideshow"
        await page.evaluate('''() => {
           const element = document.querySelector('.slick-carousel-slides');
           const slideshow = document.querySelector('.wixui-slideshow');
           if (element && slideshow && slideshow.parentNode) {
               slideshow.parentNode.insertBefore(element, slideshow.nextSibling);
           }
        }''')

        # Take the class and id from aria-label="Slideshow" and add it to slick-carousel, then delete aria-label="Slideshow"
        await page.evaluate('''() => {
           const element = document.querySelector('.wixui-slideshow');
           const carousel = document.querySelector('.slick-carousel-slides');
           if (element && carousel) {
               carousel.className = element.className + ' slick-carousel-slides';
               carousel.id = element.id;
               if (element.parentNode) {
                   element.parentNode.removeChild(element);
               }
           }
        }''')

        # Make .slick-next class element have the style: right: 75px and .slick-prev class element have the style: left: 75px
        # using style tags
        await page.addStyleTag(content='''
        .slick-next {
            z-index: 100;
            right: 75px;
        }

        .slick-prev {
            z-index: 100;
            left: 75px;
        }''')


# Constants for HTML fixes
slideFix = '''<script>
        window.addEventListener('DOMContentLoaded', function() {
        var $jq = jQuery.noConflict();
        $jq(document).ready(function () {
            $jq('.slick-carousel-slides').slick({
                dots: true,
                infinite: false,
                speed: 300,
                slidesToShow: 1,
                responsive: [
                    {
                    breakpoint: 1024,
                    settings: {
                        slidesToShow: 1,
                    }
                    },
                    {
                    breakpoint: 600,
                    settings: {
                        slidesToShow: 1,
                    }
                    }
                ]
            });
        });
    });</script></body>'''

lightModeFix = '''<style>
        .slick-dots li button:before {
            font-family: 'slick';
            font-size: 6px;
            line-height: 20px;
            position: absolute;
            top: 0;
            left: 0;
            width: 20px;
            height: 20px;
            content: '•';
            text-align: center;
            opacity: .25;
            color: white;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .slick-dots li.slick-active button:before {
            opacity: .75;
            color: white;
        }
    </style></head>'''


async def fix_page(page, wait, hostname, blockPrimaryFolder, darkWebsite, forceDownloadAgain, metatags, mapData):
    """Main function to fix a Wix page - applies all transformations."""
    # Get the current page
    key = page.url.split(hostname)[1]

    print("Current page: " + key)
    
    await asyncio.sleep(wait)
    await scroll_to_bottom(page)
    await delete_wix(page)
    await fix_gallery(page)
    await fix_googlemap(page, mapData)
    await fix_slideshow(page)

    # Defer all scripts
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('script');
        for (const element of elements) {
            element.setAttribute('defer', '');
        }
    }''')

    # In every font-face, add font-display: swap;
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            if (element.innerText.includes('@font-face')) {
                element.innerText = element.innerText.replace('@font-face {', '@font-face { font-display: swap;');
            }
        }
    }''')

    # Remove data-href from every style tag
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('style');
        for (const element of elements) {
            element.removeAttribute('data-href');
            element.removeAttribute('data-url');
        }
    }''')

    # Make all images local
    await makeLocalImages(page, hostname, forceDownloadAgain)

    # Make all fonts local
    await makeFontsLocal(page, hostname, forceDownloadAgain)

    # Meta fixes
    # Delete all meta tags
    await page.evaluate('''() => {
        const elements = document.querySelectorAll('meta');
        for (const element of elements) {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }
    }''')

    # Get metatags for this page, or use defaults
    if(key not in metatags):
        print("Warning: No metatags defined for this page. Using default metatags.")
        # Try to use root metatags if available, otherwise use defaults
        if '/' in metatags:
            key = '/'
        else:
            # Use default values
            title = hostname
            description = f"Content from {hostname}"
            keywords = ""
            canonical = f"https://{hostname}{key}"
            image = f"https://{hostname}/favicon.ico"
            author = ""
            # Set key to empty to skip the metatags[key] access below
            key = None
    
    if key is not None:
        title = metatags[key]['title']
        description = metatags[key]['description']
        keywords = metatags[key]['keywords']
        canonical = metatags[key]['canonical']
        image = metatags[key]['image']
        author = metatags[key]['author']

    # Add all meta tags
    await page.evaluate(f'''() => {{
        const element = document.createElement('title');
        element.innerText = '{title}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'title';
        element.content = '{title}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.property = 'og:title';
        element.content = '{title}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'description';
        element.content = '{description}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.property = 'og:description';
        element.content = '{description}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'keywords';
        element.content = '{keywords}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('link');
        element.rel = 'canonical';
        element.href = '{canonical}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.property = 'og:url';
        element.content = '{canonical}';
        document.querySelector('head').appendChild(element);
    }}''')

    # Twitter meta tags
    await page.evaluate('''() => {
        const element = document.createElement('meta');
        element.name = 'twitter:card';
        element.content = 'summary_large_image';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'twitter:url';
        element.content = '{canonical}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'twitter:title';
        element.content = '{title}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'twitter:description';
        element.content = '{description}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'twitter:image';
        element.content = '{image}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.property = 'og:image';
        element.content = '{image}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate(f'''() => {{
        const element = document.createElement('meta');
        element.name = 'author';
        element.content = '{author}';
        document.querySelector('head').appendChild(element);
    }}''')

    await page.evaluate('''() => {
        const element = document.createElement('meta');
        element.property = 'og:type';
        element.content = 'website';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate('''() => {
        const element = document.createElement('meta');
        element.name = 'viewport';
        element.content = 'width=device-width, initial-scale=1.0';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate('''() => {
        const element = document.createElement('meta');
        element.name = 'robots';
        element.content = 'index, follow';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate('''() => {
        const element = document.createElement('meta');
        element.name = 'googlebot';
        element.content = 'index, follow';
        document.querySelector('head').appendChild(element);
    }''')

    # Favicon links
    await page.evaluate('''() => {
        const element = document.createElement('link');
        element.rel = 'apple-touch-icon';
        element.sizes = '180x180';
        element.href = '/apple-touch-icon.png';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate('''() => {
        const element = document.createElement('link');
        element.rel = 'icon';
        element.type = 'image/png';
        element.sizes = '32x32';
        element.href = '/favicon-32x32.png';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate('''() => {
        const element = document.createElement('link');
        element.rel = 'icon';
        element.type = 'image/png';
        element.sizes = '16x16';
        element.href = '/favicon-16x16.png';
        document.querySelector('head').appendChild(element);
    }''')

    await page.evaluate('''() => {
        const element = document.createElement('link');
        element.rel = 'manifest';
        element.href = '/site.webmanifest';
        document.querySelector('head').appendChild(element);
    }''')

    # Get final HTML and apply fixes
    html = await page.evaluate('document.documentElement.outerHTML')

    html = html.replace('<br>', '')
    html = html.replace('</body>', slideFix)
    if(darkWebsite):
        html = html.replace('</head>', lightModeFix)
    
    # Fix every href to be relative 
    html = html.replace('href="https://' + hostname, 'href="')
    html = html.replace('href="http://' + hostname, 'href="')
    html = html.replace('href="https://www.' + hostname, 'href="')
    html = html.replace('href="http://www.' + hostname, 'href="')
    html = html.replace('href="www.' + hostname, 'href="')
    html = html.replace('href="' + hostname, 'href="')

    # Remove the primaryFolder from any hrefs
    html = html.replace('href="/' + blockPrimaryFolder, 'href="')

    # Any empty hrefs are now root hrefs, replace them with /
    html = html.replace('href=""', 'href="/"')

    # Remove browser-sentry script
    html = html.replace('<script src="https://browser.sentry-cdn.com/6.18.2/bundle.min.js" defer></script>', '')
    html = html.replace('//static.parastorage.com', 'https://static.parastorage.com')

    # Add passive listeners for better performance
    html = html.replace('<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.4/dist/jquery.min.js" defer=""></script>', 
    '''<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.4/dist/jquery.min.js" defer=""></script><script>window.addEventListener('DOMContentLoaded', function() { jQuery.event.special.touchstart = { setup: function( _, ns, handle ) { this.addEventListener("touchstart", handle, { passive: !ns.includes("noPreventDefault") }); } }; jQuery.event.special.touchmove = { setup: function( _, ns, handle ) { this.addEventListener("touchmove", handle, { passive: !ns.includes("noPreventDefault") }); } }; jQuery.event.special.wheel = { setup: function( _, ns, handle ){ this.addEventListener("wheel", handle, { passive: true }); } }; jQuery.event.special.mousewheel = { setup: function( _, ns, handle ){ this.addEventListener("mousewheel", handle, { passive: true }); } }; });</script>''')

    # Add doctype HTML to start 
    html = '<!DOCTYPE html>' + html

    return html
