import json
import os
import re

# --- Reusable Helper Functions (from event_scraper_v2.py) ---

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
        print(f"  Successfully loaded {len(events)} events.")
        return events
    except json.JSONDecodeError as e:
        print(f"  Error decoding JSON from {filepath}: {e}")
        return None
    except IOError as e:
        print(f"  Error reading file {filepath}: {e}")
        return None

def save_events_to_json(events_list: list[dict], filepath: str):
    """
    Saves a list of event dictionaries to a JSON file.
    """
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

# --- LLM Simulation Logic ---

def simulate_llm_call(prompt_name: str, text_to_classify: str | None) -> str:
    """
    Simulates an LLM call for classifying event type or cost based on heuristics.
    """
    print(f"DEBUG: Simulating LLM for prompt: {prompt_name} with text: '{str(text_to_classify)[:100]}...'")

    if not text_to_classify or len(text_to_classify) < 10:
        if prompt_name == "classify_event_type":
            return "UNCERTAIN"
        elif prompt_name == "classify_event_cost":
            return "UNCERTAIN_COST"
        return "ERROR_UNKNOWN_PROMPT"

    text_lower = text_to_classify.lower()

    if prompt_name == "classify_event_type":
        # Heuristics for event type
        negative_keywords = [
            "seizes", "seized", "arrested", "notification for recruitment", "recruitment of",
            "tender notice", "tender invited", "passed away", "condolence", 
            "rules notified", "clarification regarding", 
            "public notice regarding scheme extension" # Usually not an event unless about a launch
            # Add more specific non-event phrases if needed
        ]
        # More nuanced: some "public notice" can be about an event.
        # "public notice regarding scheme extension" might be borderline.
        
        positive_keywords = [
            "invitation to", "invites applications for workshop", "invites applications for contest",
            "workshop on", "festival", "webinar on", "training program", "exhibition of",
            "cultural event", "join us for", "public meeting on", "consultation on",
            "commemorates", "celebrates", "conference on", "symposium on", "lecture series",
            "awareness campaign on", "launch of" 
            # "public notice" alone is too ambiguous.
        ]

        for keyword in negative_keywords:
            if keyword in text_lower:
                # Special case: "public notice regarding scheme extension" might be an event if it's a launch.
                if "public notice regarding scheme extension" == keyword and "launch" in text_lower:
                    continue # Don't mark as NO if it's a launch event for the extension
                print(f"  DEBUG: Classified as NO due to negative keyword: '{keyword}'")
                return "NO"
        
        for keyword in positive_keywords:
            if keyword in text_lower:
                print(f"  DEBUG: Classified as YES due to positive keyword: '{keyword}'")
                return "YES"
        
        print("  DEBUG: No strong positive/negative keywords for event type. Classified as UNCERTAIN.")
        return "UNCERTAIN"

    elif prompt_name == "classify_event_cost":
        # Heuristics for event cost
        free_keywords = [
            "free entry", "free admission", "free participation", "no fee", "no cost", 
            "free registration", "open to all at no charge", "registration is free",
            "entry is free"
        ]
        paid_keywords = [
            "fee: rs", "cost: rs", "price: rs", "registration fee:", "charges apply",
            "ticket price:", "fee of rs", "payment of rs"
            # Consider currency symbols like ₹, $, etc. if needed, but problem specifies "rs"
        ]

        for keyword in free_keywords:
            if keyword in text_lower:
                print(f"  DEBUG: Classified as FREE due to keyword: '{keyword}'")
                return "FREE"
        
        for keyword in paid_keywords:
            if keyword in text_lower:
                print(f"  DEBUG: Classified as PAID due to keyword: '{keyword}'")
                return "PAID"
        
        # Check for numbers associated with fee/cost/price if keywords like "fee" are present but not full phrases
        if re.search(r'(?:fee|cost|price|charge|ticket)\s*(?:is|:|of)?\s*(?:rs\.?|inr|\₹)\s*\d+', text_lower):
            print("  DEBUG: Classified as PAID due to fee/cost pattern with amount.")
            return "PAID"
        if re.search(r'(?:rs\.?|inr|\₹)\s*\d+\s*(?:fee|cost|price|charge|ticket)', text_lower):
            print("  DEBUG: Classified as PAID due to amount followed by fee/cost pattern.")
            return "PAID"

        print("  DEBUG: No strong free/paid keywords for event cost. Classified as UNCERTAIN_COST.")
        return "UNCERTAIN_COST"
    
    else:
        print(f"  DEBUG: Unknown prompt name: {prompt_name}")
        return "ERROR_UNKNOWN_PROMPT"

# --- Main Script Logic ---

def main():
    print("Starting LLM classification script...")

    input_filepath = "data/extracted_events_v3_final_limited.json"
    output_filepath = "data/extracted_events_v4_llm_classified.json"

    events_data = load_events_from_json(input_filepath)

    if not events_data: # Handles None or empty list
        print(f"No events loaded from {input_filepath}. Exiting.")
        # Ensure output file is created even if empty, for consistency
        if not os.path.exists("data"): os.makedirs("data")
        save_events_to_json([], output_filepath)
        return

    output_events = []
    events_processed_count = 0
    attendable_event_count = 0
    free_event_count = 0

    for event in events_data:
        events_processed_count += 1
        copied_event = event.copy()

        # Use detailed_text if available and substantial, otherwise fall back to event_title
        text_for_llm_classification = None
        detailed_text = copied_event.get('detailed_text')
        event_title = copied_event.get('event_title', '') # Default to empty string if no title

        if detailed_text and len(detailed_text) > 50: # Prefer detailed_text if it's substantial
            text_for_llm_classification = detailed_text
        elif event_title: # Fallback to title
            text_for_llm_classification = event_title
        # If both are short or None, simulate_llm_call will handle it.

        # Default LLM classifications
        copied_event['is_attendable_event_llm'] = "UNCERTAIN"
        copied_event['cost_status_llm'] = "UNCERTAIN_COST"

        event_type = simulate_llm_call("classify_event_type", text_for_llm_classification)
        copied_event['is_attendable_event_llm'] = event_type

        if event_type == "YES":
            attendable_event_count += 1
            # Only classify cost if it's an attendable event
            cost_status = simulate_llm_call("classify_event_cost", text_for_llm_classification)
            copied_event['cost_status_llm'] = cost_status
            if cost_status == "FREE":
                free_event_count += 1
        else:
            # If not an attendable event, cost is not applicable
            copied_event['cost_status_llm'] = "NOT_APPLICABLE"
        
        output_events.append(copied_event)

    # Ensure data directory exists for output
    os.makedirs("data", exist_ok=True)
    save_events_to_json(output_events, output_filepath)

    print("\n--- LLM Classification Summary ---")
    print(f"Total events processed: {events_processed_count}")
    print(f"Events classified as ATTENDABLE ('YES'): {attendable_event_count}")
    print(f"Attendable events classified as FREE: {free_event_count}")
    print(f"Classified data saved to: {output_filepath}")
    print("LLM classification script finished.")

if __name__ == "__main__":
    main()
