# Flow Map: Event Scraping Process

This document outlines the multi-stage pipeline for scraping event information.

## Optional Pre-Stage: General Site Discovery

- **Input:** Seed URLs (e.g., `igod.gov.in`)
- **Script:** `scraper.py`
- **Process:** Crawls seed URLs to find links to various government department websites.
- **Output:** `data/collected_igod_urls.txt` (List of potential government websites)

```
     |
     V
```

## Stage 1: Initial Event Discovery & Detail URL Extraction

- **Input:** Hardcoded list of event *listing page* URLs (e.g., `.../events`, `.../press-releases`)
- **Script:** `event_scraper_v1.py`
- **Process:**
    1. Fetch HTML from each event *listing* page.
    2. Parse listing page HTML (using site-specific parsers like `parse_india_gov_events`):
       - Find links to individual *event detail* pages.
       - Extract:
         - `event_title` (from link text)
         - `source_url` (URL to the event detail page) <-- Initial "Decided URL"
         - `event_date_str` (preliminary)
         - `is_free_indicator_present` (preliminary, from title)
         - `site_scraped_from`
- **Output:** `data/extracted_events_v1.json` (List of candidate events with their detail URLs)

```
     |
     V
```

## Stage 2: Event Classification (Speculative)

- **Input:** `data/extracted_events_v1.json` (or similar)
- **Script:** `llm_event_classifier.py` (Likely)
- **Process:**
    1. Use LLM to analyze each candidate event (title, `source_url`).
    2. Classify if it's a relevant event a user might attend (filters out non-events).
- **Output:** `data/extracted_events_v4_llm_classified.json` (Refined list of event candidates, contains more qualified "Decided URLs")

```
     |
     V
```

## Stage 3: Detailed Event Scraping & Enrichment

- **Input:** `data/extracted_events_v4_llm_classified.json`
- **Script:** `event_scraper_v2.py`
- **Focus:** For each event `source_url` (the "Decided URL" from Stage 1/2):
- **Process:**
    1. Fetch HTML of the event *detail page* (`source_url`) using `fetch_html()`.
    2. Parse detail page HTML using site-specific parsers (e.g., `parse_pib_detail_page`, `parse_asr_district_document_page`):
       - Extract `detailed_text` (full event description).
       - Handle site structures (iframes, specific divs).
    3. Determine "Free" Status:
       - Analyze `detailed_text` for keywords ("free", "no fee", "complimentary") using `is_event_free()`.
       - Update `is_free_indicator_present`.
    4. Extract/Refine Dates:
       - Use `dateparser` and regex on `detailed_text` for `event_date_iso`.
    5. Identify PDFs:
       - Find links to PDFs on the page or if `source_url` is a PDF.
       - (Note: PDF content extraction is currently SKIPPED).
- **Output:** `data/extracted_events_v4_llm_classified.json` (Overwritten with enriched event details: `detailed_text`, refined date, more accurate `is_free_indicator_present`)

```

This textual representation should give a clearer, more diagram-like overview of the flow.
