import os
import re # For parsing the plain text "Visible links" section
from urllib.parse import urljoin, urlparse

# Define the base URL for resolving relative links (though most should be absolute from view_text_website)
BASE_IGOD_URL = "https://igod.gov.in" # Kept for get_absolute_url, though less critical now

INDIAN_GOV_TLDS_PRIMARY = ['.gov.in', '.nic.in']


def get_absolute_url(base_url: str, link: str) -> str:
    """
    Converts a link (href attribute value) to an absolute URL if it's relative,
    using the provided base_url.
    """
    if not link:
        return ""
    
    parsed_link = urlparse(link)
    # A URL is absolute if it has a scheme (e.g., 'http', 'https') and a netloc (domain).
    if parsed_link.scheme and parsed_link.netloc:
        return link
    return urljoin(base_url, link)


def is_government_site_url(url_string: str) -> bool:
    """
    Checks if a URL string is likely an external Indian government website.
    """
    if not url_string:
        return False

    if not (url_string.startswith('http://') or url_string.startswith('https://')):
        return False

    try:
        parsed_url = urlparse(url_string)
    except ValueError:
        return False 

    if parsed_url.scheme not in ['http', 'https']:
        return False

    hostname = parsed_url.hostname
    if not hostname: 
        return False
    if hostname == 'igod.gov.in' or hostname == 'www.igod.gov.in':
        return False

    is_gov_tld = any(hostname.endswith(tld) for tld in INDIAN_GOV_TLDS_PRIMARY)
    
    if is_gov_tld:
        # Optional: filter out direct document links
        if parsed_url.path.lower().endswith(('.pdf', '.jpg', '.png', '.zip', '.doc', '.docx', '.xls', '.xlsx')):
            # print(f"  Skipping likely document/image link: {url_string}")
            return False
        return True

    return False

def extract_urls_from_view_text_output(file_content: str) -> list[str]:
    """
    Extracts URLs from the "Visible links:" section of view_text_website plain text output.
    """
    urls = []
    in_visible_links_section = False
    
    # Regex to find lines like "  1. https://example.com" or "123. https://example.com"
    # It captures the URL part.
    # The pattern allows for optional leading digits/letters for list items (e.g. [1], a., 1.)
    link_pattern = re.compile(r'^\s*(?:\[?\w+\]?\s*|\w+\.\s+)?(https?://\S+)')
    # Simpler pattern focusing on numbered list from "Visible links:"
    # Example: "   1. https://actual.url/path"
    # Example: "  15. https://igod.gov.in/sg/AN/categories" (from Turn 10 output)
    numbered_link_pattern = re.compile(r'^\s*\d+\.\s+(https?://\S+)')

    lines = file_content.splitlines()
    for line in lines:
        if "Visible links:" in line:
            in_visible_links_section = True
            continue
        
        # If we encounter "Hidden links:" or other delimiters, stop processing visible links.
        if in_visible_links_section and ("Hidden links:" in line or "----" in line or "References" in line and "Visible links:" not in line) :
            in_visible_links_section = False
            # Stop if we are clearly out of the section, prevents reading "Saved VCL" etc.
            break 
            
        if in_visible_links_section:
            match = numbered_link_pattern.match(line)
            if match:
                url = match.group(1).strip()
                # Further clean URL if it has trailing characters from the text dump, e.g. quotes or brackets
                # For now, assuming \S+ in regex is greedy enough but not too greedy.
                urls.append(url)
    return urls


def main():
    """
    Main function to parse local HTML text dump files and extract government website URLs.
    """
    collected_urls = set()
    html_files_directory = "data/html_sources/"
    output_file_path = "data/government_sites.txt"

    print(f"Starting parsing of HTML text dump files in {html_files_directory} (plain text mode)...")

    if not os.path.exists(html_files_directory):
        print(f"Error: Directory not found: {html_files_directory}")
        return

    for filename in os.listdir(html_files_directory):
        if filename.endswith(".html"): # Files are named .html but contain text
            file_path = os.path.join(html_files_directory, filename)
            print(f"Processing file: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except IOError as e:
                print(f"  Error reading file {file_path}: {e}")
                continue
            
            extracted_raw_urls = extract_urls_from_view_text_output(file_content)
            
            found_links_in_file = 0
            if not extracted_raw_urls:
                print(f"  No URLs found in 'Visible links:' section of {file_path} using regex.")
            
            for raw_url in extracted_raw_urls:
                # Links from "Visible links" are typically already absolute.
                absolute_url = get_absolute_url(BASE_IGOD_URL, raw_url) 
                
                if absolute_url.startswith('javascript:'): # Filter javascript pseudo-protocol
                    continue

                if is_government_site_url(absolute_url):
                    collected_urls.add(absolute_url)
                    found_links_in_file +=1
            
            if found_links_in_file > 0:
                 print(f"  Extracted {found_links_in_file} valid government URLs from {file_path}.")


    print(f"\nProcessed all files. Found {len(collected_urls)} unique government URLs.")

    data_dir = os.path.dirname(output_file_path) 
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            print(f"Created directory: {data_dir}")
        except OSError as e:
            if not os.path.isdir(data_dir): 
                print(f"Error creating directory {data_dir}: {e}")
                return 
            
    try:
        with open(output_file_path, 'w') as f:
            for url in sorted(list(collected_urls)):
                f.write(url + "\n")
        print(f"Results saved to: {output_file_path}")
    except IOError as e:
        print(f"Error writing to file {output_file_path}: {e}")

if __name__ == "__main__":
    main()
