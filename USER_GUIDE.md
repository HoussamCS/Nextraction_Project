# NEXTRACION User Guide

## Solution Overview

NEXTRACION is a Web-based Retrieval-Augmented Generation (RAG) Pipeline that crawls websites, indexes the content, and answers questions with evidence-based responses backed by citations.

### The Problem

Standard AI models hallucinate - they make up plausible-sounding answers that aren't grounded in reality. This system fixes that by:

1. Crawling websites to get actual content
2. Indexing that content in a vector database
3. Grounding all answers in the indexed material
4. Providing citations showing exactly where answers came from
5. Refusing to answer when evidence is insufficient

### Who's This For

- Companies building chatbots from their documentation
- Teams needing evidence-based information extraction
- Researchers requiring grounded responses
- Support teams automating knowledge bases

---

## Quick Start Workflow

### Access the UI
Run the application

You'll see two main sections:
- Left side: "Ingest Content" - crawls and indexes websites
- Right side: "Ask Question" - queries the indexed content

---

## Detailed Usage Guide

### Phase 1: Ingest Content (Left Panel)

#### 1. Add Seed URLs

A seed URL is where the crawler starts. It follows links from there based on your configuration.

Steps:
1. Enter a URL: `https://example.com/documentation`
2. Click "Add" button
3. Add multiple URLs if needed
4. See them listed below

Examples:
- `https://docs.stripe.com/`
- `https://support.github.com/`
- `https://blog.openai.com/`

#### 2. Configure Domain Allowlist

This defines which domains the crawler is allowed to visit. It keeps crawling focused and prevents following links to external sites.

How to use:
1. Enter domain names (comma-separated)
2. Don't include `https://` - just the domain
3. Be specific to avoid crawling unrelated content

Examples:
```
example.com
docs.example.com, api.example.com, blog.example.com
```

#### 3. Set Crawling Limits

Max Pages (1-500, default 10):
- Number of pages to index
- More pages = more coverage but slower crawling
- Start with 10-20 for testing

Max Depth (0-5, default 2):
- How many link-hops from seed URL
- 0 = only seed URL itself
- 2 = seed URL + its links + those pages' links
- 2-3 is usually balanced

#### 4. Add Notes (Optional)

Metadata about what you're indexing. Helps you remember later.

#### 5. Click "Start Ingestion"

The crawler will:
1. Validate your config
2. Fetch pages from seed URLs
3. Extract and clean text
4. Split into chunks
5. Generate embeddings via OpenAI
6. Store in vector database

You'll get a Job ID - save this for later.

---

### **Phase 2: Monitor Progress**

While ingestion is running, you can check its status.

#### Check Status (Right Panel)

1. Paste the **Job ID** from Phase 1 into the "Job ID" field
2. Click **"Check Status"** button

**You'll see:**
```
Job Status: RUNNING
Pages Fetched: 3
Pages Indexed: 2
```

**Job States:**
- 🟡 **QUEUED** – Waiting to start
- 🟠 **RUNNING** – Currently crawling and indexing
- 🟢 **DONE** – Complete, ready for questions
- 🔴 **FAILED** – Error occurred

**Keep checking until status shows "DONE"**

---

### **Phase 3: Ask Questions (Right Panel)**

Once ingestion is complete, you can ask questions about the indexed content.

#### 1. Enter the Job ID

Paste the same Job ID from Phase 1.

#### 2. Type Your Question

Ask anything about the content you indexed:
```
"What is the pricing model?"
"How do I integrate with Stripe?"
"What are the system requirements?"
"Explain authentication methods"
```

#### 3. Click "Get Answer"

NEXTRACION will:
1. Search the vector database for relevant content
2. Generate an answer grounded in that content
3. Extract citations showing sources
4. Estimate confidence based on evidence quality

#### 4. Review the Response

You'll see:

**Confidence Badge** (color-coded)
- 🟢 **HIGH** – Strong evidence, multiple sources
- 🟡 **MEDIUM** – Adequate evidence, some uncertainty
- 🔴 **LOW** – Weak evidence, should be verified

**The Answer**
- Grounded only in indexed content
- Will refuse to guess if evidence is insufficient

**Citations** (Click to view sources)
- URL: Where the information came from
- Title: Page title
- Quote: The exact text supporting the answer
- Score: Similarity percentage (higher = more relevant)

**Grounding Notes**
- Explanation of why confidence is at that level
- Details about evidence quality and quantity

---

## 💡 Example: Complete Workflow

### Scenario: Index OpenAI Documentation

#### Step 1: Ingest
```
Seed URL: https://platform.openai.com/docs
Domain Allowlist: platform.openai.com, openai.com
Max Pages: 25
Max Depth: 3
Click: Start Ingestion
→ Job ID: job_xyz789
```

#### Step 2: Monitor
```
Check Status with Job ID: job_xyz789
→ Status: RUNNING (Pages Fetched: 12, Pages Indexed: 10)
→ Status: RUNNING (Pages Fetched: 20, Pages Indexed: 18)
→ Status: DONE (Pages Fetched: 25, Pages Indexed: 24)
```

#### Step 3: Ask Questions
```
Question 1: "What models are available?"
→ Answer: Details with 3 citations, HIGH confidence

Question 2: "How much does GPT-4 cost?"
→ Answer: Pricing with citations, HIGH confidence

Question 3: "Can I use this for time travel?"
→ Refusal: "I cannot find evidence for this capability"
```

---

## ⚙️ Configuration Recommendations

### For General Documentation
```
Max Pages: 20-50
Max Depth: 2-3
Why: Balances coverage with crawling speed
```

### For Large Knowledge Bases
```
Max Pages: 100-200
Max Depth: 3-4
Why: More comprehensive indexing
Time: May take several minutes
```

### For Quick Testing
```
Max Pages: 5-10
Max Depth: 1-2
Why: Fast iteration for testing
Time: Usually < 1 minute
```

### For Specific Sections
```
Max Pages: 10-20
Max Depth: 1
Seed URL: Direct link to specific section
Why: Focused, high-quality results
```

---

## 🛡️ Data Privacy & Security

### Your Data
- All indexed content stays local (on your machine)
- Content is stored in a local vector database
- No data is sent to external servers (except OpenAI for embeddings)

### API Keys
- Never share your OpenAI API key
- Store it in `.env` file, never in code
- The UI doesn't display your key
- Revoke old keys if they're compromised

### Allowed Domains
- Use this to prevent crawling sensitive sites
- Always include only domains you own or have permission to crawl

---

## 🔍 Understanding Confidence Levels

### HIGH Confidence ✅
- Multiple relevant sources found
- High similarity scores (0.8+)
- Clear, unambiguous evidence
- **Trust this answer**

### MEDIUM Confidence ⚠️
- Some relevant sources found
- Medium similarity scores (0.6-0.8)
- Partial evidence, some interpretation
- **Verify if critical**

### LOW Confidence ❌
- Few relevant sources
- Low similarity scores (<0.6)
- Weak or contradictory evidence
- **Don't rely on this answer**

---

## 🐛 Troubleshooting

### "Health Status: Offline"
**Problem:** API isn't responding
**Solution:** 
1. Restart the server: `uvicorn src.main:app --port 8001`
2. Check if port 8001 is already in use
3. Try port 8000 instead

### "Job ID not found"
**Problem:** Status check fails
**Solution:**
1. Copy-paste Job ID exactly (no spaces)
2. Check that ingestion was actually started
3. Wait a few seconds for job to be created

### "Error during ingestion"
**Problem:** Crawling failed
**Solution:**
1. Check that seed URLs are valid (start with http/https)
2. Verify domain allowlist includes the seed URL's domain
3. Check internet connection
4. Try with fewer max pages

### "Answer is too generic"
**Problem:** Response doesn't match your question
**Solution:**
1. Check confidence level – may be too low
2. Rephrase question more specifically
3. Ingest more pages (increase Max Pages)
4. Ensure domain allowlist includes all relevant domains

### "No citations appearing"
**Problem:** Answer has no sources
**Solution:**
1. This means confidence is very low
2. Try ingesting more content
3. Check that indexed pages contain relevant information
4. Verify OpenAI API key is valid

---

## 📊 How It Works (Technical Overview)

### The RAG Pipeline

```
1. CRAWLING
   Seed URLs → Follow links → Fetch HTML
   ↓
2. CLEANING
   Remove boilerplate → Extract text → Split into chunks
   ↓
3. EMBEDDING
   Convert text → OpenAI embeddings → Create vectors
   ↓
4. INDEXING
   Store vectors → Create searchable database (Chroma)
   ↓
5. RETRIEVAL
   User question → Convert to embedding → Find similar chunks
   ↓
6. GENERATION
   Similar chunks → Feed to LLM → Generate grounded answer
   ↓
7. CITATION
   Trace back to source → Extract quotes → Create citations
```

### Anti-Hallucination Features

- ❌ No making up information
- ✅ Answers must cite indexed content
- ✅ Refusal when evidence insufficient
- ✅ Confidence scoring based on evidence quality
- ✅ Grounding notes explaining source quality

---

## 🚀 Advanced Tips

### 1. Multiple Ingestion Jobs
You can run multiple ingestion jobs with different domains:
- Job 1: Your API docs
- Job 2: Your blog posts
- Job 3: Your help center

Each has its own Job ID for separate queries.

### 2. Iterative Refinement
Start small, then expand:
1. Test with 5 pages
2. Review answer quality
3. Gradually increase Max Pages
4. Adjust domain allowlist based on results

### 3. Combining Domains
Index multiple related domains in one job:
```
Seed URLs:
- https://docs.example.com
- https://api.example.com

Allowed Domains:
docs.example.com, api.example.com, example.com
```

### 4. Monitoring Performance
- **High answer quality** = Good domain focus, sufficient pages
- **Low confidence** = Need more pages or relevant content
- **Wrong answers** = Domain allowlist too broad

---

## 📱 Using the Dashboard

### Header
- Shows API health status (green = good)
- Confirms server location

### Ingest Panel
- Left side for content ingestion
- Stores Job IDs for reference
- Shows ingestion status

### Ask Panel
- Right side for querying
- Paste Job ID from ingest
- See answers with evidence

### Mobile Responsive
The UI works on phones/tablets:
- Single-column layout
- Touch-friendly buttons
- Readable on smaller screens

---

## ✨ Best Practices

### ✅ DO:
- Start with small test crawls
- Use specific, focused seed URLs
- Include all relevant domains in allowlist
- Save Job IDs for future reference
- Ask specific, clear questions
- Check confidence levels before trusting answers
- Verify important answers with source documents

### ❌ DON'T:
- Crawl sites you don't own or have permission for
- Use overly broad domain allowlists
- Ingest millions of pages (system limitations)
- Trust LOW confidence answers for critical decisions
- Share your OpenAI API key
- Expect answers outside your indexed content

---

## 📧 Support

If you encounter issues:

1. Check the `/docs` endpoint for API documentation
2. Monitor the server console for error messages
3. Review the `.env` file for configuration issues
4. Ensure OpenAI API key is valid and has credits
5. Check that your internet connection is stable

---

## 🎓 Learning Resources

- **RAG Explained:** https://en.wikipedia.org/wiki/Retrieval-augmented_generation
- **OpenAI Embeddings:** https://platform.openai.com/docs/guides/embeddings
- **Vector Databases:** https://www.pinecone.io/learn/vector-database/
- **Prompt Engineering:** https://platform.openai.com/docs/guides/prompt-engineering

---

## Summary

**NEXTRACION is your tool for creating intelligent, evidence-based chatbots.**

1. **Ingest** → Crawl websites and index content
2. **Monitor** → Track progress with Job IDs
3. **Query** → Ask questions and get grounded answers
4. **Trust** → Verify with citations and confidence scores

**Start with the Quick Start Workflow above and explore!**

---

*Version 2.0 | NEXTRACION – Nextraction 2*
*Web-based Retrieval-Augmented Generation for Evidence-First Insights*
