import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import json # Added for JSON output
import os # Added for os.makedirs

# --- Configuration ---
# USER_AGENT = "GovEventScraper/0.1" # Old user agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
FREE_KEYWORDS = [r'\bfree\b', r'no fee', r'no cost', r'without any fee', r'complimentary'] # Use regex for \bfree\b

# --- Helper Functions ---

def fetch_html(url: str) -> str | None:
    """
    Fetches HTML content from a URL.
    Returns HTML text or None if an error occurs.
    """
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1' # Do Not Track
    }
    print(f"Fetching HTML from: {url} with enhanced headers.")
    try:
        response = requests.get(url, headers=headers, timeout=10) # Timeout set to 10s
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None

def is_event_free(text_content: str) -> bool:
    """
    Checks if the text content suggests the event is free using keywords.
    """
    if not text_content:
        return False
    text_lower = text_content.lower()
    for keyword_pattern in FREE_KEYWORDS:
        if re.search(keyword_pattern, text_lower):
            return True
    return False

# --- Site-Specific Parsing Functions (Placeholders) ---

def parse_india_gov_events(html_content: str, base_url: str) -> list[dict]:
    print(f"Parsing india.gov.in/mygov/events from {base_url}...")
    events = []
    soup = BeautifulSoup(html_content, 'html.parser')

    # Based on view_text_website output, links are to mygov.in/node/...
    # Titles are the text of these links.
    # The structure is not super clear from text, but typically these are in a list or divs.
    # Let's try finding all links and filtering them.
    # Common Drupal content area: div.region-content, article, main content sections
    # Try to find a container for the event listings. If page is simple, direct find_all('a') might work.
    # A common pattern on india.gov.in seems to be divs with class 'content-main-right' or 'middle-content'.
    # Let's assume a general content selector first, e.g., a div with class 'item-list' or 'view-content'
    # For now, let's try a broad approach: find all links and filter by URL.

    # The links in the provided text output (Turn 45) are often of the form:
    # "Video Making Contest on Introduction of New Offences in NCL [74]Video Making Contest on Introduction of New Offences in NCL"
    # Link 74: https://www.mygov.in/node/359457/
    # This implies the link text is the title.
    # The actual HTML might have list items or divs for each event.
    # Example from similar pages: items might be in <div class="views-row"> or <li>

    # Attempting a general selector for list items or content blocks
    # This will need refinement based on actual HTML structure if available.
    # If the text output is directly parsed, it's harder.
    # The subtask implies parsing HTML content fetched by requests.
    
    # Let's assume events are list items or contained in divs.
    # A common pattern is <div class="field-content"> containing an <a> tag.
    # Or, directly, find all <a> tags that link to mygov.in/node/
    
    for link_tag in soup.find_all('a', href=True):
        href = link_tag.get('href')
        if href and 'mygov.in/node/' in href:
            title = link_tag.get_text(strip=True)
            if not title: # Skip if link has no text (e.g. image link without alt text)
                continue

            absolute_url = urljoin(base_url, href) # base_url is india.gov.in
            
            # Date extraction from title (simple regex for "on DDth Month YYYY" or similar)
            date_str = "N/A"
            # Regex for dates like "on 25th May 2025" or "25 May 2025" or "May 25, 2025"
            date_match = re.search(r'(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})', title, re.IGNORECASE)
            if not date_match: # Try "Month DD, YYYY"
                date_match = re.search(r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', title, re.IGNORECASE)
            if not date_match: # Try "DD-MM-YYYY" or "DD/MM/YYYY" - less likely in titles but possible
                 date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', title)

            if date_match:
                date_str = date_match.group(1)
            
            # Check for free status (simple keyword check on title)
            free_indicator = is_event_free(title)

            events.append({
                "event_title": title,
                "event_date_str": date_str,
                "source_url": absolute_url,
                "is_free_indicator_present": free_indicator,
                "site_scraped_from": base_url 
            })
    
    if not events:
        print(f"  No events found on {base_url} with 'mygov.in/node/' links. Structure might differ.")
        # Fallback or alternative selectors could be added here if the primary one fails.
        # For example, if the text output was very flat, one might iterate over all text and use regex to find titles near links.
        # However, sticking to BeautifulSoup parsing of <a> tags as per general instructions.
        
    return events

def parse_india_gov_press_releases(html_content: str, base_url: str) -> list[dict]:
    # Note: base_url is https://pib.gov.in as per target list update
    print(f"Parsing PIB press releases from {base_url} (intended for india.gov.in/press-releases)...")
    events = []
    soup = BeautifulSoup(html_content, 'html.parser')

    # Based on Turn 49 output for pib.gov.in/indexd.aspx
    # Look for a section with heading "Latest Press Releases"
    # Then find links within that section that point to PressReleseDetail.aspx
    
    # First, try to find a specific section/div that contains "Latest Press Releases"
    # This is a common pattern. The heading might be h1, h2, h3, etc.
    latest_releases_heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'div', 'span'] and "Latest Press Releases" in tag.get_text())
    
    search_area = soup # Default to searching the whole soup
    if latest_releases_heading:
        print(f"  Found 'Latest Press Releases' heading: {latest_releases_heading.name}")
        # Try to find a sensible parent or container for the links to narrow the search.
        # This could be the parent of the heading, or a sibling div/ul.
        possible_container = latest_releases_heading.find_parent('div') # Common case: heading is inside a div
        if possible_container:
            # Check if this container has the links, or if a sibling list/div has them
            # This part is heuristic. A common pattern is heading, then a list/div of items.
            ul_sibling = latest_releases_heading.find_next_sibling('ul')
            if ul_sibling:
                search_area = ul_sibling
                print("  Searching in <ul> sibling of heading.")
            elif possible_container.find('ul'): # Check if parent has a ul
                 search_area = possible_container
                 print("  Searching in parent container of heading that has a <ul>.")
            else: # Fallback to the parent if no direct list found
                search_area = possible_container
                print("  Searching in parent container of heading.")
        else:
            print("  Could not identify a specific container for 'Latest Press Releases', searching broadly after heading if possible.")
            # If no parent div, try searching all elements after the heading
            # This is less reliable. For now, if no parent, stick to broader soup search but log it.
            # search_area = soup # Already default
    else:
        print(f"  'Latest Press Releases' section/heading not found on {base_url}. Searching all links.")

    processed_urls = set()
    for link_tag in search_area.find_all('a', href=True):
        href = link_tag.get('href')
        # PIB links use "PressReleseDetail.aspx" (with "Relese")
        if href and 'PressReleseDetail.aspx?PRID=' in href:
            if href in processed_urls: # Avoid processing the same link multiple times
                continue
            
            title = link_tag.get_text(strip=True)
            if not title or title.lower() == "more +": 
                continue

            absolute_url = urljoin(base_url, href) 
            processed_urls.add(href)
            
            # Date is not directly available in this list view on pib.gov.in/indexd.aspx for each item.
            # It is available on the detail page. For v1, we'll mark as N/A.
            date_str = "N/A" 
            
            free_indicator = is_event_free(title)

            events.append({
                "event_title": title,
                "event_date_str": date_str,
                "source_url": absolute_url,
                "is_free_indicator_present": free_indicator,
                "site_scraped_from": base_url 
            })
            
    if not events:
         print(f"  No press release links matching pattern found in search area of {base_url}.")
        
    return events

def parse_asr_district_events(html_content: str, base_url: str) -> list[dict]:
    print(f"Parsing asr.ap.gov.in/events-2/ from {base_url}...")
    events = []
    soup = BeautifulSoup(html_content, 'html.parser')

    # Based on view_text_website output (Turn 52), the /events-2/ page
    # itself does not seem to list individual events. It's a generic page titled "EVENTS".
    # Events might be loaded dynamically or listed elsewhere (e.g., message board or specific news sections).
    # For this version, if no static event items are found, it will return an empty list.
    
    # Example selector if events were listed (hypothetical):
    # for item in soup.select('div.event-item-class'):
    #     title_tag = item.select_one('h3.event-title-class a')
    #     date_tag = item.select_one('span.event-date-class')
    #     if title_tag and title_tag.get('href'):
    #         title = title_tag.get_text(strip=True)
    #         url = urljoin(base_url, title_tag.get('href'))
    #         date_str = date_tag.get_text(strip=True) if date_tag else "N/A"
    #         free_indicator = is_event_free(title + " " + (item.get_text(strip=True)))
    #         events.append({
    #             "event_title": title,
    #             "event_date_str": date_str,
    #             "source_url": url,
    #             "is_free_indicator_present": free_indicator,
    #             "site_scraped_from": base_url
    #         })
            
    if not events:
        print(f"  No direct static event listings found on {base_url}/events-2/. Page might be dynamic or events are in other sections.")
        
    return events

def parse_asr_district_message_board(html_content: str, base_url: str) -> list[dict]:
    print(f"Parsing asr.ap.gov.in message board from {base_url}...")
    events = []
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the "Message Board" heading. Based on Turn 54, it's a heading tag.
    # Let's try to find a heading (h1-h4) that contains "Message Board"
    message_board_heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4'] and "Message Board" in tag.get_text())

    if message_board_heading:
        # Assume the links are in a list (ul) or series of divs that are siblings or children of a common parent.
        # Try to find a common container for the message board items.
        # Often, this is the next sibling <ul> or a <div> wrapper.
        # Let's try finding a `div` or `ul` that is an immediate sibling or parent of the heading,
        # or just search for relevant links within a reasonable scope after the heading.

        # A common structure is that the heading is followed by a <ul> or items are within a specific div.
        # From the text output (Turn 54), it appears as a list of links:
        # Message Board
        #      * [77]Status of the Candiates applied for posts in ICPS, SAA, OSC & Children Home Chinthapalli
        #      * [78]Recruitment Notification For State GST
        # Link 77: https://allurisitharamaraju.ap.gov.in/document/status-of-the-candiates.../
        # This implies items are <li><a>...</a></li> or similar.

        # Let's find the parent of the heading and search within it, or search siblings.
        # For simplicity, and assuming the message board is a distinct section,
        # we can look for list items (li) with links inside, after the heading.
        # This requires careful traversal or a known wrapper div.

        # A more direct approach if the structure is flat:
        # Find all <a> tags after the message_board_heading.
        # This is fragile if other links appear before the next section.

        # Alternative: Look for a known class if the message board items are wrapped.
        # e.g., <div class="message-board-items"><ul><li>...</li></ul></div>
        # Without clear class names from view_text_website, this is a guess.
        # The output shows links like [77] pointing to /document/ paths.

        # Let's try to find a <ul> that follows the heading or is a sibling.
        # If the heading is within a section div, find all 'a' tags in that div.
        
        # Heuristic: find all 'a' tags after the heading, and filter them if they seem to be part of the message board.
        # This district website often uses /document/ paths for these kinds of links.
        
        # Try to find a list (ul) that is a sibling of the heading or a child of its parent
        list_container = None
        if message_board_heading.find_next_sibling('ul'):
            list_container = message_board_heading.find_next_sibling('ul')
        elif message_board_heading.parent and message_board_heading.parent.find('ul'): # check parent
            list_container = message_board_heading.parent.find('ul')
        
        if list_container:
            message_items = list_container.find_all('li')
            for item in message_items:
                link_tag = item.find('a', href=True)
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    href = link_tag.get('href')
                    
                    if not title or not href:
                        continue

                    absolute_url = urljoin(base_url, href)
                    date_str = "N/A" # Dates not apparent in the list view for message board
                    free_indicator = is_event_free(title) # Check title for free keywords

                    events.append({
                        "event_title": title,
                        "event_date_str": date_str,
                        "source_url": absolute_url,
                        "is_free_indicator_present": free_indicator,
                        "site_scraped_from": base_url
                    })
        else:
            # Fallback if <ul> not found: search all links after heading that point to /document/
            print("  Message board <ul> not found, trying fallback for /document/ links after heading.")
            for sibling in message_board_heading.find_next_siblings():
                for link_tag in sibling.find_all('a', href=True):
                    href = link_tag.get('href')
                    if href and '/document/' in href:
                        title = link_tag.get_text(strip=True)
                        if not title: continue
                        
                        absolute_url = urljoin(base_url, href)
                        date_str = "N/A"
                        free_indicator = is_event_free(title)
                        events.append({
                            "event_title": title,
                            "event_date_str": date_str,
                            "source_url": absolute_url,
                            "is_free_indicator_present": free_indicator,
                            "site_scraped_from": base_url
                        })
                # Break after a few siblings to avoid scanning whole page if structure is unexpected
                if len(events) > 0 and sibling.name not in ['ul', 'div', 'p']: # Heuristic stop
                    break


    if not events:
        print(f"  No 'Message Board' items found or parsed on {base_url}.")
        
    return events

def parse_education_gov_updates(html_content: str, base_url: str) -> list[dict]:
    print(f"Parsing education.gov.in/updates from {base_url}...")
    events = []
    soup = BeautifulSoup(html_content, 'html.parser')

    # Based on Turn 56 output:
    # Updates are listed, often as links to PDFs.
    # Example item text: "* [63]Shri Dharmendra Pradhan presides over LoI handover ceremony to University of Liverpool   (Monday,26-May-2025 ) - (158.54 KB)"
    # Link 63: https://www.education.gov.in/sites/upload_files/mhrd/files/PIB2131284.pdf
    # This suggests list items (<li>) containing an <a> tag and then plain text for date.

    # Common Drupal selectors for lists: div.view-content ul, div.item-list ul, etc.
    # Let's look for <li> elements as they seem to represent individual items.
    # If the structure is flat, we might need to find <a> tags and then look for date text nearby.

    # Try finding list items within a main content area to avoid navigation links.
    # Common main content selectors: #main-content, div.content, article, etc.
    # Based on typical Drupal structure, view-content is often used for lists.
    # Let's try to find a div with class "view-content" or "item-list" or just "content"
    # If not found, fall back to all 'li's but this might be noisy.
    
    content_area = soup.find('div', class_='view-content') # Common Drupal view container
    if not content_area:
        content_area = soup.find('div', class_='item-list') # Another common one
    if not content_area:
        content_area = soup.find('main') # HTML5 main tag
    if not content_area:
        print(f"  No specific content area (view-content, item-list, main) found on {base_url}. Searching all <li> tags.")
        list_items = soup.find_all('li')
    else:
        print(f"  Searching for <li> items within identified content area on {base_url}.")
        list_items = content_area.find_all('li')

    if not list_items:
        print(f"  No <li> items found in targeted content area on {base_url}.")

    for item in list_items:
        link_tag = item.find('a', href=True)
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        href = link_tag.get('href')
        
        if not title or not href:
            continue

        absolute_url = urljoin(base_url, href)
        
        # Date extraction: Date string seems to be in the text of the list item, after the link.
        # Format: (Day,DD-Month-YYYY )
        date_str = "N/A"
        item_text = item.get_text(strip=False) # Get text with spaces to help split
        
        # Try to find date pattern like (Day, DD-Month-YYYY)
        # Example: (Monday,26-May-2025 )
        date_match = re.search(r'\((?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,\s*\d{1,2}-[A-Za-z]{3,}-\d{4}\s*\)', item_text)
        if date_match:
            date_str = date_match.group(0).strip()
            # Clean up: remove surrounding parentheses and extra spaces
            date_str = date_str.strip('() ')
        
        # If not found, try a simpler DD-Month-YYYY or Month-DD-YYYY within the item text
        if date_str == "N/A":
            # Regex for DD-Month-YYYY or Month DD, YYYY (allow variations)
            # This is a general fallback if the specific format above isn't found.
            simple_date_match = re.search(r'(\d{1,2}\s+[A-Za-z]+,\s+\d{4}|\d{1,2}-\w+-\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})', item_text)
            if simple_date_match:
                 date_str = simple_date_match.group(1).strip()


        free_indicator = is_event_free(title + " " + item_text)

        events.append({
            "event_title": title,
            "event_date_str": date_str,
            "source_url": absolute_url,
            "is_free_indicator_present": free_indicator,
            "site_scraped_from": base_url
        })

    if not events:
        print(f"  No events extracted from {base_url}. Parsers might need adjustment based on actual HTML structure.")
        
    return events

def parse_education_gov_press_releases(html_content: str, base_url: str) -> list[dict]:
    print(f"Parsing education.gov.in/press-releases from {base_url}...")
    events = []
    soup = BeautifulSoup(html_content, 'html.parser')

    # Structure is very similar to /updates page based on Turn 58 output.
    # Example item text: "* [63]Shri Dharmendra Pradhan presides over LoI handover ceremony to University of Liverpool   (Monday,26-May-2025 ) - (158.54 KB)"
    # Link 63: https://www.education.gov.in/sites/upload_files/mhrd/files/PIB2131284.pdf
    
    content_area = soup.find('div', class_='view-content')
    if not content_area:
        content_area = soup.find('div', class_='item-list')
    if not content_area:
        content_area = soup.find('main')
    if not content_area:
        print(f"  No specific content area (view-content, item-list, main) found on {base_url} for press releases. Searching all <li> tags.")
        list_items = soup.find_all('li')
    else:
        print(f"  Searching for <li> items within identified content area on {base_url} for press releases.")
        list_items = content_area.find_all('li')
        
    if not list_items:
        print(f"  No <li> items found in targeted content area on {base_url} for press releases.")

    for item in list_items:
        link_tag = item.find('a', href=True)
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        href = link_tag.get('href')
        
        if not title or not href:
            continue

        absolute_url = urljoin(base_url, href)
        
        date_str = "N/A"
        item_text = item.get_text(strip=False) 
        
        date_match = re.search(r'\((?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,\s*\d{1,2}-[A-Za-z]{3,}-\d{4}\s*\)', item_text)
        if date_match:
            date_str = date_match.group(0).strip().strip('() ')
        
        if date_str == "N/A":
            simple_date_match = re.search(r'(\d{1,2}\s+[A-Za-z]+,\s+\d{4}|\d{1,2}-\w+-\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})', item_text)
            if simple_date_match:
                 date_str = simple_date_match.group(1).strip()

        # Press releases are generally informational, "free" indicator might not be relevant.
        free_indicator = is_event_free(title + " " + item_text) 

        events.append({
            "event_title": title,
            "event_date_str": date_str,
            "source_url": absolute_url,
            "is_free_indicator_present": free_indicator,
            "site_scraped_from": base_url
        })

    if not events:
        print(f"  No press releases extracted from {base_url}. Parsers might need adjustment.")
        
    return events

# --- Main Script Logic ---

def main():
    targets = [
        {
            "url": "https://www.india.gov.in/mygov/events",
            "parser": parse_india_gov_events,
            "base_for_links": "https://www.india.gov.in"
        },
        {
            "url": "https://pib.gov.in/indexd.aspx", # Changed from india.gov.in/press-releases
            "parser": parse_india_gov_press_releases,
            "base_for_links": "https://pib.gov.in" # Base URL for PIB
        },
        {
            "url": "https://allurisitharamaraju.ap.gov.in/events-2/",
            "parser": parse_asr_district_events,
            "base_for_links": "https://allurisitharamaraju.ap.gov.in"
        },
        {
            "url": "https://allurisitharamaraju.ap.gov.in/", # Main page for message board
            "parser": parse_asr_district_message_board,
            "base_for_links": "https://allurisitharamaraju.ap.gov.in"
        },
        {
            "url": "https://www.education.gov.in/updates",
            "parser": parse_education_gov_updates,
            "base_for_links": "https://www.education.gov.in"
        },
        {
            "url": "https://www.education.gov.in/press-releases",
            "parser": parse_education_gov_press_releases,
            "base_for_links": "https://www.education.gov.in"
        },
    ]

    all_events = []
    site_event_counts = {}

    for target in targets:
        url = target["url"]
        parser_func = target["parser"]
        base_for_links = target["base_for_links"] # Used for resolving relative URLs

        html = fetch_html(url)
        if html:
            parsed_events = parser_func(html, base_for_links)
            for event in parsed_events:
                # Ensure all required keys are present, add site_scraped_from
                event_data = {
                    "event_title": event.get("event_title", "N/A"),
                    "event_date_str": event.get("event_date_str", "N/A"),
                    "source_url": event.get("source_url", "N/A"),
                    "is_free_indicator_present": event.get("is_free_indicator_present", False),
                    "site_scraped_from": base_for_links # Use base_for_links as site identifier
                }
                all_events.append(event_data)
            
            # Store count per site for summary
            parsed_url_obj = urlparse(base_for_links)
            site_name = parsed_url_obj.netloc
            site_event_counts[site_name] = site_event_counts.get(site_name, 0) + len(parsed_events)


    print(f"\n--- Scraping Summary ---")
    print(f"Total potential events found: {len(all_events)}")
    for site, count in site_event_counts.items():
        print(f"  - Events from {site}: {count}")

    print("\n--- Extracted Event Details ---")
    if all_events:
        for i, event in enumerate(all_events):
            print(f"\nEvent {i+1}:")
            print(f"  Title: {event['event_title']}")
            print(f"  Date String: {event['event_date_str']}")
            print(f"  Source URL: {event['source_url']}")
            print(f"  Free Indicator: {event['is_free_indicator_present']}")
            print(f"  Scraped From: {event['site_scraped_from']}")
    else:
        print("No events extracted.")

    # Save to JSON file
    output_json_path = "data/extracted_events_v1.json"
    print(f"\nSaving extracted events to {output_json_path}...")
    try:
        os.makedirs("data", exist_ok=True) # Ensure data directory exists
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_events, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved {len(all_events)} events to {output_json_path}.")
    except IOError as e:
        print(f"  Error writing JSON to file {output_json_path}: {e}")
    except Exception as e:
        print(f"  An unexpected error occurred while saving JSON: {e}")


if __name__ == "__main__":
    main()
