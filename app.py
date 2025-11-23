import time
import json
import threading
import cloudscraper
from bs4 import BeautifulSoup
from flask import Flask, render_template, jsonify
import os
import random

app = Flask(__name__)

# Global state
SCRAPING_ACTIVE = False
SCRAPER_THREAD = None
LISTINGS_FILE = 'listings.json'
TARGET_URLS = [
    "https://www.gamermarkt.com/tr/ilanlar/valorant-hesap",
    "https://www.gamermarkt.com/tr/ilanlar/lol-hesap",
    "https://www.gamermarkt.com/tr/ilanlar/cs2-hesap",
    "https://www.gamermarkt.com/tr/ilanlar/cs2-item-skin",
    "https://www.gamermarkt.com/tr/ilanlar/fortnite-hesap"
]

def load_listings():
    if os.path.exists(LISTINGS_FILE):
        try:
            with open(LISTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_listings(listings):
    with open(LISTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(listings, f, ensure_ascii=False, indent=4)

def scrape_worker():
    global SCRAPING_ACTIVE
    scraper = cloudscraper.create_scraper()
    
    print("Scraper thread started...")
    
    # Load existing listings into a map to prevent duplicates and allow updates
    existing_data = load_listings()
    listings_map = {item['id']: item for item in existing_data}
    
    while SCRAPING_ACTIVE:
        
        for base_url in TARGET_URLS:
            if not SCRAPING_ACTIVE:
                break
            
            print(f"Starting category: {base_url}")
            page = 1
            first_page_ids = set() # To detect loops
            
            while SCRAPING_ACTIVE:
                # Construct URL
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url}?page={page}"
                
                print(f"Scraping: {url}")
                
                try:
                    response = scraper.get(url)
                    if response.status_code != 200:
                        print(f"Failed to fetch {url}, status: {response.status_code}")
                        break
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Specific selectors for Gamermarkt (List Layout)
                    listing_items = soup.select('div.col-12.bg-white.color-inherit.shadow-sm.rounded-3')
                    
                    if not listing_items:
                        # Fallback for potential grid layouts
                        listing_items = soup.select('.product-item-wrapper, .col-lg-3.col-md-4.col-6.mb-4')

                    if not listing_items:
                        print("No items found on this page. Stopping category.")
                        break

                    page_listing_ids = []
                    
                    for item in listing_items:
                        try:
                            # Link
                            link_el = item.select_one('a')
                            link = link_el['href'] if link_el else "#"
                            if link and not link.startswith('http'):
                                link = "https://www.gamermarkt.com" + link

                            # Price
                            price_el = item.select_one('.fw-600')
                            price = price_el.get_text(strip=True) if price_el else "N/A"

                            # Title
                            badges = item.select('.badge.bg-light')
                            if badges:
                                title_parts = [b.get_text(strip=True) for b in badges]
                                title = " - ".join(title_parts)
                            else:
                                title_el = item.select_one('.product-title, h5, h4, .card-title')
                                title = title_el.get_text(strip=True) if title_el else link.split('/')[-1].replace('-', ' ').title()

                            # Image
                            img_el = item.select_one('img')
                            image = ""
                            if img_el:
                                image = img_el.get('data-src') or img_el.get('src') or ""
                                if image and not image.startswith('http'):
                                    image = "https://cdns.gamermarkt.com" + image
                            
                            # ID
                            listing_id = link.split('-')[-1] if link else str(random.randint(10000, 99999))
                            
                            # Category
                            category = "Unknown"
                            if "valorant" in base_url: category = "Valorant"
                            elif "lol" in base_url: category = "LoL"
                            elif "cs2-item" in base_url: category = "CS2 Item"
                            elif "cs2" in base_url: category = "CS2"
                            elif "fortnite" in base_url: category = "Fortnite"
                            
                            listing_obj = {
                                "id": listing_id,
                                "title": title,
                                "price": price,
                                "category": category,
                                "url": link,
                                "image": image,
                                "timestamp": time.time()
                            }
                            
                            listings_map[listing_id] = listing_obj
                            page_listing_ids.append(listing_id)
                            
                        except Exception as e:
                            print(f"Error parsing item: {e}")

                    # Loop Detection
                    if page == 1:
                        first_page_ids = set(page_listing_ids)
                    else:
                        # If any ID from this page was also on the first page, we looped
                        # If more than 50% of items from this page are also on the first page, we likely looped
                        current_ids_set = set(page_listing_ids)
                        overlap = current_ids_set.intersection(first_page_ids)
                        if len(page_listing_ids) > 0 and (len(overlap) / len(page_listing_ids)) > 0.5:
                            print(f"Detected loop (>{int((len(overlap) / len(page_listing_ids))*100)}% items from page 1 reappeared). Stopping category.")
                            break
                    
                    # Save immediately to show progress
                    save_listings(list(listings_map.values()))
                    
                    # Check for Next Page Button
                    # User said: <span class="page-link" id="next-page">Sonraki Sayfa</span>
                    # We look for text "Sonraki Sayfa"
                    next_btn = soup.find(lambda tag: tag.name in ['span', 'a', 'li'] and 'Sonraki Sayfa' in tag.get_text())
                    
                    if not next_btn:
                        print("No 'Sonraki Sayfa' button found. Stopping category.")
                        break
                        
                    # Also check if the button is disabled (common in pagination)
                    if 'disabled' in next_btn.get('class', []):
                         print("Next page button is disabled. Stopping category.")
                         break

                    # Prepare for next page
                    page += 1
                    time.sleep(random.uniform(3, 6)) # Anti-spam delay
                    
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    break
            
            # Small break between categories
            time.sleep(5)
        
        # Wait before restarting the full cycle of all categories
        print("Full cycle complete. Waiting...")
        time.sleep(60)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/listings')
def get_listings():
    return jsonify(load_listings())

@app.route('/api/stop', methods=['POST'])
def stop_system():
    global SCRAPING_ACTIVE
    SCRAPING_ACTIVE = False
    return jsonify({"status": "stopping"})

@app.route('/api/start', methods=['POST'])
def start_system():
    global SCRAPING_ACTIVE, SCRAPER_THREAD
    if not SCRAPING_ACTIVE:
        SCRAPING_ACTIVE = True
        SCRAPER_THREAD = threading.Thread(target=scrape_worker)
        SCRAPER_THREAD.daemon = True
        SCRAPER_THREAD.start()
        return jsonify({"status": "started"})
    return jsonify({"status": "already_running"})

@app.route('/api/status')
def get_status():
    return jsonify({"active": SCRAPING_ACTIVE})

if __name__ == '__main__':
    # Start scraper automatically on launch
    SCRAPING_ACTIVE = True
    SCRAPER_THREAD = threading.Thread(target=scrape_worker)
    SCRAPER_THREAD.daemon = True
    SCRAPER_THREAD.start()
    
    app.run(debug=True, use_reloader=False)
