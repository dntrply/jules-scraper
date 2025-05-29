import json
import pandas as pd
import os

def main():
    print("Starting JSON to CSV conversion...")

    json_file_path = "data/extracted_events_v4_llm_classified.json"
    csv_file_path = "data/visualization_events_data.csv"

    # Ensure the output directory exists
    try:
        os.makedirs("data", exist_ok=True)
    except OSError as e:
        print(f"Error creating directory 'data': {e}")
        return # Cannot proceed if directory creation fails

    # Load JSON data
    print(f"Loading JSON data from: {json_file_path}")
    if not os.path.exists(json_file_path):
        print(f"Error: Input JSON file not found: {json_file_path}")
        return
        
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} records from JSON.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {json_file_path}: {e}")
        return
    except IOError as e:
        print(f"Error reading file {json_file_path}: {e}")
        return
    except Exception as e: # Catch any other unexpected error during loading
        print(f"An unexpected error occurred while loading JSON: {e}")
        return

    if not data or not isinstance(data, list):
        print("No data or invalid data format in JSON file. CSV will be empty or not created.")
        # Create an empty CSV if no data or handle as error
        if isinstance(data, list) and not data: # If it's an empty list
             df = pd.DataFrame()
        else: # If data is not a list (e.g. None due to earlier error, or wrong type)
            print("Exiting due to invalid data format from JSON.")
            return
    else:
        # Convert to Pandas DataFrame
        try:
            df = pd.DataFrame(data)
            print(f"Successfully converted data to Pandas DataFrame with {len(df)} records.")
        except Exception as e:
            print(f"Error converting JSON data to DataFrame: {e}")
            return

    # Optional: Define preferred column order (as per subtask description)
    # For simplicity, if not all columns are guaranteed, pandas will order them automatically.
    # If a specific order is desired, a more robust way is to get existing columns and reorder
    # those that are present, and append any others.
    # Example:
    # preferred_columns = [
    #     'event_title', 'event_date_iso', 'event_date_str',
    #     'is_attendable_event_llm', 'cost_status_llm',
    #     'is_free_indicator_present', 
    #     'detailed_text', 'pdf_extracted_text',
    #     'source_url', 'primary_pdf_url_on_detail_page',
    #     'site_scraped_from'
    # ]
    # existing_columns = df.columns.tolist()
    # final_columns = [col for col in preferred_columns if col in existing_columns]
    # remaining_columns = [col for col in existing_columns if col not in preferred_columns]
    # df = df[final_columns + remaining_columns]
    # For this task, let's rely on pandas' default column order from the JSON keys.

    # Save to CSV
    print(f"Saving DataFrame to CSV: {csv_file_path}")
    try:
        df.to_csv(csv_file_path, index=False, encoding='utf-8')
        print(f"Successfully converted and saved {len(df)} records to {csv_file_path}")
    except IOError as e:
        print(f"Error writing CSV to {csv_file_path}: {e}")
    except Exception as e: # Catch any other unexpected error during CSV saving
        print(f"An unexpected error occurred while saving CSV: {e}")

if __name__ == "__main__":
    main()
