import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import io 
# import pdfplumber # Not used in this version

# --- Imports for v3 (and current task) ---
import dateparser 

# --- Configuration ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
MAX_HTML_DETAILS_TO_PROCESS = 15 # Limit for HTML detail processing (from subtask 2.11)
FREE_KEYWORDS = [r'\bfree\b', r'no fee', r'no cost', r'without any fee', r'complimentary'] # For is_event_free

# --- Batch URLs for Subtask 2.14 ---
# This will be used in the main logic when processing this specific batch.
BATCH_URLS_FOR_REPROCESSING_HTML = [
    "https://pib.gov.in/PressReleseDetail.aspx?PRID=2131884",
    "https://allurisitharamaraju.ap.gov.in/document/dmho-asr-tenders-for-ambulances-from-mp-lads-funds/",
    "https://allurisitharamaraju.ap.gov.in/document/status-of-the-candiates-applied-for-posts-in-icps-saa-osc-children-home-chinthapalli/",
    "https://allurisitharamaraju.ap.gov.in/document/recruitment-notification-for-state-gst/",
    "https://allurisitharamaraju.ap.gov.in/document/dwsc-recruitment-notification/",
    "https://allurisitharamaraju.ap.gov.in/document/recruitment-for-the-post-of-medical-record-technician/",
    "https://allurisitharamaraju.ap.gov.in/document/notification-chs-april-2025-revised/",
    "https://allurisitharamaraju.ap.gov.in/document/notification-for-the-vacant-posts-in-children-home-chinthapalli/",
    "https://allurisitharamaraju.ap.gov.in/document/notification-icps-saa-april-2025/",
    "https://allurisitharamaraju.ap.gov.in/document/notification-osc-april-2025/"
]
BATCH_URLS_SET = set(BATCH_URLS_FOR_REPROCESSING_HTML)


# --- Helper Functions ---

def fetch_html(url: str) -> str | None:
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1'
    }
    print(f"Fetching HTML from: {url}") # General message for any HTML fetch
    try:
        response = requests.get(url, headers=headers, timeout=15) 
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {url}: {e}") # General error message
        return None

def load_events_from_json(filepath: str) -> list[dict]:
    print(f"Loading events from JSON file: {filepath}")
    if not os.path.exists(filepath):
        print(f"  Error: File not found: {filepath}")
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            events = json.load(f)
        print(f"  Successfully loaded {len(events)} events from {filepath}.")
        return events
    except json.JSONDecodeError as e:
        print(f"  Error decoding JSON from {filepath}: {e}")
        return []
    except IOError as e:
        print(f"  Error reading file {filepath}: {e}")
        return []

def save_events_to_json(events_list: list[dict], filepath: str):
    print(f"Saving {len(events_list)} events to JSON file: {filepath}")
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(events_list, f, indent=4, ensure_ascii=False)
        print(f"  Successfully saved events to {filepath}.")
    except IOError as e:
        print(f"  Error writing JSON to {filepath}: {e}")
    except Exception as e:
        print(f"  An unexpected error occurred while saving JSON: {e}")

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

def parse_date_to_iso(date_string: str) -> str | None:
    """
    Parses a date string using dateparser and returns it in "YYYY-MM-DD" ISO format.
    """
    if not date_string or not isinstance(date_string, str) or date_string.lower() == "n/a":
        return None
    try:
        date_obj = dateparser.parse(date_string, languages=['en'])
        if date_obj:
            return date_obj.strftime("%Y-%m-%d")
        return None
    except Exception:
        return None

# --- Site-Specific Detail Page Parsers (from Turn 115/Subtask 2.10) ---
def parse_pib_detail_page(html_content: str) -> str | None:
    # ... (Content from Turn 115, already robust) ...
    if not html_content: return None
    print("  Parsing PIB detail page...")
    soup = BeautifulSoup(html_content, 'html.parser')
    selectors_to_try = [
        {'name': 'div', 'attrs': {'class': 'actualbody'}}, {'name': 'div', 'attrs': {'id': 'release'}},
        {'name': 'td', 'attrs': {'class': 'ReleaseContent'}}, {'name': 'div', 'attrs': {'class': 'content-area'}},
        {'name': 'div', 'attrs': {'class': 'middle-content'}}, {'name': 'article'}, 
        {'name': 'div', 'attrs': {'role': 'main'}},
    ]
    content_area = None
    for sel_info in selectors_to_try:
        content_area = soup.find(sel_info['name'], sel_info.get('attrs', {}))
        if content_area: break
    if content_area:
        paragraphs = content_area.find_all('p', recursive=False)
        if not paragraphs: paragraphs = content_area.find_all('p')
        if paragraphs:
            valid_texts = [p.get_text(separator=' ', strip=True) for p in paragraphs if p.get_text(strip=True)]
            full_text = "\n\n".join(valid_texts)
        else:
            full_text = content_area.get_text(separator=' ', strip=True)
        read_in_marker = "Read this release in:"
        if read_in_marker in full_text: full_text = full_text.split(read_in_marker)[0]
        full_text = re.sub(r'\(Release ID:\s*\d+\)\s*$', '', full_text.strip()).strip()
        return full_text if full_text else None
    else: # Fallback
        all_paragraphs = soup.find_all('p')
        if all_paragraphs:
            valid_texts = [p.get_text(separator=' ', strip=True) for p in all_paragraphs if p.get_text(strip=True)]
            meaningful_paras = [text for text in valid_texts if len(text) > 50 and "skip to main content" not in text.lower()]
            if meaningful_paras:
                full_text = "\n\n".join(meaningful_paras)
                read_in_marker = "Read this release in:"
                if read_in_marker in full_text: full_text = full_text.split(read_in_marker)[0]
                full_text = re.sub(r'\((Release ID:\s*\d+\))\s*$', '', full_text.strip()).strip()
                if full_text: return full_text
        print("    Could not find any known main content selectors or meaningful paragraphs for PIB detail page.")
    return None


def parse_asr_district_document_page(html_content: str, base_url: str) -> dict:
    # ... (Content from Turn 115, already robust) ...
    default_result = {'detailed_text': None, 'primary_pdf_url_on_detail_page': None}
    if not html_content: return default_result
    print("  Parsing ASR district document page...")
    soup = BeautifulSoup(html_content, 'html.parser')
    main_text_content = None
    content_area = soup.find('div', class_='entry-content')
    if not content_area: content_area = soup.find('article')
    if not content_area: content_area = soup.find('div', id='content')
    if content_area:
        paragraphs = content_area.find_all('p')
        if paragraphs: main_text_content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else: main_text_content = content_area.get_text(strip=True)
    pdf_url = None
    if content_area: # Search for PDF links within the identified content area first
        for link_tag in content_area.find_all('a', href=True):
            href = link_tag.get('href')
            if href and href.lower().endswith('.pdf'):
                pdf_url = urljoin(base_url, href)
                break 
    if not pdf_url: # Fallback to searching whole document if not found in content area
        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href')
            if href and href.lower().endswith('.pdf'):
                pdf_url = urljoin(base_url, href)
                break
    return {'detailed_text': main_text_content.strip() if main_text_content else None, 
            'primary_pdf_url_on_detail_page': pdf_url}


# --- PDF Fetching (SKIPPED) ---
def fetch_and_extract_text_from_pdf(pdf_url: str) -> str | None:
    print(f"  DEBUG: PDF processing for {pdf_url} is SKIPPED.")
    return "PDF_PROCESSING_SKIPPED_DUE_TO_TIMEOUTS"

# --- Main Script Logic ---
def main():
    input_filepath = "data/extracted_events_v4_llm_classified.json" 
    output_filepath = "data/extracted_events_v4_llm_classified.json" # Overwriting

    events_data = load_events_from_json(input_filepath)
    if not events_data:
        print(f"No events loaded from {input_filepath}. Exiting.")
        return

    final_events = []
    batch_items_html_processed_count = 0
    # Counters for other refinements that will still run on all events
    dates_successfully_parsed_count = 0
    free_status_refined_count = 0
    pdfs_identified_as_candidates_count = 0 # Still count candidates

    print(f"\nStarting processing of {len(events_data)} events.")
    print(f"Will attempt HTML detail processing for {len(BATCH_URLS_SET)} specific batch URLs.")

    for event in events_data:
        copied_event = event.copy()
        source_url = copied_event.get("source_url")
        site_scraped_from = copied_event.get("site_scraped_from")

        # HTML Detail Page Processing for BATCH ITEMS ONLY
        if source_url in BATCH_URLS_SET:
            print(f"DEBUG: Processing HTML detail for batch item: {source_url}")
            # Reset fields that might be re-populated
            copied_event['detailed_text'] = None 
            if site_scraped_from == "https://allurisitharamaraju.ap.gov.in":
                 copied_event['primary_pdf_url_on_detail_page'] = None

            html = fetch_html(source_url)
            if html:
                if site_scraped_from == "https://pib.gov.in" and "PressReleseDetail.aspx" in source_url:
                    final_html_to_parse = html
                    soup_outer = BeautifulSoup(html, 'html.parser')
                    iframe_tag = soup_outer.find('iframe', src=lambda s: s and 'PressReleasePage.aspx' in s)
                    if iframe_tag:
                        iframe_src = iframe_tag.get('src')
                        if iframe_src:
                            absolute_iframe_url = urljoin(source_url, iframe_src)
                            print(f"  Found iframe with src: {iframe_src}. Fetching content from: {absolute_iframe_url}")
                            iframe_html = fetch_html(absolute_iframe_url)
                            if iframe_html: final_html_to_parse = iframe_html
                            else: print(f"  Failed to fetch iframe content for {absolute_iframe_url}. Parsing outer page.")
                    else: print("  No specific PIB content iframe found. Parsing current page.")
                    if final_html_to_parse:
                        copied_event['detailed_text'] = parse_pib_detail_page(final_html_to_parse)
                elif site_scraped_from == "https://allurisitharamaraju.ap.gov.in" and "/document/" in source_url:
                    parsed_data = parse_asr_district_document_page(html, site_scraped_from)
                    copied_event['detailed_text'] = parsed_data.get('detailed_text')
                    copied_event['primary_pdf_url_on_detail_page'] = parsed_data.get('primary_pdf_url_on_detail_page')
                
                if copied_event.get('detailed_text') or copied_event.get('primary_pdf_url_on_detail_page'):
                    batch_items_html_processed_count += 1
            else:
                print(f"  Failed to fetch HTML for batch item: {source_url}")
        
        # Date Parsing and Free Status Refinement (applied to all events)
        if 'event_date_iso' not in copied_event: copied_event['event_date_iso'] = None
        
        event_date_str = copied_event.get('event_date_str')
        parsed_iso_date = parse_date_to_iso(event_date_str)
        if parsed_iso_date and copied_event['event_date_iso'] != parsed_iso_date :
            if not copied_event['event_date_iso']: dates_successfully_parsed_count +=1
            copied_event['event_date_iso'] = parsed_iso_date
            
        detailed_text_content = copied_event.get('detailed_text')
        if not copied_event['event_date_iso'] and detailed_text_content:
            date_patterns = re.findall(
                r'(\d{4}-\d{1,2}-\d{1,2})|(\d{1,2}[-/]\d{1,2}[-/]\d{4})|(\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})|((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4})',
                detailed_text_content, re.IGNORECASE)
            for match_tuple in date_patterns:
                for potential_date_str in match_tuple:
                    if potential_date_str:
                        parsed_iso_from_text = parse_date_to_iso(potential_date_str)
                        if parsed_iso_from_text and copied_event['event_date_iso'] != parsed_iso_from_text:
                            if not copied_event['event_date_iso']: dates_successfully_parsed_count += 1
                            copied_event['event_date_iso'] = parsed_iso_from_text
                            break
                if copied_event['event_date_iso'] and (not parsed_iso_date or copied_event['event_date_iso'] != parsed_iso_date): break
        
        if detailed_text_content:
            original_free_status = copied_event.get('is_free_indicator_present', False)
            refined_free_status = is_event_free(detailed_text_content)
            if refined_free_status != original_free_status:
                copied_event['is_free_indicator_present'] = refined_free_status
                free_status_refined_count +=1
        
        # PDF Processing Skipped Logic (Ensure it's applied to all)
        target_pdf_url = None
        if copied_event.get('site_scraped_from') == "https://www.education.gov.in" and \
           copied_event.get('source_url', '').lower().endswith('.pdf'):
            target_pdf_url = copied_event['source_url']
        elif copied_event.get('primary_pdf_url_on_detail_page'):
            target_pdf_url = copied_event['primary_pdf_url_on_detail_page']
        
        if target_pdf_url:
            pdfs_identified_as_candidates_count += 1
            copied_event['pdf_extracted_text'] = "PDF_PROCESSING_SKIPPED_DUE_TO_TIMEOUTS"
        
        final_events.append(copied_event)

    save_events_to_json(final_events, output_filepath)

    print("\n--- Overall Enrichment Summary (v4_llm_classified_plus_batch_HTML) ---")
    print(f"Total events processed: {len(events_data)}")
    print(f"Batch items for which HTML details were processed in this run: {batch_items_html_processed_count}/{len(BATCH_URLS_SET)}")
    print(f"Dates successfully parsed/updated to ISO format: {dates_successfully_parsed_count}")
    print(f"Free status indicators refined using detailed_text: {free_status_refined_count}")
    print(f"PDFs identified as candidates (processing was SKIPPED): {pdfs_identified_as_candidates_count}")
    print(f"Data saved to: {output_filepath}")

if __name__ == "__main__":
    main()
