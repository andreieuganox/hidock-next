# Trademark Services

A trademark search and analysis system that searches multiple data sources and generates Excel reports with similarity scoring and risk assessment.

## What It Does

The trademark services module performs automated trademark clearance searches by:
- Querying trademark databases via TMTKO API
- Searching web content via Google Custom Search API
- Searching gaming databases (board games, slot games, video games)
- Applying similarity scoring and rule-based risk evaluation
- Generating Excel workbooks with multiple worksheets
- Creating AI-generated legal summaries via OpenAI API

## How It Works

### Step 1: Input Processing

The main function `get_trademark_report_workbook()` accepts:
- `search`: The trademark term to search for
- `jurisdictions`: Optional list of jurisdictions to search (defaults to all)
- `db_session`: Database session for local game searches

### Step 2: Concurrent Data Collection

The system uses `asyncio.gather()` to run five searches simultaneously:

#### 1. TMTKO Trademark Search (`get_trademark_report_items`)
- Calls TMTKO API with `KnockoutMarkRequest`
- Searches up to 200 matches across specified jurisdictions
- Filters for live statuses: 'Published', 'Registered', 'Pending'
- Returns `TrademarkReportItem` objects with registration details

#### 2. Google Web Search (`get_websearch_results`)
- Uses Google Custom Search API with predefined query templates
- Searches multiple categories: common_law, social_media, store, class-specific
- Applies webpage scoring algorithm to rank relevance
- Returns `ScoredWebsearchResult` objects

#### 3. Board Game Search (`search_board_games`)
- Queries local database for board game titles
- Converts to `ReleasedProduct` objects with BoardGameGeek URLs

#### 4. Slot Game Search (`search_slot_games`)
- Queries local database for slot game titles
- Converts to `ReleasedProduct` objects

#### 5. Video Game Search (`search_igdb_games`)
- Calls IGDB API for video game titles
- Converts to `ReleasedProduct` objects with release dates

### Step 3: Similarity Scoring

Each data source gets processed through similarity scoring:

#### Semantic Scoring (`get_combined_score`)
- Uses ML models to calculate semantic similarity between search term and found items
- Returns scores for semantic, spelling, and phonetic similarity
- Applied to trademark mark_identification, product names, and web candidates

#### Web Search Scoring (`score_row`)
- Analyzes title, snippet, and URL for relevance
- Applies industry-specific term bonuses
- Filters results with webpage_score >= 8.0 for rule evaluation

#### Social Media Deduplication (`canonical_bucket_key`)
- Groups social media profiles by platform and username
- Prevents duplicate analysis of same entity across multiple URLs
- Supports major platforms: Facebook, Instagram, YouTube, TikTok, Twitter, LinkedIn, etc.

### Step 4: Rule-Based Risk Assessment

The system applies trademark rules via `evaluate_rules_shortcircuit()`:

#### Rule Categories
- **High Risk Rules**: `high_identical`, `high_nearly_identical`
- **Medium Risk Rules**: `two_words_plus_different`, `phonetically_similar`, `single_word_match`, etc.

#### Short-Circuit Logic
- Evaluates high-risk rules first
- If any high-risk rule matches, returns "High" risk and stops
- Otherwise evaluates all medium/low risk rules
- Returns "Medium" if any medium rule matches, else "Low"

#### Rule Evaluation Process
- Uses OpenAI API with structured output (`TrademarkComparison` schema)
- Caches results to avoid duplicate evaluations of identical terms
- Returns boolean results, explanations, and overall risk level for each comparison

### Step 5: Excel Report Generation

The system generates an Excel workbook using `populate_trademark_workbook()`:

#### Worksheet Structure
- **Search**: Search parameters and timestamp
- **Trademark Report**: TMTKO results with trademark images, legal details, and rule evaluations
- **Web search**: Google search results filtered to webpage_score >= 8.0
- **Board games**: BoardGameGeek results with similarity scores
- **Slot catalog**: Internal slot game database results
- **Video games**: IGDB results with release dates

#### Report Features
- **Color-coded sections**: Different background colors for data categories
- **Conditional formatting**: Highlights high-scoring results
- **Hyperlinks**: Clickable URLs and trademark office links
- **Images**: Downloads and embeds trademark images from TMTKO
- **Rule columns**: Shows rule evaluation results and explanations for each item
- **Sorting**: Orders results by similarity scores

#### AI-Generated Summary (`get_trademark_report_summary`)
Creates PDF legal summary using OpenAI API:

**Data Processing**:
- Reads Excel worksheets into pandas DataFrames
- Filters web results to webpage_score >= 8.0
- Combines product data from all gaming sources
- Includes rule evaluation results and risk assessments

**OpenAI Integration**:
- Uses GPT-5 model with structured prompts
- System prompt defines trademark analyst role for iGaming industry
- User prompt includes search term, jurisdictions, and formatted data tables
- Includes goods & services importance mapping for legal analysis

**Output Format**:
- Returns PDF document with legal analysis
- Structured sections: earlier trademarks, web results, existing games, recommendations
- Risk classification and actionable guidance

## Key Implementation Details

### Data Models
- **TrademarkReportItem**: Trademark registration data with legal details
- **ScoredWebsearchResult**: Web search results with scoring and candidate extraction
- **ReleasedProduct**: Game titles from various databases with metadata

### Search Query Templates
The system uses predefined search templates in `mappings.py`:
- **Common law**: Basic trademark term search
- **Social media**: Site-specific searches across major platforms
- **Store**: App store and gaming platform searches
- **Class-specific**: Searches tailored to trademark classes 9, 16, 28, 38, 41, 42

### Concurrent Processing
- Uses `asyncio.gather()` for parallel API calls
- `ProcessPoolExecutor` for CPU-intensive similarity scoring
- `asyncio.to_thread()` for blocking operations like sorting and Excel generation

### Caching and Deduplication
- `_normalize_key()` creates consistent keys for deduplication
- Caches rule evaluation results to avoid redundant API calls
- Groups social media results by platform and username

## API Dependencies

### Required External Services
- **TMTKO API**: Trademark database access
- **Google Custom Search API**: Web search functionality
- **IGDB API**: Video game database
- **OpenAI API**: Rule evaluation and summary generation

### Configuration Requirements
- Google API key and Custom Search Engine ID
- TMTKO API credentials
- IGDB API token
- OpenAI API key
- Database connection for local game catalogs

## Output Formats

### Excel Workbook Structure
```
Search/                    # Search parameters and metadata
Trademark Report/          # TMTKO results with images and rule evaluations
Web search/               # Google results filtered by relevance score
Board games/              # BoardGameGeek results
Slot catalog/             # Internal slot game database
Video games/              # IGDB results
```

### Rule Evaluation Columns
Each worksheet includes paired columns for rule results:
- Rule name (True/False/not evaluated)
- Rule explanation (detailed reasoning)
- Overall risk assessment (High/Medium/Low)

### PDF Summary
- Executive summary with risk classification
- Detailed analysis by data source
- Legal recommendations and next steps
- Generated via OpenAI API with structured prompts

## Technical Architecture

### Core Components
- **Search Orchestration**: `get_trademark_report_workbook()` coordinates all searches
- **Data Sources**: TMTKO, Google Custom Search, IGDB, local databases
- **Similarity Engine**: ML-based scoring with `get_combined_score()`
- **Rule Engine**: OpenAI-powered trademark rule evaluation
- **Report Generation**: Excel workbook creation with openpyxl
- **Summary Generation**: AI-powered legal analysis via OpenAI

### Processing Flow
```
Input (search term, jurisdictions)
    ↓
Concurrent API calls (5 sources)
    ↓
Similarity scoring (semantic, spelling, phonetic)
    ↓
Rule evaluation (high-risk short-circuit logic)
    ↓
Excel report generation (6 worksheets)
    ↓
AI summary generation (PDF output)
```

### Error Handling
- Graceful degradation when API calls fail
- Exception handling with `return_exceptions=True`
- Partial results processing when some sources are unavailable

## Code Organization

### Main Module (`src/biab_legal_mate/services/trademarks/__init__.py`)
- `get_trademark_report_workbook()`: Main orchestration function
- `submit_trademark_search_job()`: Job submission for async processing
- Helper functions for rule evaluation and data processing

### Supporting Modules
- **`searching.py`**: API integration for TMTKO, Google, IGDB
- **`scoring.py`**: Similarity algorithms and social media deduplication
- **`report.py`**: Excel workbook generation and formatting
- **`helpers.py`**: Data transformation and sorting utilities
- **`mappings.py`**: Search query templates and jurisdiction mappings
- **`prompts.py`**: OpenAI integration for legal summaries

### Data Transfer Objects (`dto/trademarks.py`)
- `TrademarkReportItem`: Trademark registration data structure
- `ScoredWebsearchResult`: Web search results with scoring
- `ReleasedProduct`: Game title data from various sources
- `TrademarkSearchJobDTO`: Job tracking and status

### Rule Engine (`core/similarity_engine/trademark_rules.py`)
- `TrademarkRules`: Pydantic model defining all trademark rules
- `evaluate_rules_shortcircuit()`: Main rule evaluation function
- `get_rule_headers()`: Returns human-readable rule names
- OpenAI integration for structured rule evaluation


