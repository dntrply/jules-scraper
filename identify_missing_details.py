import json
import os

def load_events_from_json(filepath: str) -> list[dict] | None:
    """
    Loads a list of event dictionaries from a JSON file.
    """
    print(f"Loading events from JSON file: {filepath}")
    if not os.path.exists(filepath):
        print(f"  Error: File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            events = json.load(f)
        print(f"  Successfully loaded {len(events)} events from {filepath}.")
        return events
    except json.JSONDecodeError as e:
        print(f"  Error decoding JSON from {filepath}: {e}")
        return None
    except IOError as e:
        print(f"  Error reading file {filepath}: {e}")
        return None

def main():
    print("Starting identification of missing HTML details...")

    filepath_v1 = "data/extracted_events_v1.json"
    filepath_v4 = "data/extracted_events_v4_llm_classified.json"

    events_v1 = load_events_from_json(filepath_v1)
    events_v4 = load_events_from_json(filepath_v4)

    if events_v1 is None:
        print(f"Could not load events from {filepath_v1}. Exiting.")
        return
    if events_v4 is None:
        print(f"Could not load events from {filepath_v4}. Exiting.")
        return
        
    if len(events_v1) == 0:
        print(f"No events found in {filepath_v1}. Exiting.")
        return
    if len(events_v4) == 0: # Should not happen if v1 has events and v4 is derived.
        print(f"No events found in {filepath_v4}, though v1 has events. This is unexpected. Exiting.")
        return


    # Create a dictionary from events_v4 for efficient lookup by source_url
    events_v4_dict = {}
    for event_v4_item in events_v4:
        source_url = event_v4_item.get('source_url')
        if source_url:
            events_v4_dict[source_url] = event_v4_item
        else:
            print("Warning: Found event in v4 without a source_url.")


    remaining_html_detail_candidates_urls = []
    inconsistent_items_count = 0

    for event_v1_item in events_v1:
        source_url_v1 = event_v1_item.get('source_url')
        if not source_url_v1:
            # print(f"Warning: Event in v1 missing source_url: {event_v1_item.get('event_title', 'N/A')}")
            continue

        event_v4_item = events_v4_dict.get(source_url_v1)

        if not event_v4_item:
            # print(f"Warning: Event from v1 with source_url '{source_url_v1}' not found in v4 data.")
            # This can happen if v1 had items that were filtered out before v4 stage, or if v4 processing was incomplete.
            # For this task, we assume v4 is the "current state" and v1 defines "potential candidates".
            # If an item from v1 isn't in v4, its detailed_text status is unknown from v4's perspective.
            # We will consider it as if its detailed_text is missing for candidacy check.
            inconsistent_items_count +=1
            # For the purpose of this task, assume detailed_text is missing if not in v4
            detailed_text_v4 = None 
        else:
            detailed_text_v4 = event_v4_item.get('detailed_text')

        is_candidate = False
        site_scraped_from_v1 = event_v1_item.get('site_scraped_from')

        # Check if it's an HTML detail candidate
        if site_scraped_from_v1 == "https://pib.gov.in" and \
           source_url_v1 and "PressReleseDetail.aspx" in source_url_v1: # Typo "Relese" is intentional as per actual URLs
            is_candidate = True
        elif site_scraped_from_v1 == "https://allurisitharamaraju.ap.gov.in" and \
             source_url_v1 and "/document/" in source_url_v1:
            is_candidate = True
        
        # Check if detailed_text is missing or empty
        detailed_text_is_missing = not detailed_text_v4 # Handles None or empty string

        if is_candidate and detailed_text_is_missing:
            remaining_html_detail_candidates_urls.append(source_url_v1)

    if inconsistent_items_count > 0:
        print(f"\nWarning: Found {inconsistent_items_count} items from '{filepath_v1}' that were not present in '{filepath_v4}'. These were treated as having missing detailed_text if they were candidates.")

    print(f"\n--- Identification Report ---")
    print(f"Total HTML detail candidates with missing 'detailed_text': {len(remaining_html_detail_candidates_urls)}")
    
    if remaining_html_detail_candidates_urls:
        print("\nFirst 10-15 URLs for reprocessing HTML details:")
        for i, url in enumerate(remaining_html_detail_candidates_urls):
            if i < 15:
                print(f"  {i+1}. {url}")
            else:
                break
    else:
        print("No HTML detail candidates found with missing 'detailed_text'.")
        
    print("\nIdentification script finished.")

if __name__ == "__main__":
    main()
