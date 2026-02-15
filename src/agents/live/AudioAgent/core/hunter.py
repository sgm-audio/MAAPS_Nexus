import random
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from config import Config
from core.bloodhound import Bloodhound

class Hunter:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.leads = []

    def hunt(self, cities=None):
        cities = cities or Config.TARGET_CITIES
        print(f"\n📡 HUNTER PROTOCOL ACTIVATED")
        print(f"🎯 Targets: {cities}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            for city in cities:
                self._scan_city(page, city)
                
            browser.close()
        
        return self.leads

    def _scan_city(self, page, city):
        query = f"{Config.SEARCH_QUERY} in {city}"
        print(f"\n📍 Scanning: {city}...")
        
        try:
            page.goto(f"https://www.google.com/maps/search/{query.replace(' ', '+')}", timeout=60000)
            page.wait_for_timeout(3000)
            
            # Scroll Feed
            try:
                page.locator('div[role="feed"]').wait_for(timeout=5000)
                feed = page.locator('div[role="feed"]')
                for _ in range(4): # Deeper scroll
                    feed.evaluate("node => node.scrollTop += 2000")
                    page.wait_for_timeout(1000)
            except:
                pass

            listings = page.locator('div[class*="Nv2PK"]').all()
            print(f"   ↳ Found {len(listings)} raw signals.")
            
            for listing in listings[:15]: # Cap at 15
                self._process_listing(page, listing, city)
                
        except Exception as e:
            print(f"   ⚠️ Scan Error: {e}")

    def _process_listing(self, page, listing, city):
        text_lines = listing.inner_text().split('\n')
        company = text_lines[0]
        
        # Check Dedupe (Simple in-memory check)
        if any(l['Company'] == company for l in self.leads): return

        # Extract Website
        website = ""
        try:
            links = listing.locator('a').all()
            for link in links:
                href = link.get_attribute('href')
                if href and href.startswith('http') and 'google' not in href:
                    website = href
                    break
        except: pass

        # BLOODHOUND ENGAGE
        email = ""
        hook = "general audio workflow"
        
        if website:
            print(f"      🔎 Inspecting: {company}...")
            try:
                # Spawn isolated page
                site_page = page.context.new_page()
                site_page.goto(website, timeout=10000)
                
                # Scan Homepage
                content = site_page.content()
                emails = Bloodhound.extract_emails(content)
                
                # Deep Scan if empty
                if not emails:
                    soup = BeautifulSoup(content, 'html.parser')
                    contact_url = Bloodhound.find_contact_link(soup, website)
                    if contact_url:
                        print(f"         🐕 Bloodhound: Tracking {contact_url}...")
                        try:
                            site_page.goto(contact_url, timeout=8000)
                            emails.update(Bloodhound.extract_emails(site_page.content()))
                        except: pass
                
                site_page.close()
                
                if emails:
                    email = Bloodhound.rank_emails(emails)
                    print(f"         🩸 EMAIL CAPTURED: {email}")
                else:
                    print(f"         ❌ No email found.")
                    
            except Exception as e:
                print(f"         ⚠️ Visit Error: {e}")

        # Add to list
        self.leads.append({
            'Company': company,
            'City': city,
            'Website': website,
            'Email': email,
            'Hook': hook 
        })
