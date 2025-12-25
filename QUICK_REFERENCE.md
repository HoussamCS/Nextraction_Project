# NEXTRACION Quick Reference

## What Is It?
A tool that crawls websites, indexes their content, and answers questions with **citations and evidence**.

## 3-Step Workflow

### Step 1 INGEST (Left Panel)
```
1. Add seed URL (e.g., https://docs.example.com)
2. Set allowed domains (e.g., docs.example.com)
3. Set Max Pages (10-50) & Max Depth (2-3)
4. Click "Start Ingestion"
5. SAVE the Job ID shown
```

### Step 2️⃣ MONITOR (Right Panel)
```
1. Paste Job ID into "Job ID" field
2. Click "Check Status"
3. Wait for status to change from RUNNING → DONE
4. Typical wait: 1-5 minutes (depends on page count)
```

### Step 3️⃣ ASK (Right Panel)
```
1. Keep same Job ID
2. Type your question
3. Click "Get Answer"
4. Read answer + citations + confidence level
```

---

## UI Sections

| Section | Purpose | Action |
|---------|---------|--------|
| Ingest | Crawl websites | Enter URLs, configure limits, click Start |
| Job ID | Track ingest job | Copy from Ingest result, paste in Ask |
| Ask | Query content | Paste Job ID, ask question, view answer |
| Health Status | Check API | Green = working, Red = offline |
| Citations | See sources | Click URL to visit source page |

---

## Answer Components

When you get an answer, you'll see:

```
Confidence: HIGH/MEDIUM/LOW
└─ Green = Trust it, Yellow = Check it, Red = Verify separately

Answer Text
└─ The actual response to your question

Citations
├─ Title: Where it came from
├─ Quote: Exact text supporting answer
└─ Score: 85% (relevance percentage)

Grounding Notes
└─ Why the AI has this confidence level
```

---

## Configuration Examples

### Quick Test (2-3 minutes)
```
Seed URL: https://example.com
Domains: example.com
Max Pages: 5
Max Depth: 1
```

### Standard (5-10 minutes)
```
Seed URL: https://docs.example.com
Domains: docs.example.com, example.com
Max Pages: 20
Max Depth: 2
```

### Comprehensive (10-30 minutes)
```
Seed URLs: 
  - https://docs.example.com
  - https://api.example.com
Domains: docs.example.com, api.example.com, example.com
Max Pages: 100
Max Depth: 3
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Health Offline" | Server down | Restart server: `uvicorn src.main:app --port 8001` |
| "Job not found" | Wrong Job ID | Copy exact ID from ingest result (no spaces) |
| "Ingestion failed" | Bad URL or domain | Check seed URL is valid (starts with http/https) |
| "No citations" | Low confidence | Ingest more pages, rephrase question |
| "Wrong answer" | Insufficient content | Increase Max Pages, check domain allowlist |

---

## Key Concepts

**Seed URL** = Starting page for crawling
**Domain Allowlist** = Which websites are allowed to crawl
**Max Pages** = How many pages to index (more = better coverage)
**Max Depth** = How many link-hops to follow (0 = only seed URL)
**Job ID** = Unique identifier to track ingestion
**Confidence** = How much the AI trusts its answer
**Citations** = Links to sources proving the answer

---

## Best Practices

- Start with **small crawls** (5-10 pages) to test
- Use **specific seed URLs** (not just domain root)
- **Keep domain allowlist focused** (don't add unrelated domains)
- **Save Job IDs** in a notepad for later reference
- **Verify important answers** by clicking citations
- **Trust HIGH confidence** answers, question MEDIUM/LOW
- **Ask clear, specific questions** (not vague ones)

---

## Example: Real Usage

### You have: Stripe API Documentation
```
STEP 1: Ingest
  Seed: https://stripe.com/docs/api
  Domain: stripe.com, docs.stripe.com
  Pages: 30
  Depth: 2
  → Job ID: abc123xyz

STEP 2: Wait
  Check Status → DONE

STEP 3: Ask
  Q: "How do I create a payment intent?"
  A: Detailed answer with 4 citations, HIGH confidence
  
  Q: "What's your favorite color?"
  A: REFUSED - "This information is not in the documentation"
```

---

## 🌐 Access Points

| Endpoint | Purpose |
|----------|---------|
| `http://127.0.0.1:8001/` | **This UI (use this!)** |
| `http://127.0.0.1:8001/docs` | API documentation (for developers) |
| `http://127.0.0.1:8001/health` | Server health check |

---

## Security Notes

- Your indexed content stays **local** (on your computer)
- OpenAI API key goes in `.env` file (never in code)
- Never share your API key
- Domain allowlist prevents crawling unauthorized sites
- No data is stored permanently after restart

---

## Pro Tips

1. **Organize by Job ID** - Create a spreadsheet tracking what each job indexed
2. **Start narrow** - Test with 5 pages, expand if needed
3. **Use multiple jobs** - One for docs, one for blog, one for FAQ
4. **Combine domains** - Add related domains to single job for better context
5. **Monitor citations** - Low scores = weak evidence, ignore those answers

---

## When to Use

Use NEXTRACION for:
- Product documentation chatbots
- Company knowledge bases
- FAQ automation
- Research data extraction
- Training material indexing

Don't use for:
- Real-time data (stock prices, weather)
- Websites you don't have permission to crawl
- Data requiring absolute accuracy without verification
- Personal information extraction

---

NEXTRACION – Nextraction 2 | v2.0
