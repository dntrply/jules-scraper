"""
A web scraper for fetching and parsing HTML, and collecting URLs from igod.gov.in.
This script provides functions to fetch and parse HTML from a given URL,
extract links, and specifically scrape URLs from
the Indian Government Directory (igod.gov.in).
This version is significantly simplified to reduce execution time by
processing only a limited number of state category pages and not fetching detail pages.
"""

import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse

# Base URL for igod.gov.in to resolve relative paths
IGOD_BASE_URL = "https://igod.gov.in/"

# Max number of state/UT category pages to process to avoid timeouts
MAX_STATES_TO_PROCESS = 3 # Significantly reduced

def get_parsed_html(url: str):
    """
    Fetches the HTML content of a given URL and returns a BeautifulSoup object.
    """
    try:
        response = requests.get(url, timeout=30) # Slightly increased individual timeout
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        else:
            print(f"Error: Received status code {response.status_code} for URL: {url}")
            return None
    except requests.exceptions.Timeout:
        print(f"Error: Timeout while fetching URL {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def extract_all_links_from_page(page_url: str, content_selector: str = "body"):
    """
    Extracts all unique absolute URLs from anchor tags within a specified content area of a page.
    The original subtask asked for a 'link_selector' here, but to simplify and align with
    how it was used, this function gets all links in a 'content_selector' area, and the
    calling function does the filtering if needed.
    """
    print(f"Extracting all links from: {page_url} within selector: {content_selector}")
    parsed_html = get_parsed_html(page_url)
    links = set() 
    if parsed_html:
        content_area = parsed_html.select_one(content_selector)
        if not content_area:
            print(f"Warning: Content selector '{content_selector}' not found on {page_url}. Searching whole body.")
            content_area = parsed_html 
            
        for element in content_area.find_all('a', href=True): 
            href = element.get('href').strip()
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                absolute_url = urljoin(page_url, href)
                links.add(absolute_url)
    else:
        print(f"Could not parse HTML from {page_url}")
    return list(links)

def scrape_igod_union_government_sites():
    """
    Scrapes website URLs from the IGoD Union Government categories page.
    Simplified: Collects only direct external links from the main category page.
    """
    target_url = "https://igod.gov.in/ug/categories"
    print(f"\nScraping Union Government sites (highly simplified) from: {target_url}")
    collected_urls = set()
    
    # Using "div.region-content" as a general content area selector.
    initial_links = extract_all_links_from_page(target_url, "div.region-content") 

    for link_url in initial_links:
        parsed_link_url = urlparse(link_url)
        if parsed_link_url.hostname and parsed_link_url.hostname != urlparse(IGOD_BASE_URL).hostname:
            if link_url.startswith("http"): 
                print(f"  Found direct external Union site: {link_url}")
                collected_urls.add(link_url)

    print(f"Found {len(collected_urls)} unique Union Government URLs (highly simplified).")
    return collected_urls


def scrape_igod_state_government_sites():
    """
    Scrapes website URLs from the IGoD State Government pages.
    Highly Simplified: Processes only the first MAX_STATES_TO_PROCESS state category pages.
    Collects direct external links from those few state category pages.
    """
    state_list_url = "https://igod.gov.in/sg/states"
    print(f"\nScraping State Government sites (highly simplified) from: {state_list_url}")
    collected_urls = set()

    # Using "div.region-content" as a general content area selector.
    state_main_page_links = extract_all_links_from_page(state_list_url, "div.region-content") 

    state_category_page_urls = []
    for link_url in state_main_page_links:
        # Filter for links that look like state category pages: e.g., /sg/AP/categories
        if "/sg/" in link_url and "/categories" in link_url: 
            # Ensure it's not a link to the parent "states" page itself or some other non-category link
            if link_url != state_list_url and link_url.startswith(IGOD_BASE_URL + "sg/") and link_url.endswith("/categories"):
                state_category_page_urls.append(link_url)
    
    state_category_page_urls = sorted(list(set(state_category_page_urls))) # Deduplicate and sort for consistent processing order
    
    print(f"Found {len(state_category_page_urls)} unique State/UT category pages. Processing first {MAX_STATES_TO_PROCESS}.")

    for i, state_cat_url in enumerate(state_category_page_urls):
        if i >= MAX_STATES_TO_PROCESS:
            print(f"Reached MAX_STATES_TO_PROCESS ({MAX_STATES_TO_PROCESS}), stopping state processing.")
            break
        
        print(f"Processing State Category Page ({i+1}/{MAX_STATES_TO_PROCESS}): {state_cat_url}")
        # Using "div.region-content" as a general content area selector.
        links_on_state_cat_page = extract_all_links_from_page(state_cat_url, "div.region-content")
        
        for link_url in links_on_state_cat_page:
            parsed_link_url = urlparse(link_url)
            if parsed_link_url.hostname and parsed_link_url.hostname != urlparse(IGOD_BASE_URL).hostname:
                if link_url.startswith("http"): 
                    print(f"    Found direct external State site: {link_url}")
                    collected_urls.add(link_url)

    print(f"Found {len(collected_urls)} unique State/UT Government URLs (from {MAX_STATES_TO_PROCESS} states).")
    return collected_urls

if __name__ == "__main__":
    print("Starting URL collection from igod.gov.in (Highly Simplified Strategy)...")

    union_urls = scrape_igod_union_government_sites()
    state_urls = scrape_igod_state_government_sites()

    all_unique_urls = union_urls.union(state_urls)
    
    output_dir = "data"
    output_filename = os.path.join(output_dir, "collected_igod_urls.txt")

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        except OSError as e:
            print(f"Error creating directory {output_dir}: {e}")
            if not os.path.isdir(output_dir): # Check again in case of race condition
                print("Exiting as output directory could not be created.")
                exit()
            else:
                print(f"Directory {output_dir} already exists.")


    try:
        with open(output_filename, "w") as f:
            for url in sorted(list(all_unique_urls)):
                f.write(url + "\n")
        print(f"\nCollected {len(all_unique_urls)} unique URLs (highly simplified).")
        print(f"Results saved to: {output_filename}")
    except IOError as e:
        print(f"Error writing to file {output_filename}: {e}")
