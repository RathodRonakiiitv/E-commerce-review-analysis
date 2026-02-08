
import requests
from bs4 import BeautifulSoup
import random

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

session = requests.Session()
session.headers.update(headers)

product_url = "https://www.flipkart.com/devsignature-sheesham-wood-dining-table-set-wooden-4-seater-set-home-solid/p/itme4fad1c7e12cc"
review_url = "https://www.flipkart.com/devsignature-sheesham-wood-dining-table-set-wooden-4-seater-set-home-solid/product-reviews/itme4fad1c7e12cc?marketplace=FLIPKART&page=1"

print(f"Visiting Product Page: {product_url}...")
try:
    p_response = session.get(product_url, timeout=20)
    print(f"Product Page Status: {p_response.status_code}")
    
    print(f"Fetching Review Page: {review_url}...")
    response = session.get(review_url, timeout=20)
    print(f"Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check Title
    title = soup.find('title')
    print(f"Title: {title.get_text(strip=True) if title else 'No Title'}")
    
    # Check Certified Buyer strings
    cbs = soup.find_all(string=lambda t: t and "Certified Buyer" in t)
    print(f"Found {len(cbs)} 'Certified Buyer' strings")
    
    if cbs:
        print("\n--- Analysing First Match ---")
        cb = cbs[0]
        print(f"Text: {cb}")
        parent = cb.parent
        print(f"Parent Tag: {parent.name}")
        print(f"Parent Class: {parent.get('class')}")
        
        # Traverse up and print simplified structure
        p = parent
        for i in range(5):
            p = p.parent
            if not p: break
            print(f"Level {i+1} Up: {p.name} (Class: {p.get('class')})")
            # print(f"  Text preview: {list(p.stripped_strings)[:5]}")

    # Try existing extraction logic
    print("\n--- Testing Extraction Logic ---")
    review_containers = []
    for cb in cbs:
        p = cb.parent
        for _ in range(15):
            if p is None: break
            p = p.parent
            if p and p.name == 'div':
                inner_cbs = len(p.find_all(string=lambda t: t and "Certified Buyer" in t))
                # Relaxed check: Just see if we can find relevant text
                strings = list(p.stripped_strings)
                if any("READ MORE" in s for s in strings) and len(strings) >= 5:
                     # Just checking if this simplified logic works
                     if p not in review_containers:
                        review_containers.append(p)
                     break
    
    print(f"Found {len(review_containers)} potential containers with relaxed logic")
    
    if review_containers:
        print("First container strings:", list(review_containers[0].stripped_strings))

except Exception as e:
    print(f"Error: {e}")
