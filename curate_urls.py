import os
from urllib.parse import urlparse, urlunparse
import collections

NON_HTML_EXTENSIONS = [
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',  # Images & Docs
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', # Office Docs
    '.zip', '.gz', '.tar', '.rar', '.7z', # Archives
    '.mp4', '.avi', '.mov', '.wmv', '.flv', # Videos
    '.mp3', '.wav', '.aac', '.ogg', # Audio
    '.txt', '.csv', '.xml', '.json', '.rtf', # Plain text & data
    '.exe', '.msi', '.dmg', '.pkg', # Executables
    '.css', '.js' # Web assets that aren't primary content pages
]

def normalize_url(url_string: str) -> str:
    """
    Normalizes a URL: ensures it has a scheme (defaults to http) and removes trailing slashes.
    """
    if not url_string:
        return ""
    
    parsed = urlparse(url_string)
    
    scheme = parsed.scheme if parsed.scheme else 'http'
    netloc = parsed.netloc
    path = parsed.path.rstrip('/') if parsed.path else '' # Remove trailing slash from path
    
    # Reconstruct without query, params, fragment for this normalization,
    # or include them if they should be preserved (subtask implies general normalization)
    # For simple normalization (scheme, netloc, path without trailing slash):
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))

def main():
    input_file_path = "data/government_sites.txt"
    curated_output_file_path = "data/government_sites.txt" # Overwrite
    removed_output_file_path = "data/curation_removed_urls.txt"

    initial_urls = []
    if os.path.exists(input_file_path):
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                initial_urls = [line.strip() for line in f if line.strip()]
        except IOError as e:
            print(f"Error reading input file {input_file_path}: {e}")
            return
    else:
        print(f"Input file not found: {input_file_path}. Nothing to curate.")
        # Create empty output files for consistency if script is run on non-existent input
        open(curated_output_file_path, 'w').close()
        open(removed_output_file_path, 'w').close()
        print("Created empty output files.")
        return

    initial_url_count = len(initial_urls)
    print(f"Read {initial_url_count} URLs from {input_file_path}.")

    curated_urls = []
    removed_urls_with_reasons = [] # List of tuples (url, reason)
    reason_counts = collections.Counter()

    for raw_url in initial_urls:
        url = normalize_url(raw_url)
        
        # Ensure normalization didn't break it (e.g., if raw_url was just "htp://nonsense")
        try:
            parsed_url = urlparse(url)
        except ValueError:
            removed_urls_with_reasons.append((raw_url, "normalization/parse error"))
            reason_counts["normalization/parse error"] += 1
            continue

        # 1. Valid Scheme/Netloc Check
        if not (parsed_url.scheme in ['http', 'https'] and parsed_url.netloc):
            removed_urls_with_reasons.append((raw_url, "invalid URL structure"))
            reason_counts["invalid URL structure"] += 1
            continue
            
        # 2. File Extension Check
        path_lower = parsed_url.path.lower()
        is_non_html_file = any(path_lower.endswith(ext) for ext in NON_HTML_EXTENSIONS)
        if is_non_html_file:
            removed_urls_with_reasons.append((raw_url, "non-HTML file"))
            reason_counts["non-HTML file"] += 1
            continue
        
        # If all checks pass
        curated_urls.append(url)

    # Remove duplicates from curated list (after normalization)
    final_curated_urls = sorted(list(set(curated_urls)))
    final_url_count = len(final_curated_urls)

    # Save curated URLs
    try:
        with open(curated_output_file_path, 'w', encoding='utf-8') as f:
            for url_to_save in final_curated_urls:
                f.write(url_to_save + "\n")
        print(f"Successfully saved {final_url_count} curated URLs to {curated_output_file_path}.")
    except IOError as e:
        print(f"Error writing curated URLs to {curated_output_file_path}: {e}")

    # Save removed URLs
    try:
        with open(removed_output_file_path, 'w', encoding='utf-8') as f:
            for removed_url, reason in removed_urls_with_reasons:
                f.write(f"{removed_url} - {reason}\n")
        print(f"Successfully saved {len(removed_urls_with_reasons)} removed URLs to {removed_output_file_path}.")
    except IOError as e:
        print(f"Error writing removed URLs to {removed_output_file_path}: {e}")

    # Report
    print("\n--- Curation Report ---")
    print(f"Initial number of URLs: {initial_url_count}")
    print(f"Number of URLs removed: {len(removed_urls_with_reasons)}")
    if len(removed_urls_with_reasons) > 0:
        print("Reasons for removal:")
        for reason, count in reason_counts.items():
            print(f"  - {reason}: {count}")
    print(f"Final number of curated URLs: {final_url_count}")

if __name__ == "__main__":
    main()
