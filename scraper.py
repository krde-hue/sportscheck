import json
import os
import re
from datetime import datetime
import pytz
from playwright.sync_api import sync_playwright

# Target Websites
SITES = {
    "KT": "https://www.7abet.com/en-UN/sportsbook",
    "Sultan": "https://sultanbet.com/betting",
    "SS-BR": "https://www.qbet.com/en-UN/sportsbook",
    "SS-BC": "https://www.55bet.com/en-UN/sportsbook"
}

SPORTS_TO_TRACK = ["Football", "Soccer", "Basketball", "Tennis", "Ice Hockey", "Table Tennis"]

def get_manila_time():
    manila_tz = pytz.timezone('Asia/Manila')
    now = datetime.now(manila_tz)
    date_str = now.strftime('%d/%m/%Y')
    
    hour = now.hour
    if hour < 13:
        time_slot = "Early 10AM"
    elif hour < 18:
        time_slot = "Mid 4PM"
    else:
        time_slot = "Late 9PM"
        
    return date_str, time_slot

def scrape_counts():
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        for name, url in SITES.items():
            print(f"Scraping {name} at {url}...")
            try:
                page = context.new_page()
                page.goto(url, timeout=60000)
                page.wait_for_load_state("networkidle", timeout=15000)
                
                page_text = page.inner_text("body")
                site_data = {}
                
                for sport in SPORTS_TO_TRACK:
                    pattern = rf"{sport}\s*\n*\s*\(?(\d+)\)?"
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    
                    sport_key = "Football" if sport.lower() == "soccer" else sport
                    
                    if match:
                        site_data[sport_key] = int(match.group(1))
                    elif sport_key not in site_data:
                        site_data[sport_key] = ""
                        
                results[name] = site_data
                page.close()
            except Exception as e:
                print(f"Failed to scrape {name}: {e}")
                results[name] = {"Football": "", "Basketball": "", "Tennis": "", "Ice Hockey": "", "Table Tennis": ""}
                
        browser.close()
    return results

def update_json(new_data, date_str, time_slot):
    file_path = 'data.json'
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    else:
        data = {}
        
    if date_str not in data:
        data[date_str] = {}
    
    data[date_str][time_slot] = new_data
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Successfully updated data.json for {date_str} - {time_slot}")

if __name__ == "__main__":
    date_str, time_slot = get_manila_time()
    print(f"Running scraper for {date_str} - {time_slot}")
    scraped_data = scrape_counts()
    update_json(scraped_data, date_str, time_slot)
