# Trademark Services Performance Analysis

## Problem Statement
"one report is 9 hours" and "costs 15 dollars"

## Current Performance Reality
**Identified Processing Time: ~28 minutes** and costs of ~$1 per search in API calls (OpenAI).

### Analysed Breakdown:
1. **Rule Evaluation**: 400+ individual OpenAI API calls
   - 200+ trademark matches + 200+ high-scoring web results (≥8.0)
   - Time: 400 calls × 2-3 seconds = **13-20 minutes**
   - Cost: 400 calls × ~$0.002 = **$0.80 per search**

2. **Similarity Scoring**: 1,950+ individual embedding API calls
   - 200 trademark matches (1 call each)
   - 1,600+ web search candidates (200 results × 8 candidates each)
   - 150 game products (board/slot/video games)
   - Time: 1,950 calls × 200ms = **6.5+ minutes**
   - Cost: 1,950 calls × ~$0.0001 = **$0.20 per search**

3. **Image Downloads**: 50-200 trademark images
   - Time: **1-3 minutes**
   - Cost: CloudFront bandwidth = **~$0.01 per search**

#### The core issue: 
The massive API call volume (2,350+ calls total: 400+ rule evaluation + 1,950+ similarity scoring) combined with sequential processing creates significant performance bottlenecks. The system makes individual API calls instead of batching, leading to network latency accumulation and potential rate limiting delays.

### Optimized Breakdown (After P1 & P2 Fixes listed below):
1. **Rule Evaluation**: Batched OpenAI API calls
   - Time: 2-4 batch calls × 30-60 seconds = **2-4 minutes**
   - Cost: 2-4 calls × ~$0.20 = **$0.80 per search** (same cost, faster delivery)

2. **Similarity Scoring**: Local BERT model batch processing
   - Time: Single batch operation = **under 2 seconds**
   - Cost: Local processing = **$0.00 per search** (eliminates $0.20 API cost)

3. **Image Downloads**: 50-200 trademark images (unchanged)
   - Time: **1-3 minutes**
   - Cost: CloudFront bandwidth = **~$0.01 per search**

4. **Other Processing**: Web search, report generation, etc.
   - Time: **2-5 minutes**
   - Cost: Minimal server resources

**Optimized Total**: **7-12 minutes** and costs of **$0.81 per search**
- **Time improvement**: ~28 minutes → 7-12 minutes (60%+ reduction)
- **Cost improvement**: $1.01 → $0.81 (20% reduction)
- **Note**: If there are additional unknown bottlenecks beyond the identified work, further investigation needed

## Performance Bottlenecks Identified

### 1. Sequential OpenAI API Calls

**Performance Impact:** High

**Why This Is Needed:**
The system must evaluate complex trademark rules that require legal reasoning beyond simple string matching. Rules like "phonetically similar", "same grammatical structure", and "conceptual similarity" need AI analysis to determine if "Dragon's Fortune" conflicts with "Fortune Dragon" or if "Moonshine Madness" is too similar to "Moonshine Cocktail". This legal analysis is core to providing accurate risk assessments.

**Impact:**
- Up to 200 trademark matches requiring individual rule evaluation
- Each `evaluate_rules_shortcircuit()` call makes OpenAI API request
- Sequential processing: 200 calls × 2-3 seconds = **10-15 minutes minimum**
- API rate limiting can extend this to hours

**Why It's Slow:**
- No batching of similar evaluations
- Each comparison is treated as separate API request
- OpenAI API has rate limits and latency
- Network round-trips for each evaluation

**Challenge:**
The LLM approach may be architectural overkill. Many trademark rules (phonetic similarity, identical marks, single word matches) could be handled by faster specialized algorithms (Soundex, Levenshtein distance, regex patterns) in milliseconds rather than seconds. The current system uses LLM as a "universal solver" when purpose-built tools might be more efficient.

**Recommendation:**
Implement batched API calls as the minimum viable fix. Instead of 200 individual API calls taking 10-15 minutes, batch all comparisons into 1-2 API calls taking 2-3 minutes total. This maintains the same LLM accuracy and legal reasoning quality while achieving 80% time reduction with minimal code changes.

### 2. Similarity Scoring Volume

**Performance Impact:** High

**Why This Is Needed:**
Similarity scoring is essential for ranking and filtering results by relevance. Without semantic scoring, users would get hundreds of irrelevant results like "Dragon Slayer" when searching for "Dragon's Fortune". The system needs to calculate semantic similarity to identify which of 200+ trademark matches are actually concerning and which can be safely ignored. This scoring also determines which web results meet the 8.0+ threshold for rule evaluation.

**Impact:**
- **1,950+ individual OpenAI API calls per search**:
  - 200 trademark matches (1 call each)
  - 1,600+ web search candidates (200 results × 8 candidates each)
  - 150 game products (board/slot/video games)
- **6.5+ minutes just for embedding API calls** (1,950 × 200ms each)
- **$0.20+ in API costs per search** ($0.00013 per 1K tokens for text-embedding-3-large)
- Network latency, rate limiting, and external service dependency
- LRU cache (20K entries) helps with repeated searches but doesn't eliminate the core volume problem

**Challenge:**
The system makes individual OpenAI API calls for every semantic similarity comparison, creating a massive API call explosion. Web search results extract up to 8 candidate names each (PER_ROW_MAXCANDS = 8), turning 200 web results into 1,600+ API calls. Combined with trademark and product scoring, this reaches 1,950+ individual API calls per search. Even with LRU caching, the sheer volume of unique comparisons overwhelms the cache and creates unavoidable network latency bottlenecks.

**Recommendation:**
Replace the 1,950+ individual OpenAI API calls with local BERT model batch processing. Use `all-mpnet-base-v2` loaded at startup to compute all embeddings (search term + 200 trademarks + 1,600 web candidates + 150 products) in a single batch operation (~1-2 seconds), then vectorized cosine similarity for all 1,950+ comparisons simultaneously. This reduces 6.5+ minutes of API calls to under 2 seconds of local processing while eliminating $0.20+ per search in API costs.

### 3. Image Download and Processing

**Performance Impact:** Low

**Why This Is Needed:**
Trademark images are crucial for legal analysis because many trademarks are logos, designs, or stylized text rather than plain word marks. Legal teams need to visually compare trademark designs to assess likelihood of confusion. A text search might miss that "DRAGON" in gothic font looks very similar to an existing dragon logo. The Excel report must include these images for proper legal review and decision-making.

**Impact:**
- Downloads 50-200+ trademark images from TMTKO CloudFront CDN
- Multiple images per trademark (logos, designs, stylized text)
- Network latency: 100-500ms per image download
- Image processing: Resize, format conversion, Excel embedding
- Sequential processing despite async TaskGroup
- Total time: 1-3 minutes for image downloads and processing

### 4. Web Search Processing Scale

**Performance Impact:** Medium

**Why This Is Needed:**
Web search is essential for finding common law trademark rights and marketplace usage that wouldn't appear in official trademark databases. A company might be using "Dragon's Fortune" as a brand name without registering it, or there might be social media accounts, apps, or websites using similar names. This "common law" usage can still create legal conflicts, so comprehensive web search across multiple platforms (social media, app stores, gaming sites) is necessary for complete risk assessment.

**Impact:**
- Multiple search query types (7+ different searches)
- Up to 3 pages per query = 21+ API calls to Google
- Each result requires similarity scoring
- High-scoring results (≥8.0) require additional rule evaluation

### 5. Inefficient Caching Strategy

**Performance Impact:** Low

**Why This Is Needed:**
Caching is critical because many trademark comparisons are repeated across different searches. If multiple users search for gaming terms like "Fortune", "Dragon", "Casino", or "Slots", the system will repeatedly evaluate the same trademark conflicts. Additionally, within a single search, the same trademark might appear in multiple jurisdictions or the same web result might appear in different search categories. Effective caching prevents redundant expensive API calls and computations.

**Impact:**
- Cache is local to single search session
- No persistence across searches
- Duplicate work for similar trademark terms
- No pre-computation of common comparisons

