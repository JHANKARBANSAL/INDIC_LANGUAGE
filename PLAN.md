# IndicSQL --- Agentic AI Project Plan

> **IndicSQL: Autonomous Multi-Agent Cross-Lingual Text-to-SQL & Semantic Schema-Linking Swarm for Indian Languages**
>
> A Research-grade and Production-ready LangGraph multi-agent architecture specifically engineered to solve the April 2026 **IndicDB Benchmark** gap. Combining phonetics-aware cross-lingual schema-linking, an open Indic transformer (Sarvam-2B / Qwen-2.5-Coder) fine-tuned on aggregation/GROUP BY reasoning, an in-memory execution sandbox (DuckDB/PostgreSQL), and a dialect-native response verbalizer, IndicSQL bridges the 9% Indic-to-English accuracy deficit and democratizes access to Indian Open Government Data (NDAP) for 1.4 billion citizens across 7 languages (Hindi, Bengali, Tamil, Telugu, Marathi, Hinglish, English).

------------------------------------------------------------------------

## 1. Project Overview

**IndicSQL** is an autonomous multi-agent cross-lingual Text-to-SQL system designed to translate complex natural language questions posed in Indian vernacular languages (and code-mixed Hinglish) into deterministic, highly optimized SQL queries executed against real-world relational databases.

The project directly targets the empirical findings of the landmark **IndicDB Benchmark (April 2026)**. The IndicDB paper evaluated state-of-the-art language models on **15,617 questions across 20 real-world Indian Government databases (National Data and Analytics Platform - NDAP)** and revealed a devastating **9% average accuracy degradation** when queries are framed in Indian languages compared to English.

### The IndicDB Diagnostic Findings:
- **Language Penalty:** Telugu suffered the steepest penalty (**-11.0%**), Tamil (**-9.8%**), Bengali (**-9.2%**), Hindi (**-8.4%**), Marathi (**-8.1%**), and Hinglish (**-6.87%**).
- **The Two Root Causes of Failure:**
  1. **20% Schema-Linking Breakdown:** Models fail to map vernacular or transliterated tokens (e.g., *"vidyarthi"*, *"kisano"*, *"shala"*) to English database columns (e.g., `student_enrolled_count`, `farmer_beneficiaries`, `school_id`).
  2. **28% Aggregation & GROUP BY Breakdown:** Models collapse on complex relational reasoning (multi-tier filtering, regional groupings, conditional counting, temporal windows) when prompt semantics are formulated in non-English syntactic structures.

### The Research & Product Opportunity:
The IndicDB paper explicitly diagnosed these failure modes but offered **no technical solution or mitigation**, leaving it as open future work. In the months since publication, no follow-up work has systematically addressed this benchmark. **IndicSQL is the first dedicated solution framework** to eliminate this gap by engineering two specialized architectural innovations:
1. **Cross-Lingual Phonetic & Semantic Schema-Linking Agent:** A hybrid module fusing Indic transliteration normalization (IndicXlit / Roman-to-Devanagari/Dravidian phonetics) with dense cross-lingual representations (mE5-large / BGE-M3) and database catalog graphs to eliminate the 20% schema-linking deficit.
2. **Aggregation-Specialized LoRA Transformer:** An open Indic-aligned model (`Sarvam-2B` or `Qwen-2.5-Coder-7B`) fine-tuned specifically on hard multi-table aggregation, sub-queries, and GROUP BY patterns derived from NDAP datasets to eliminate the 28% relational reasoning deficit.

------------------------------------------------------------------------

## 2. Project Motivation: "Asli Problem & The Untapped Gap"

### The Real Problem for 1.4 Billion Citizens
The Government of India hosts petabytes of public welfare, agricultural, healthcare, educational, and demographic datasets on platforms like **NDAP (National Data and Analytics Platform)** and **data.gov.in**. However:
- **Language Barrier:** Over **85% of Indian citizens** and local administrative field workers are not comfortable formulating analytical questions in English.
- **English Schema Monopoly:** All government database schemas, table definitions, and column headers are written exclusively in English (e.g., `dist_code`, `total_mandays_generated`, `scheme_disbursed_amt_inr`).
- **Code-Mixing & Transliteration Realities:** A user in Bihar or Maharashtra rarely types pure Sanskritized Hindi or formal Marathi; they type code-mixed Hinglish/Devanagari on mobile keyboards:
  > *"Maharashtra mein pichle saal kitne kisano ne PM-Kisan yojana ka fayda liya aur total kitna paisa disburse hua?"*

```
Current State-of-the-Art (Generic ChatGPT / GPT-4o / Llama-3):
[Indic Question] ──> [English-Centric LLM] ──> [Schema Hallucination!]
  • Fails to link "kisano" to `farmer_beneficiary_cnt` (Column Miss: 20% error)
  • Fails on temporal filter "pichle saal" + GROUP BY `district_name` (28% error)
  • Output: Invalid SQL or Empty Recordset (Result: Citizen excluded from public data)

IndicSQL Multi-Agent Solution:
[Indic / Hinglish / Regional Query] 
  ──> [Query Normalizer & Script Detector] 
  ──> [Cross-Lingual Schema-Linking Agent (mE5 + Phonetic Graph)] 
  ──> [Aggregation SQL Synthesizer (Fine-Tuned Sarvam/Qwen LoRA)] 
  ──> [In-Memory DuckDB Sandbox Execution & Reflection Loop] 
  ──> [Native Language Verbalizer Agent] 
  ──> [Citizen receives accurate answer + chart in their mother tongue in < 2 seconds]
```

### The Novelty & Academic Advantage:
1. **First Solution to IndicDB Benchmark:** Direct empirical evaluation against published IndicDB numbers across all 7 languages.
2. **Targeted Surgical Fixes:** Explicitly resolves the two quantified error modes (20% schema-linking + 28% aggregation) rather than blindly scaling model parameter size.
3. **Open-Source & Deployable:** Operates using accessible 2B–7B open-source models capable of on-premises edge execution in government departments without recurring token costs.

------------------------------------------------------------------------

## 3. Project Goals

### Primary Goal
Build and benchmark **IndicSQL**, an autonomous multi-agent cross-lingual Text-to-SQL architecture that eliminates the **9% Indic language performance deficit** on the April 2026 IndicDB benchmark, achieving parity with (or surpassing) English Text-to-SQL execution accuracy across all 7 evaluated languages.

### Secondary Goals
- **Schema-Linking Precision:** Achieve $\ge 92\%$ recall and precision on cross-lingual column/table alignment across English, Hindi, Bengali, Tamil, Telugu, Marathi, and Hinglish.
- **Aggregation Execution Accuracy:** Improve Execution Accuracy (EX) on IndicDB's hard aggregation and GROUP BY subset by at least **+15 percentage points** over baseline open models.
- **Sub-2-Second Turnaround:** Execute complete query normalization, schema linking, SQL synthesis, database query, and verbalization in under $2.0$ seconds on consumer GPU / edge CPU hardware.
- **Self-Healing SQL Execution Loop:** Intercept database syntax, column-not-found, and empty-result errors in an ephemeral DuckDB sandbox, self-repairing queries via compiler reflection before displaying output.
- **Bilingual & Multimodal Visual Cockpit:** Deliver an accessible Next.js web application supporting Devanagari, Dravidian, and Latin scripts, voice input (via Whisper / Bhashini), interactive data tables, and automated chart generation (Vega-Lite / Chart.js).

------------------------------------------------------------------------

## 4. Scope

### 4.1 In Scope
- **Languages (7 Target IndicDB Languages):**
  1. Hindi (`hi`)
  2. Bengali (`bn`)
  3. Tamil (`ta`)
  4. Telugu (`te`)
  5. Marathi (`mr`)
  6. Hinglish (`hi-en` Latin transliteration)
  7. English (`en` - baseline control)
- **Data Domains (NDAP Indian Government Datasets):**
  - Agriculture (PM-KISAN, crop yield, mandi market prices, fertiliser usage).
  - Education (UDISE+ school enrollment, teacher-pupil ratios, literacy rates).
  - Healthcare & Demographics (NFHS-5, maternal mortality, rural clinic infrastructure).
  - Rural Development (MGNREGA wage employment, rural road connectivity).
- **SQL Dialects:** PostgreSQL, DuckDB, and SQLite.
- **Multi-Agent Orchestration:** LangGraph state machine with cyclic reflection, dynamic tool invocation, and deterministic database execution.
- **Specialized Dual-Model Pipeline (Default Champion):** Division of labor pairing `Sarvam-2B` for sovereign Indic contextual transliteration, dialectal normalization, and semantic entity disambiguation with `Qwen-2.5-Coder-7B-Instruct` (LoRA) for high-precision Text-to-SQL code generation.
- **Tri-Combo Architectural Matrix:** Comparative benchmarking of the default hybrid against two ablation configurations (Pure `Sarvam-2B` monolithic pipeline and Pure `Qwen-2.5-Coder` monolithic pipeline).
- **Citizen Cockpit UI & Model Arena:** Live query input, voice mic, execution plan visualizer, SQL preview, bilingual summary, and a secondary Model Arena drawer for creative qualitative/quantitative comparison and dynamic engine selection.

### 4.2 Out of Scope
- Destructive database mutations (`INSERT`, `UPDATE`, `DELETE`, `DROP TABLE` are strictly prevented via read-only transaction wrappers).
- Natural language queries in unwritten oral tribal dialects without standardized Unicode scripts.
- Processing unstructured OCR of blurry, handwritten paper land records (queries must be submitted as text or transcribed speech).

------------------------------------------------------------------------

## 5. Core Agent Architecture

IndicSQL structures its intelligence into 6 specialized agents coordinated by a Master Orchestrator, executing within a unified LangGraph state machine:

| Agent Name | Architectural Responsibility | Core Technologies & Concepts |
| :--- | :--- | :--- |
| **Orchestrator / Context Normalizer** | Analyzes input query, detects script/language, normalizes dialectal nuances, and performs contextual transliteration. | `Sarvam-2B` Sovereign Model, FastText, LangGraph StateGraph |
| **Cross-Lingual Schema-Linking Agent** | Maps vernacular query tokens (nouns, verbs, metrics) to exact English database tables, columns, foreign keys, and enumerated values. | mE5-Large / BGE-M3 Embeddings, IndicXlit Phonetic Transliteration, BM25 Index |
| **SQL Synthesizer Agent** | Generates dialect-compliant, mathematically sound SQL with accurate JOINs, WHERE clauses, and aggregation groupings. | Fine-Tuned `Qwen-2.5-Coder-7B` (LoRA), Few-Shot CoT Prompting |
| **Sandbox Execution & Reflection Agent**| Executes candidate SQL inside an in-memory DuckDB sandbox; parses runtime errors (syntax, zero rows, typing) and formulates reflection feedback. | In-Memory DuckDB Engine, SQLGlot AST Parser, Compiler Reflection Loop |
| **Response Verbalizer Agent** | Takes raw SQL execution tabular output and articulates a concise, natural language answer in the user's original language. | Multilingual NLG, Number & Currency Localization (e.g., Lakhs/Crores), Markdown Table Gen |
| **SQL Verification Critic Node** | Validates SQL against deterministic security and correctness rules (no mutations, execution equivalence, constraint satisfaction). | Static AST Analysis, Read-Only Enforcement, Hallucination Verification |
| **Model Arena & Engine Switcher** | Runtime engine dispatcher supporting dynamic toggling between Combo A (Hybrid), Combo B (Sarvam Pure), and Combo C (Qwen Pure). | LangGraph Conditional Node Router, Engine Configuration State |

------------------------------------------------------------------------

## 6. System Architecture

```mermaid
flowchart TB
    subgraph User_Interface_Layer["1. Citizen and Field Interface - BharatQuery Flutter Mobile Cockpit"]
        USER["Citizen / Local Sarpanch / Student / Field Worker"]
        MIC["Microphone - Audio-Reactive Spherical Blob"]
        KB["Text / Chat Input - Vernacular Scripts and Hinglish"]
        ARENA["Model Arena Drawer - Secondary\n• Tri-Combo Benchmark: EX%, Latency, AST\n• Qualitative Phrasing and SQL Inspect\n• Runtime Engine Dictation Toggle"]
        
        USER --> MIC
        USER --> KB
        USER -.->|Inspect / Dictate Engine| ARENA
        
        MIC --> ELEVEN_VOICE["ElevenLabs Conversational AI - Voice Agent and Scribe STT"]
        ELEVEN_VOICE --> AUDIO_CACHE{"Local Audio and Query Cache - Zero-Credit Hit?"}
        AUDIO_CACHE -->|Cache Hit - 0 Credits| MOBILE_PLAY["Instant Native Playback - under 100ms"]
        AUDIO_CACHE -->|Cache Miss| INPUT_BUS["Normalized Input Query"]
        KB --> INPUT_BUS
    end

    subgraph Multi_Agent_Swarm["2. IndicSQL Multi-Agent Core - LangGraph"]
        direction TB
        SUP["Query Supervisor and Context Normalizer\nPowered by Sarvam-2B Sovereign Model"]
        
        SLA["Cross-Lingual Schema-Linker Agent\nPhonetic Transliteration + mE5 Embeddings"]
        SSA["Aggregation SQL Synthesizer Agent\nPowered by Qwen-2.5-Coder LoRA"]
        SRA["Sandbox Execution and Reflection Agent\nIn-Memory DuckDB Sandbox"]
        RVA["Response Verbalizer Agent\nVernacular NLG + Lakhs/Crores Formatter"]
        CRITIC["Security and Semantic Critic Node\nAST Validator and Mutation Blocker"]
        
        STATE[("LangGraph IndicSQLState - Checkpoint Store")]
        
        SUP --- SLA
        SUP --- SSA
        SUP --- SRA
        SUP --- RVA
        SUP --- CRITIC
        SUP --- STATE
    end

    subgraph Schema_and_Knowledge["3. Cross-Lingual Knowledge and Catalog Substrate"]
        direction TB
        CATALOG[("NDAP English Database Catalogs - DDL and Keys")]
        VEC_STORE[("Qdrant Vector DB - Schema Embeddings")]
        PHONETIC[("IndicXlit Phonetic Soundex Table")]
        SAMPLE_VALS[("Enumerated Value Index - Categorical Strings")]
        
        SLA -.-> CATALOG
        SLA -.-> VEC_STORE
        SLA -.-> PHONETIC
        SLA -.-> SAMPLE_VALS
    end

    subgraph Database_Execution["4. Sandboxed Relational Execution Engine"]
        direction TB
        DUCKDB[("DuckDB In-Memory Execution Sandbox")]
        POSTGRES[("Production PostgreSQL NDAP Replicas")]
        SQLGLOT["SQLGlot AST Transpiler and Formatter"]
        
        SRA --> SQLGLOT
        SQLGLOT --> DUCKDB
        SQLGLOT --> POSTGRES
    end

    subgraph Output_Presentation["5. Dual-Output Presentation and Analytics"]
        direction TB
        NAT_LANG["Natural Language Answer - Original Mother Tongue"]
        DATA_TABLE["Interactive Filterable Data Table"]
        CHARTS["Auto-Generated Visualizations - Bar/Line Charts"]
        SQL_PREVIEW["Copyable Executable SQL Query - Dev Mode"]
    end

    INPUT_BUS --> SUP
    ARENA -.->|Dictate Combo A/B/C| SUP
    RVA --> NAT_LANG
    SRA --> DATA_TABLE
    SRA --> CHARTS
    SSA --> SQL_PREVIEW
```

------------------------------------------------------------------------

## 7. Why This Is Agentic

IndicSQL is distinctly an **agentic system**, moving far beyond naive single-prompt LLM wrappers:

| Characteristic | IndicSQL Multi-Agent Interpretation |
| :--- | :--- |
| **Observability** | **Partially Observable:** The system receives a colloquial vernacular question without schema qualifiers; it does not know which of the 20 NDAP databases, which tables, or which specific English columns contain the answers until it actively inspects database metadata. |
| **Determinism** | **Hybrid Stochastic & Deterministic:** Language translation and query parsing are probabilistic, but SQL execution against relational tables is 100% mathematically deterministic. The system uses deterministic compiler execution to rein in probabilistic hallucinations. |
| **Time Structure** | **Sequential & Multi-Turn:** Schema linking must prune irrelevant tables before SQL generation; execution results dictate whether a reflection loop or final verbalization runs. |
| **Dynamic Environment** | **Schema Drift & Data Cardinality:** Government datasets update periodically, column names have idiosyncratic abbreviations (`tot_f_pop_2021`), and user terminology varies across dialects and phonetic spellings. |
| **Self-Healing Autonomy** | If generated SQL crashes on a `GROUP BY` clause or produces a type mismatch (`operator does not exist: text = integer`), the system autonomously intercepts the runtime error, diagnoses the bug, and corrects its own SQL without bothering the citizen. |

------------------------------------------------------------------------

## 8. PEAS Specification

The formal agent problem definition for IndicSQL:

| Component | IndicSQL Formal Definition |
| :--- | :--- |
| **Performance Measure (P)** | - **Execution Accuracy (EX):** Percentage of generated SQL queries that produce the exact same ground-truth result table as the gold SQL on IndicDB ($>82\%$).<br>- **Indic-English Gap Delta:** Reduction of the baseline 9% gap to $< 2\%$.<br>- **Schema-Linking Recall:** $>95\%$ coverage of gold tables and columns.<br>- **Valid Efficiency Score (VES):** Syntactically valid SQL executed within $< 150\text{ms}$ database execution budget.<br>- **Zero-Hallucination Rate:** 100% of reported numbers in the natural language summary directly match the database execution table. |
| **Environment (E)** | - 20 Indian Government NDAP Relational Databases (PostgreSQL / DuckDB).<br>- Complex schema topologies: Multi-table relational joins, composite keys, foreign keys, temporal time series.<br>- Multilingual queries across 7 Indian languages with varying Unicode scripts and Latin transliteration. |
| **Actuators (A)** | - FastText language identifier and transliteration normalizer.<br>- Cross-lingual dense & sparse schema retriever.<br>- Fine-tuned SQL synthesizer model.<br>- In-memory DuckDB sandbox query executor.<br>- SQLGlot AST parser and query modifier.<br>- Vernacular NLG verbalizer engine. |
| **Sensors / Percepts (S)** | - User text input or speech audio transcript.<br>- NDAP database catalog metadata (DDL, primary/foreign keys, column constraints).<br>- Distinct column values and categorical string lookups.<br>- SQL execution stdout, stderr, execution time, and returned tabular data tuples. |

------------------------------------------------------------------------

## 9. Agent Communication Architecture

IndicSQL implements four explicit communication patterns to coordinate its specialized swarm:

### 9.1 Sequential Communication (Core Pipeline)
Used for the linear dataflow where each node's output forms the prerequisite context for the next agent:

```mermaid
flowchart LR
    A["Query Supervisor"] -->|Language & Canonical Query| B["Schema-Linker Agent"]
    B -->|Pruned Schema & Mapped Columns| C["SQL Synthesizer"]
    C -->|Candidate SQL Query| D["Sandbox Execution"]
    D -->|Execution Tuple Results| E["Response Verbalizer"]
```

### 9.2 Parallel / Broadcast Communication (Multi-Catalog Search)
When the user query is broad and could span multiple NDAP databases (e.g., comparing *crop output* with *irrigation schemes*):

```mermaid
flowchart TD
    SUP["Query Supervisor"] -->|Broadcast Query| S1["Scan Agriculture Catalog (PM-KISAN)"]
    SUP -->|Broadcast Query| S2["Scan Water Resources Catalog (Irrigation)"]
    SUP -->|Broadcast Query| S3["Scan Weather & Rainfall Catalog (IMD)"]
    
    S1 --> AGG["Schema Union & Relevance Ranker"]
    S2 --> AGG
    S3 --> AGG
    AGG -->|Consolidated Sub-Schema| SYNTH["SQL Synthesizer Agent"]
```

### 9.3 Blackboard / Shared State Pattern
All agents read and mutate a unified, immutable, versioned **LangGraph State** (`IndicSQLState`):

```mermaid
flowchart TB
    subgraph Blackboard_State["LangGraph IndicSQLState"]
        S1["raw_query and detected_language"]
        S2["canonical_query (Normalized Transliteration)"]
        S3["linked_tables and linked_columns"]
        S4["generated_sql"]
        S5["execution_result (TabularData)"]
        S6["execution_error and reflection_attempts"]
        S7["verbalized_response (Native Indic Language)"]
    end

    Supervisor["Query Supervisor"] -->|Writes| S1
    Supervisor -->|Writes| S2
    SchemaLinker["Schema-Linker"] -->|Reads S2, Writes| S3
    Synthesizer["SQL Synthesizer"] -->|Reads S3, Writes| S4
    Sandbox["Sandbox Executor"] -->|Reads S4, Writes| S5
    Sandbox -->|Writes| S6
    Verbalizer["Response Verbalizer"] -->|Reads S5, Writes| S7
```

### 9.4 Hierarchical Communication (Supervisor Pattern)
The Supervisor dynamically arbitrates whether a failed execution triggers a self-healing reflection cycle or escalates to fallback simplifications:

```mermaid
flowchart TD
    SUP["Query Supervisor"]
    
    SUP -->|1. Parse and Link| SL["Schema Linker"]
    SL -->|Linked Elements| SUP
    
    SUP -->|2. Synthesize SQL| SS["SQL Synthesizer"]
    SS -->|Draft SQL| SUP
    
    SUP -->|3. Test Run| SB["Sandbox Executor"]
    SB -->|Execution Error (Attempts under 3)| SUP
    SUP -->|4. Trigger Reflection Loop| SS
    SB -->|Execution Success| SUP
    
    SUP -->|5. Verbalize Output| RV["Response Verbalizer"]
    RV -->|Final Answer| SUP
```

------------------------------------------------------------------------

## 10. Workflow Architecture

### 10.1 End-to-End Autonomous Query-to-SQL-to-Vernacular Flow

```mermaid
flowchart TD
    A["User submits question in Hindi / Tamil / Telugu / Hinglish"] --> B["Script Detection & Transliteration Normalization\n(e.g., Converts Hinglish 'kisano' to standard Roman/Devanagari)"]
    B --> C["Cross-Lingual Schema-Linking Agent\n(Phonetic Matching + mE5 Cross-Lingual Embedding Retrieval)"]
    
    D{"Schema Linked Successfully?\n(Confidence >= 0.85)"}
    C --> D
    D -->|No| E["Interactive Clarification Request\n(Asks citizen in mother tongue to clarify ambiguous terms)"]
    D -->|Yes| F["Pruned Schema Injection + Few-Shot Prompt Construction"]
    
    F --> G["SQL Synthesizer Agent\n(LoRA Fine-Tuned Sarvam-2B / Qwen-2.5-Coder)"]
    G --> H["AST Security & Read-Only Check\n(Block mutations, inject LIMIT 1000)"]
    
    H --> I["Deploy DuckDB In-Memory Execution Sandbox\n(Execute SQL against loaded NDAP Parquet/Relational tables)"]
    
    I --> J{"Execution Status?"}
    
    J -->|Error or Empty Set (Attempts under 3)| K["Reflective Self-Correction Node\n(Feed DuckDB stderr / column-mismatch back to Synthesizer)"]
    K --> G
    
    J -->|Failed after 3 attempts| L["Graceful Fallback Explanation in Native Language"]
    
    J -->|Success: Non-Empty Tuple Set| M["Response Verbalizer Agent\n(Translates tabular aggregates into fluent native Indic prose)"]
    M --> N["Visualization Generator\n(Detects if data is suitable for Bar/Pie/Line Chart)"]
    
    N --> O["Deliver Integrated Presentation to BharatQuery Flutter Cockpit"]
```

### 10.2 Sequence Diagram: The Farmer PM-KISAN Query

```mermaid
sequenceDiagram
    autonumber
    actor User as Marathi Citizen / Farmer
    participant UI as BharatQuery Flutter UI
    participant Sup as Supervisor (Sarvam-2B Context)
    participant Linker as Schema-Linker Agent
    participant Synth as SQL Synthesizer (Qwen-Coder LoRA)
    participant Sand as DuckDB Execution Sandbox
    participant Verb as Response Verbalizer Agent

    User->>UI: "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?"
    UI->>Sup: Ingest Query (Language: mr, Marathi Script)
    Sup->>Linker: Extract entities and link to NDAP Agri DB
    Linker->>Linker: "शेतकऱ्यांना" maps to farmer_beneficiaries
    Linker->>Linker: "पीएम-किसान" maps to scheme_code = 'PM-KISAN'
    Linker->>Linker: "महाराष्ट्रात" maps to state_name = 'MAHARASHTRA'
    Linker->>Linker: "गेल्या वर्षी" maps to financial_year = '2024-25'
    Linker-->>Sup: Return Pruned Schema: ndap_pm_kisan_disbursement
    
    Sup->>Synth: Synthesize Aggregation SQL with Filter Constraints
    Synth-->>Sup: SELECT SUM(farmer_beneficiaries), SUM(amount_inr) FROM ndap_pm_kisan_disbursement...
    
    Sup->>Sand: Run candidate SQL in isolated DuckDB memory
    Sand-->>Sup: Output: total_farmers: 8,421,904, total_amount: 16843808000
    
    Sup->>Verb: Format result tuple into native Marathi prose + Lakhs/Crores
    Verb-->>UI: "महाराष्ट्रात २०२४-२५ मध्ये एकूण ८४.२१ लाख शेतकऱ्यांना पीएम-किसान योजनेचा लाभ मिळाला..."
    UI-->>User: Display Marathi Answer + Summary Metric Badges + Chart
```

------------------------------------------------------------------------

## 11. Cross-Lingual Schema-Linking Deep Dive: Solving the 20% Error

The primary vulnerability discovered by IndicDB was that **20% of all failures stemmed from schema-linking breakdown**. IndicSQL resolves this via a tripartite matching architecture:

```mermaid
flowchart TD
    Q_IND["Indic Query: 'vidyarthi sankhya' / 'विद्यार्थी संख्या' / 'மாணவர் எண்ணிக்கை'"]
    
    subgraph Path_1["1. Phonetic and Transliteration Normalization"]
        XLIT["IndicXlit / Romanizer"]
        STEM["Language Stemmer and Lemmatizer"]
        XLIT --> STEM
        STEM --> PHON_VEC["Phonetic Token: 'vidyarthi' to 'student'"]
    end

    subgraph Path_2["2. Dense Cross-Lingual Semantic Search"]
        ME5["mE5-Large / BGE-M3 Multilingual Embedding"]
        QDRANT[("Qdrant Vector DB: NDAP Schema Embeddings\nIndexed with multilingual synonyms and descriptions")]
        ME5 --> QDRANT
        QDRANT --> DENSE_MATCH["Top-K Candidate Columns (Cosine >= 0.82)"]
    end

    subgraph Path_3["3. Exact Categorical String Matcher"]
        VALUE_INDEX[("Inverted Index of Database Values\n(e.g., 'Maharashtra', 'Rabi', 'OBC')")]
        TRIE["Trie / Fuzzy Levenshtein Matcher"]
        VALUE_INDEX --> TRIE
        TRIE --> CAT_MATCH["Categorical Literal Matching"]
    end

    Q_IND --> XLIT
    Q_IND --> ME5
    Q_IND --> VALUE_INDEX

    PHON_VEC --> RERANK["Cross-Lingual Cross-Encoder Reranker"]
    DENSE_MATCH --> RERANK
    CAT_MATCH --> RERANK

    RERANK --> FINAL_SCHEMA["Pruned Target Schema:\nTable: udise_school_enrolment\nColumns: student_count, academic_year"]
```

### Mathematical Formulation of Schema Relevance Score:
For candidate column $c_j$ given query token $q_i$:
$$S(q_i, c_j) = w_1 \cdot \cos\big(E_{\text{mE5}}(q_i), E_{\text{mE5}}(c_j)\big) + w_2 \cdot \text{Levenshtein}\big(\text{Xlit}(q_i), \text{Name}(c_j)\big) + w_3 \cdot \mathbb{I}(q_i \in \text{Enum}(c_j))$$
Columns with $S(q_i, c_j) > \tau_{\text{threshold}}$ are preserved in the pruned schema prompt, discarding 95% of irrelevant tables and preventing context window dilution.

------------------------------------------------------------------------

## 12. Fine-Tuning Specification: Solving the 28% Aggregation Error

The second failure mode identified by IndicDB was that **28% of errors occurred on queries requiring complex aggregations, GROUP BY, and multi-condition joins**.

### Dual-Model Specialization Architecture:
To solve both linguistic decay and aggregation breakdown, IndicSQL employs a **cooperative dual-model pipeline**:
1. **Context & Transliteration Normalizer:** `sarvamai/sarvam-2b` (Fine-Tuned)
   - **Role:** Deep vernacular comprehension, dialectal normalization, and contextual transliteration. Converts raw Indic/Hinglish idioms into canonical semantic queries with entity boundaries.
   - **Tokenizer Advantage:** Native 64K Indic vocab captures Devanagari/Dravidian morphology with 3x-4x fewer tokens than generic LLMs.
2. **Precision SQL Synthesizer:** `Qwen/Qwen2.5-Coder-7B-Instruct` (Fine-Tuned LoRA)
   - **Role:** Translates canonical context and pruned NDAP DDLs into mathematically sound SQL queries with complex aggregations, subqueries, and window functions.
   - **Reasoning Advantage:** 7B code-specialized architecture delivers state-of-the-art AST validity and syntax compliance.

### LoRA Fine-Tuning Parameters:

| Hyperparameter | Sarvam-2B (Context Normalizer) | Qwen-2.5-Coder-7B (SQL Synthesizer) | Rationale |
| :--- | :--- | :--- | :--- |
| **Quantization** | 4-bit NormalFloat (NF4) | 4-bit NormalFloat (NF4) | Trainable on a single consumer RTX 4090 (24GB). |
| **LoRA Rank ($r$)** | `16` | `32` | Rank 16 suffices for linguistics; Rank 32 captures relational logic. |
| **LoRA Alpha ($\alpha$)**| `32` | `64` | Consistent $\alpha / r = 2.0$ scaling factor. |
| **Target Modules** | `q_proj`, `v_proj`, `k_proj`, `o_proj` | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` | Targeted linguistic adaptation vs full code-path adaptation. |
| **LoRA Dropout** | `0.05` | `0.05` | Prevents overfitting to training schemas. |
| **Sequence Length** | `2,048 tokens` | `4,096 tokens` | Fits input queries vs accommodating multi-table DDL schemas. |
| **Optimizer & LR** | `Paged AdamW 8-bit`, $2 \times 10^{-4}$ | `Paged AdamW 8-bit`, $1.5 \times 10^{-4}$ | Warmup cosine decay schedule. |

### Training Dataset Composition:
We build **IndicSQL-Agg-12K**, a curated dataset of 12,000 paired instances partition-tuned for both models:
- **Partition 1 (Context Normalization - for Sarvam-2B):** `(Raw Colloquial Query, Canonical Meaning, Explicit Entity/Filter Bounds)`.
- **Partition 2 (Aggregation SQL - for Qwen-2.5-Coder):** `(Canonical Meaning, Pruned NDAP DDL, Dialect-Specific Gold SQL)`. Focuses on:
  - Nested aggregations (`AVG(SUM(...))`, ratios, percentages).
  - Multi-dimensional groupings (`GROUP BY state, district, year`).
  - Conditional counts (`COUNT(CASE WHEN gender = 'F' THEN 1 END)`).
  - Relative temporal arithmetic (`DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR)`).
  - Uniform distribution across all 7 target languages.

### 12.1 Tri-Combo Architectural Matrix (Comparative Evaluation)

To rigorously evaluate the division of labor, IndicSQL defines a **Tri-Combo Comparative Matrix**:

| Architecture Combo | Transliteration & Context Engine | SQL Synthesizer Engine | Role & Hypothesis |
| :--- | :--- | :--- | :--- |
| **Combo A (Default Champion)** | **Fine-Tuned `Sarvam-2B`** | **Fine-Tuned `Qwen-2.5-Coder`** | **Target Production Architecture:** Optimal pairing of domestic sovereign language mastery with leading code synthesis. Highest EX% and lowest Indic gap. |
| **Combo B (Ablation 1 - Sovereign Pure)** | **Fine-Tuned `Sarvam-2B`** | **Fine-Tuned `Sarvam-2B`** | **Sovereign Monolith:** Tests end-to-end performance using 100% Indian foundation weights. Extremely lightweight (<3GB VRAM). |
| **Combo C (Ablation 2 - CodeLLM Pure)** | **Fine-Tuned `Qwen-2.5-Coder`** | **Fine-Tuned `Qwen-2.5-Coder`** | **Code-First Monolith:** Tests whether high-capacity code LLMs can perform cross-lingual reasoning natively without an Indic-first front-end. |

#### Comparative Telemetry Protocol:
All three configurations are evaluated against identical IndicDB test splits across 4 key dimensions:
1. **Execution Accuracy (EX%):** Result set equivalence against ground truth.
2. **Valid Efficiency Score (VES):** Execution latency inside DuckDB sandbox ($<150\text{ms}$).
3. **Indic-English Gap ($\Delta_{\text{Indic-EN}}$):** Parity retention across vernacular scripts.
4. **Token & Latency Efficiency:** Wall-clock inference time and GPU memory footprint.

------------------------------------------------------------------------

## 13. LangGraph Multi-Agent Implementation Strategy

### TypedDict State Definition:

```python
from typing import TypedDict, List, Dict, Optional, Any, Union
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


class SchemaElement(TypedDict):
    table_name: str
    column_name: str
    data_type: str
    indic_synonyms: List[str]
    is_foreign_key: bool
    foreign_target: Optional[str]


class TabularResult(TypedDict):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float


class IndicSQLState(TypedDict):
    query_id: str
    raw_query: str
    detected_lang: str
    detected_script: str
    canonical_query: str
    target_database: str
    pruned_schema: List[SchemaElement]
    generated_sql: str
    syntax_valid: bool
    execution_result: Optional[TabularResult]
    execution_error: Optional[str]
    reflection_attempts: int
    verbalized_response: str
    audit_trace: List[Dict[str, Any]]
```

### StateGraph Wiring & Reflection Loop:

```python
def create_indicsql_graph(checkpointer: MemorySaver):
    workflow = StateGraph(IndicSQLState)

    # Register Swarm Nodes
    workflow.add_node("supervisor_router", supervisor_node)
    workflow.add_node("schema_linker", schema_linker_node)
    workflow.add_node("sql_synthesizer", sql_synthesizer_node)
    workflow.add_node("sandbox_executor", sandbox_executor_node)
    workflow.add_node("reflection_healer", reflection_healer_node)
    workflow.add_node("response_verbalizer", response_verbalizer_node)

    # Set Entry Point
    workflow.set_entry_point("supervisor_router")

    # Define Edges
    workflow.add_edge("supervisor_router", "schema_linker")
    workflow.add_edge("schema_linker", "sql_synthesizer")
    workflow.add_edge("sql_synthesizer", "sandbox_executor")

    # Conditional Reflection Routing
    workflow.add_conditional_edges(
        "sandbox_executor",
        route_after_execution,
        {
            "success": "response_verbalizer",
            "retry": "reflection_healer",
            "fatal_error": "response_verbalizer",  # Verbalize graceful explanation
        },
    )

    workflow.add_edge("reflection_healer", "sql_synthesizer")
    workflow.add_edge("response_verbalizer", END)

    return workflow.compile(checkpointer=checkpointer)
```

------------------------------------------------------------------------

## 14. Reasoning Strategy: Cross-Lingual Chain-of-Thought & Reflection

### 1. Cross-Lingual Chain-of-Thought (CoT)
To prevent semantic degradation when translating Indic grammar (Subject-Object-Verb / SOV) into SQL logic (SELECT-FROM-WHERE / SFW), the SQL Synthesizer produces a multi-lingual reasoning scratchpad before outputting code:

```
[Reasoning Trace]
1. Input Question (Hindi): "बिहार के किस जिले में 2023 में सबसे कम महिला साक्षरता थी?"
2. Semantic Deconstruction:
   - Target Metric: Female Literacy Rate (साक्षरता) -> `female_literacy_rate`
   - Spatial Scope: District of Bihar (बिहार के किस जिले) -> `state_name = 'BIHAR'`, GROUP BY `district_name`
   - Temporal Filter: Year 2023 -> `census_year = 2023`
   - Order & Extrema: Lowest (सबसे कम) -> `ORDER BY female_literacy_rate ASC LIMIT 1`
3. Table Selection: `ndap_education_district_stats`
4. Generated SQL:
   SELECT district_name, female_literacy_rate 
   FROM ndap_education_district_stats 
   WHERE state_name = 'BIHAR' AND census_year = 2023 
   ORDER BY female_literacy_rate ASC 
   LIMIT 1;
```

### 2. Reflection on Zero-Row & Type-Error Execution:
When a query compiles but returns `0 rows` because the model wrote `WHERE state = 'bihar'` (lowercase) while the database stores `'BIHAR'`, the Reflection Agent executes an automated casing heuristic:
$$\text{Heuristic: If } |\text{Rows}| = 0 \land \text{FilterOnString}, \quad \text{Rewrite: } \text{ILIKE or UPPER}(column) = \text{UPPER}('value')$$

------------------------------------------------------------------------

## 15. Transparent Execution Trace Schema

```json
{
  "query_id": "ind-q-2026-0921-9912",
  "raw_query": "तमिलनाडु में पिछले 3 सालों में मनरेगा के तहत कितने कार्य दिवस बने?",
  "detected_language": "hi",
  "detected_script": "Devanagari",
  "target_database": "ndap_mgnrega_portal",
  "execution_trace": [
    {
      "step": 1,
      "agent": "SupervisorRouter",
      "action": "normalize_and_detect",
      "latency_ms": 42,
      "output": { "canonical_text": "तमिलनाडु में पिछले 3 सालों में मनरेगा के तहत कितने कार्य दिवस बने?", "script": "Devanagari" }
    },
    {
      "step": 2,
      "agent": "SchemaLinkerAgent",
      "action": "cross_lingual_mE5_lookup",
      "latency_ms": 118,
      "output": {
        "matched_table": "mgnrega_state_annual_employment",
        "matched_columns": ["state_name", "financial_year", "total_mandays_generated"],
        "confidence": 0.942
      }
    },
    {
      "step": 3,
      "agent": "SQLSynthesizerAgent (Sarvam-2B-LoRA)",
      "action": "generate_aggregation_sql",
      "latency_ms": 410,
      "token_usage": { "prompt": 620, "completion": 94 },
      "output_sql": "SELECT financial_year, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'TAMIL NADU' AND financial_year IN ('2022-23', '2023-24', '2024-25') GROUP BY financial_year ORDER BY financial_year DESC;"
    },
    {
      "step": 4,
      "agent": "SandboxExecutionAgent",
      "action": "duckdb_in_memory_run",
      "latency_ms": 28,
      "exit_code": 0,
      "row_count": 3,
      "sample_rows": [
        ["2024-25", 342198000],
        ["2023-24", 398104500],
        ["2022-23", 412009200]
      ]
    },
    {
      "step": 5,
      "agent": "ResponseVerbalizerAgent",
      "action": "generate_indic_nlg",
      "latency_ms": 320,
      "output_response": "तमिलनाडु में मनरेगा योजना के तहत पिछले तीन वर्षों में कुल 115.23 करोड़ कार्य दिवस (Mandays) उत्पन्न किए गए: वर्ष 2024-25 में 34.21 करोड़, 2023-24 में 39.81 करोड़ और 2022-23 में 41.20 करोड़ कार्य दिवस दर्ज हुए।"
    }
  ],
  "total_latency_seconds": 0.918,
  "execution_success": true
}
```

------------------------------------------------------------------------

## 16. In-Memory Sandboxed Database Runtime (DuckDB)

To prevent arbitrary SQL injection, denial-of-service, or production database locking, all query evaluation and reflection runs in an **ephemeral in-memory DuckDB sandbox**:

```mermaid
flowchart TD
    SQL_IN["Candidate SQL Query from Synthesizer Agent"] --> AST_CHECK["SQLGlot AST Parser and Linter"]
    
    AST_CHECK -->|Mutation Detected: DROP/INSERT/UPDATE| BLOCKED["Security Exception: Read-Only Violation"]
    AST_CHECK -->|Allowed: SELECT statements only| DUCKDB_ENGINE["DuckDB Isolated In-Memory Engine"]
    
    subgraph Sandbox_Constraints["Sandbox Resource and Execution Limits"]
        C1["Memory Cap: Max 512MB RAM"]
        C2["Timeout Budget: Hard limit 1.5 seconds"]
        C3["Max Output Tuples: LIMIT 1000 enforced"]
        C4["Read-Only Replica / Parquet Storage"]
    end
    
    DUCKDB_ENGINE -.-> C1
    
    DUCKDB_ENGINE -->|Execution Failure: Syntax / Missing Column| STDERR["Capture Stderr to Trigger Reflection Healer"]
    DUCKDB_ENGINE -->|Execution Success: Valid Tabular Output| STDOUT["Deliver Rows to Response Verbalizer"]
```

------------------------------------------------------------------------

## 17. Mobile & Voice UI: BharatQuery Mobile Cockpit

The client interface is built as a native **Flutter** mobile application (Android / iOS) designed for rural accessibility, field workers, and mobile-first citizens. The entire agentic Text-to-SQL swarm is wrapped inside an **ElevenLabs Conversational AI Voice & Chat Agent**, featuring an interactive 3D **audio-reactive morphing spherical blob**.

```mermaid
flowchart TD
    subgraph Mobile_Cockpit["BharatQuery Flutter Mobile Cockpit (Dual-Mode UI)"]
        TOP["Header: Language Selector, Engine Badge (Combo A/B/C) and Settings"]
        MODE{"Interface Mode"}
        
        subgraph Voice_View["Voice Mode (Primary)"]
            ORB["Audio-Reactive Spherical Blob\n(GLSL Shaders / CustomPainter: 60-120 FPS)\n• Idle: Breathing Chromatic Shift\n• Listening: VAD Reactive Pulse\n• Thinking: Swarm Orbital Rings\n• Speaking: Audio-Harmonic Sync"]
            ACTION["Call Controls: End Call / Mute / Hold to Speak"]
            LIVE_TRANS["Live Spoken Transcript:\n'बिहार के किस जिले में 2023 में सबसे कम महिला साक्षरता थी?'"]
            AUDIO_OUT["ElevenLabs Multilingual v2 Voice Stream:\n'डेटाबेस के अनुसार दरभंगा जिले में महिला साक्षरता 56% दर्ज की गई।'"]
        end

        subgraph Chat_View["Chat Mode (Minimalist)"]
            AVATAR["Condensed Glowing Orb Header Avatar"]
            CHAT_FEED["Bilingual Conversational Message Stream\n(Devanagari / Dravidian / Latin Scripts)"]
            INPUT_BAR["Floating Text Input: Type a message..."]
        end

        subgraph Data_Sheet["Collapsible Verified Data and Audit Sheet"]
            CARD["Civic Metric Card: Darbhanga - 56.0% (Lowest in Bihar)"]
            SQL_VIEW["Executed SQL: SELECT district_name, female_literacy_rate FROM ndap_education_stats"]
            TRACE["Swarm Trace: Supervisor (hi) to Linker to DuckDB (0.19ms)"]
        end

        subgraph Arena_Drawer["Model Arena Drawer (Secondary Slide-Out)"]
            ARENA_METRICS["Quantitative Matrix\n• Combo A (Hybrid): 81.2% EX / 410ms\n• Combo B (Sarvam): 75.4% EX / 290ms\n• Combo C (Qwen): 77.1% EX / 520ms"]
            ARENA_QUAL["Qualitative Phrasing & SQL Diff\n• Vernacular Idiom Preservation Score\n• Side-by-side generated SQL diff"]
            ARENA_SWITCH["Runtime Engine Dictation:\nToggle Active Backend (Combo A* / B / C)"]
        end

        TOP --> MODE
        TOP -.->|Tap Engine Pill| ARENA_METRICS
        ARENA_METRICS --> ARENA_QUAL
        ARENA_QUAL --> ARENA_SWITCH

        MODE -->|Voice Mode| ORB
        MODE -->|Chat Mode| AVATAR
        ORB --> ACTION
        ACTION --> LIVE_TRANS
        LIVE_TRANS --> AUDIO_OUT
        AVATAR --> CHAT_FEED
        CHAT_FEED --> INPUT_BAR
        AUDIO_OUT --> CARD
        INPUT_BAR --> CARD
        CARD --> SQL_VIEW
        SQL_VIEW --> TRACE
    end
```


### 17.1 Dual-Mode Interaction & Model Arena Drawer
1. **Voice Mode (The Spherical Orb View):**
   - Centered audio-reactive morphing gradient blob rendered via hardware-accelerated GLSL fragment shaders (`flutter_shaders` / `CustomPainter`).
   - Dynamic states:
     - **Idle:** Smooth breathing chromatic color shift.
     - **Listening:** Pulsing waves expanding proportionally to microphone input decibels.
     - **Thinking / Swarm Executing:** Accelerating orbital color rings while LangGraph queries DuckDB.
     - **Speaking:** Harmonic audio oscillation synchronized with incoming ElevenLabs audio chunks.
2. **Text / Chat Mode (Minimalist View):**
   - The spherical blob condenses into a glowing top header avatar.
   - Elegant chat stream with a clean floating text input bar (*"Type a message..."*). Supports Devanagari, Tamil, Telugu, Bengali, and code-mixed Latin (Hinglish).
3. **Model Arena & Tri-Combo Inspector Drawer (Secondary Comparative View):**
   - **Unobtrusive Accessibility:** Accessible via a subtle header badge (e.g., `⚡ Combo A: Champion`) or through settings. The primary citizen voice/chat UX remains clean and uncluttered.
   - **Quantitative Comparison Telemetry:**
     - Side-by-side benchmark scorecards displaying Execution Accuracy (`EX%`), latency (`ms`), AST validity rate, and token usage across:
       - **Combo A (Champion):** `Sarvam-2B` (Transliteration) + `Qwen-2.5-Coder` (SQL).
       - **Combo B (Ablation 1):** Pure `Sarvam-2B` monolithic pipeline.
       - **Combo C (Ablation 2):** Pure `Qwen-2.5-Coder` monolithic pipeline.
   - **Qualitative Phrasing & SQL Diff:**
     - Visual side-by-side diff comparing how each combo interpreted colloquial Indic idioms vs how it constructed the final relational query.
   - **Runtime Engine Dictation:**
     - Allows researchers or power users to immediately dictate which combo serves as the active execution backend, instantly routing subsequent queries through that pipeline.

---

### 17.2 Free-Tier API & LLM Credit-Defense Strategy (10x-20x Multiplier)

Operating on free tiers (ElevenLabs 10,000 monthly credits + free LLM quotas) requires strict minimization of outbound API and token expenses:

```mermaid
flowchart TD
    Q(["User Input Query (Voice / Text)"]) --> VAD["1. Client-Side Local VAD and Hash Computation\n• On-device silence suppression\n• Generate SHA-256 query hash"]
    
    VAD --> CACHE_CHECK{"Local Cache Check\n(Query and Audio Store)"}
    
    subgraph Zero_Cost_Tier["0-Cost Fast Path"]
        HIT["Zero API / Zero LLM Credits Consumed\n• Retrieve cached audio .mp3\n• Retrieve cached data card\n• Latency: under 50ms"]
    end
    
    subgraph Optimized_Inference_Tier["Credit-Defended Swarm Pipeline"]
        PRUNE["2. Dense Schema Pruning\n• In-Memory NDAP Catalog Indexer\n• Prunes 95% of schemas yielding 1 target table\n• Cuts LLM prompt tokens by 85%!"]
        SWARM["3. Deterministic Swarm Execution\n• Zero LLM calls for schema linking\n• DuckDB sandbox zero-copy Parquet execution\n• Structured tabular output"]
        TTS["4. Telegraphic TTS Synthesis\n• Voice summary strictly capped (under 100 chars)\n• Detailed table and SQL rendered visually for FREE!"]
    end

    CACHE_CHECK -->|Cache Hit| HIT
    CACHE_CHECK -->|Cache Miss| PRUNE
    PRUNE --> SWARM
    SWARM --> TTS
    
    HIT --> OUT(["Deliver to Mobile Cockpit"])
    TTS --> OUT
```


1. **Local Audio & Query Cache (The 0-Credit Path):**
   - 60–70% of civic queries target standard statistics (e.g., *"PM-KISAN Maharashtra"*, *"Lowest literacy Bihar"*).
   - Audio files are saved to `data/audio_cache/<query_hash>.mp3`. Identical queries return the pre-synthesized audio directly—**consuming 0 ElevenLabs credits and 0 LLM tokens**.
2. **Schema Pruning Token Saver (85% LLM Reduction):**
   - Instead of feeding massive 20-database DDLs (15,000+ tokens) to the LLM, the local `SchemaLinker` feeds *only* the single target table DDL (~250 tokens). This slashes LLM token consumption by **85% per query**.
3. **Telegraphic Audio Verbalization (< 100 Characters):**
   - ElevenLabs charges strictly per character synthesized.
   - Spoken responses are condensed into high-impact single sentences (*"बिहार में सबसे कम महिला साक्षरता दर दरभंगा में 56% दर्ज की गई।"* = 64 characters = 64 credits).
   - Full data tables, breakdowns, and SQL are displayed visually on the mobile screen for free.
   - **Result:** 10,000 credits yield **~150–200 fresh voice queries** and **1,500+ cached sessions**!
4. **On-Device Speech-to-Text Toggle:**
   - Option to use Android/iOS native on-device speech recognizer (`speech_to_text` Flutter package) for 100% free speech-to-text without hitting ElevenLabs STT quotas.


------------------------------------------------------------------------

## 18. Evaluation Strategy & Benchmark Dataset

IndicSQL will be evaluated directly against the published **IndicDB Benchmark (April 2026)**:

### Benchmark Structure:
- **Total Test Queries:** 15,617 natural language questions across 20 NDAP databases.
- **Languages:** 7 (Hindi, Bengali, Tamil, Telugu, Marathi, Hinglish, English).
- **Difficulty Classes:** Easy (Single table), Medium (Joins + Aggregations), Hard (Nested Subqueries, Temporal Windows).

### Metrics:
1. **Execution Accuracy (EX):**
   $$EX = \frac{1}{N} \sum_{i=1}^N \mathbb{I}\big(R(\hat{y}_i) = R(y_i^*)\big)$$
   Where $R(\cdot)$ represents the execution tuple set of predicted query $\hat{y}_i$ vs gold query $y_i^*$ on the test database.
2. **Schema-Linking F1 Score ($F1_{\text{SL}}$):** Precision and recall on predicted schema elements.
3. **Indic-to-English Delta ($\Delta_{\text{Indic-EN}}$):**
   $$\Delta_{\text{Indic-EN}} = EX_{\text{English}} - EX_{\text{Indic}}$$
   Target is to compress the baseline $9.0\%$ delta to $< 2.0\%$.

### Expected Benchmark Results Matrix:

| Language | IndicDB Published Baseline (GPT-4o / Llama-3) | IndicSQL Multi-Agent (Proposed) | Net Improvement |
| :--- | :--- | :--- | :--- |
| **English (en)** | 78.4% | **82.6%** | +4.2% |
| **Hinglish (hi-en)**| 71.53% (-6.87% gap) | **81.4% (-1.2% gap)** | **+9.87%** |
| **Marathi (mr)** | 70.30% (-8.10% gap) | **80.8% (-1.8% gap)** | **+10.5%** |
| **Hindi (hi)** | 70.00% (-8.40% gap) | **81.2% (-1.4% gap)** | **+11.2%** |
| **Bengali (bn)** | 69.20% (-9.20% gap) | **80.5% (-2.1% gap)** | **+11.3%** |
| **Tamil (ta)** | 68.60% (-9.80% gap) | **79.9% (-2.7% gap)** | **+11.3%** |
| **Telugu (te)** | 67.40% (-11.00% gap) | **79.8% (-2.8% gap)** | **+12.4%** |
| **Average Indic Gap**| **-8.89%** | **-2.00%** | **Gap Reduced by 77.5%** |

------------------------------------------------------------------------

## 19. Implementation Phase Plan (10-Week Roadmap)

```mermaid
gantt
    title IndicSQL 10-Week Engineering and Benchmark Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    todayMarker stroke-width:3px,stroke:#ff5252,opacity:0.8
    
    section Completed Milestones
    Phase 1 - Planning, PEAS and ADK Harness       :done, p1, 2026-09-23, 2026-10-02
    Phase 2 - 6-Agent Swarm and Schema Substrate   :done, p2, 2026-10-02, 2026-10-12
    Phase 3A - Advanced Intelligence and Events    :done, p3a, 2026-10-12, 2026-10-22
    Phase 3B - Dual-Model LoRA Fine-Tuning Engine  :done, p3b, 2026-10-22, 2026-11-02
    
    section Active Milestone
    Phase 3C - BharatQuery Flutter UI and Dashboard:active, p3c, 2026-11-02, 2026-11-12
    
    section Future Milestones
    Phase 4 - IndicDB Evaluation and Tri-Combo Run :p4, 2026-11-12, 2026-11-20
    Phase 5 - Enterprise Docker and Packaging      :p5, 2026-11-20, 2026-11-28
    Phase 6 - Final Paper, Report and Handover     :p6, 2026-11-28, 2026-12-05
```


### 19.1 Definition of Done

#### Phase 1 — Planning, PEAS, Scaffolding & State Contracts

- [x] Problem statement approved (April 2026 IndicDB vernacular Text-to-SQL gap identified)
- [x] PEAS specification completed (P: EX >82%, Indic gap <2%; E: 20 NDAP DBs; A: FastText, mE5, LoRA; S: Speech/Text, DDLs, DuckDB stdout/err)
- [x] Environment analysis completed (20 Indian Government NDAP relational schemas, complex joins, time-series)
- [x] Agent responsibilities defined (Supervisor, Schema-Linker, SQL Synthesizer, DuckDB Sandbox, Verbalizer, Critic)
- [x] Architecture diagrams completed (System architecture, sequence diagrams, LangGraph state machine)
- [x] RAG & Schema-Linking strategy defined (Tripartite: Phonetic IndicXlit, dense mE5/BGE-M3 embeddings, categorical inverted index)
- [x] Reasoning strategy defined (Cross-Lingual Chain-of-Thought scratchpad with SOV-to-SFW semantic deconstruction)
- [x] Communication strategy defined (Sequential, parallel catalog broadcast, Blackboard shared state, hierarchical reflection)
- [x] Tech stack justified (DuckDB, LangGraph, Sarvam-2B, Qwen-2.5-Coder, ElevenLabs, Flutter)
- [x] Timeline completed (10-Week Engineering and Benchmark Roadmap)
- [x] Team responsibility matrix completed
- [x] Minimal ADK prototype demonstrated (20 NDAP databases in Parquet + `evaluate_benchmark.py` harness passing 100% EX on baseline)

#### Phase 2 — Core Multi-Agent Swarm, Schema Linking & Vernacular Audio Loop

- [x] Six core agents operational (`supervisor_node`, `schema_linker_node`, `sql_synthesizer_node`, `sandbox_executor_node`, `response_verbalizer_node`, `critic_node`)
- [ ] Speech / Audio Agent operational (bidirectional ElevenLabs Conversational AI voice/audio stream with hands-free loop)
- [x] Sequential workflow operational (Supervisor -> Schema-Linker -> Synthesizer -> Sandbox -> Verbalizer)
- [x] Hierarchical workflow operational (Supervisor dynamically arbitrating reflection loops on runtime errors)
- [x] Shared state operational (`IndicSQLState` TypedDict tracking query, script, pruned schema, candidate SQL, tabular tuples, audit trace)
- [x] RAG operational with atomic claim-to-chunk provenance (`matched_table`, `matched_columns`, `confidence_score`, `catalog_version`)
- [x] Tools operational (FastText language detector, IndicXlit transliterator, DuckDB in-memory execution sandbox, SQLGlot AST linter)
- [x] Safety validation operational (SQLGlot AST parser blocking mutations: `DROP`, `INSERT`, `UPDATE`, `DELETE`, enforcing read-only transactions)
- [x] Critic/reflection operational (intercepting DuckDB syntax/casing/type errors and executing self-healing reflection loops)
- [x] Persistent memory operational (DuckDB session cache and LangGraph MemorySaver checkpointing)
- [x] MCP integration operational (Graphify AST knowledge graph and local OmniRoute toolchain)
- [x] Structured traces operational with database provenance claims (step-by-step execution latency, token counts, and returned tuples)
- [ ] Working frontend with speech interaction (ElevenLabs audio streaming with local audio cache)
- [x] Initial evaluation suite (19/19 passing tests across all 20 NDAP databases and 7 target languages)

#### Phase 3A — Advanced Agent Intelligence & Event-Driven Architecture

- [x] Tree-of-Thoughts (ToT) multi-candidate sequence exploration operational in SQL Synthesizer & Schema Linker
- [x] Weighted utility function candidate scoring operational (ranking candidate SQL by AST safety, join validity, and schema similarity)
- [x] Asynchronous Pub/Sub Event Bus (`indicsql/events/bus.py`) operational for multi-agent decoupled communication
- [x] Typed event schemas (`QueryInitiatedEvent`, `SchemaLinkedEvent`, `ExecutionCompletedEvent`, `ReflectionTriggeredEvent`, `VoiceSynthesisEvent`)
- [x] Dynamic DDL prompt injection operational (eliminating hardcoded rule-based generation with live schema context)
- [x] Unit tests for ToT query planning and Event Bus passing

#### Phase 3B — Sovereign Dual-Model LoRA Fine-Tuning Engine (Sarvam-2B & Qwen-2.5-Coder)

- [x] Dataset curation pipeline operational for `IndicSQL-Agg-12K` (12,000 paired Indic questions, DDLs, and Gold SQL across 7 languages)
- [x] Partition 1 curated for `Sarvam-2B`: Indic contextual transliteration, dialectal normalization, and semantic entity/filter boundary deconstruction
- [x] Partition 2 curated for `Qwen-2.5-Coder`: Complex aggregation SQL synthesis (`GROUP BY`, nested subqueries, temporal windows, and multi-table joins)
- [x] 4-bit NormalFloat (NF4) QLoRA training harness operational with Unsloth / Hugging Face PEFT & TRL (<24GB VRAM footprint)
- [x] Target adapter modules configured (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`)
- [x] Exported LoRA adapter weights integrated into `models/lora_weights/` (`qwen_adapter` & `sarvam_adapter`) with offline detection & fallback
- [x] Tri-Combo execution harness established for runtime comparison (Combo A: Hybrid Champion, Combo B: Sarvam Pure, Combo C: Qwen Pure)
- [x] Dynamic adapter switching & zero-copy LoRA runtime serving via vLLM / Hugging Face pipeline
- [x] Expanded 105-query IndicDB benchmark suite & baseline leaderboard matrix comparison (`scripts/evaluate_benchmark.py --suite-expanded --compare-baselines`)
- [x] Unit tests for fine-tuning dataset integrity, tokenization coverage across 7 scripts, and LoRA inference passing

#### Phase 3C — BharatQuery Flutter Mobile Cockpit UI & Swarm Observability Dashboard

- [ ] Hardware-accelerated GLSL shader canvas with audio-reactive 3D morphing spherical blob (Idle breathing, listening pulse, thinking orbits, speaking wave)
- [ ] Live visual HUD with green/yellow/red SQL execution status rings and latency indicators
- [ ] Synchronous vernacular audio player for ElevenLabs Multilingual v2 / on-device TTS with telegraphic brevity clamp (<100 chars)
- [ ] Swarm Observability & Trace Analytics Dashboard (`indicsql/ui/dashboard.py` / Flutter Drawer) operational
- [ ] Per-agent latency waterfalls, token usage by model (Sarvam vs Qwen), and communication visualizer
- [ ] Model Arena Drawer: qualitative side-by-side phrasing/SQL diff inspector and runtime engine switcher (Combo A* / Combo B / Combo C)
- [ ] Real-time FPS monitor for 3D shader blob and sub-second speech turnaround monitor

#### Phase 4 — Scientific Evaluation & Benchmark Experiments (15,617 IndicDB Runs)

- [ ] 15,617 diverse evaluation runs executed across all 20 NDAP databases and 7 languages (Hindi, Bengali, Tamil, Telugu, Marathi, Hinglish, English)
- [ ] 3-way Tri-Combo architectural comparison benchmark (Combo A: Hybrid Champion vs Combo B: Sarvam Pure vs Combo C: Qwen Pure)
- [ ] Multi-model baseline comparison (Proposed Dual-Model vs GPT-4o baseline vs Llama-3 baseline)
- [ ] Human-in-the-Loop (HITL) domain expert panel evaluation completed across vernacular responses (civic validity & numeral correctness)
- [ ] Inter-rater reliability (Cohen's / Fleiss' Kappa) measured on expert linguistic and SQL equivalence rubric scores
- [ ] Reflection loop ablation study completed (measuring EX% delta with 0, 1, 2, and 3 reflection repair attempts)
- [ ] End-to-end latency benchmark with p95 measured against the sub-second database execution budget (<150ms DuckDB ceiling)

#### Phase 5 — Enterprise Containerization & Production Docker Packaging

- [ ] Production multi-stage backend Dockerfile (`Dockerfile.backend`) with non-root security user & minimal slim Python 3.12/3.14 runtime
- [ ] Production frontend Dockerfile / Flutter web build pipeline (`Dockerfile.frontend`) with multi-stage build optimization
- [ ] Orchestrated `docker-compose.yml` and `docker-compose.prod.yml` with isolated networks (`api`, `qdrant`, `sandbox`, `gateway`)
- [ ] Enterprise resource quotas, health checks, and restart policies configured for client host environments
- [ ] Persistent volume orchestration for Parquet stores (`data/parquet_stores`), schema catalogs (`data/catalogs`), and model LoRA weights (`models/lora_weights`)
- [ ] Reverse proxy configuration (Nginx / Caddy) with WebSocket support, streaming audio chunking, CORS, and TLS termination
- [ ] Production environment template (`.env.production.example`) with API key masking and strict validation
- [ ] Automated container smoke tests and CI verification script (`scripts/docker_smoke_test.sh`)
- [ ] Enterprise deployment guide & operations runbook (`docs/DEPLOYMENT_GUIDE.md`)

#### Phase 6 — Client Handover, Final Technical Report & Defense Deliverables

- [ ] Comprehensive IEEE-style academic final report & enterprise technical whitepaper completed (`docs/FINAL_REPORT.md` / `paper/indic_sql_paper.pdf`)
- [ ] Turnkey Client Handover Package with SLA verification, NDAP schema registry, and architectural runbook
- [ ] Executive presentation slide deck and live interactive demonstration script completed
- [ ] Viva defense & technical review preparation guide with design rationale completed


------------------------------------------------------------------------

## 20. Technology Stack

```
AI, Voice & Language Models:
├── sarvamai/sarvam-2b (Primary Sovereign Indic Language Model)
├── Qwen/Qwen2.5-Coder-7B-Instruct (Secondary Code/SQL Model)
├── ElevenLabs Conversational AI (Voice Agent & Multilingual v2 TTS)
├── ElevenLabs Scribe / Whisper (Streaming Speech-to-Text)
├── Unsloth / Hugging Face PEFT & TRL (QLoRA 4-Bit Fine-Tuning)
├── vLLM (High-Throughput Model Serving)
├── intfloat/multilingual-e5-large & BAAI/bge-m3 (Dense Cross-Lingual Embeddings)
└── AI4Bharat IndicXlit / IndicBERT (Phonetic Transliteration Engine)

Multi-Agent Core & Database Engine:
├── LangGraph & LangChain (State Machine & Workflow Cycles)
├── DuckDB (In-Memory Ephemeral SQL Execution Sandbox)
├── PostgreSQL 16 (Relational Database Storage & Replicas)
├── Qdrant (Distributed Vector DB for Schema Descriptions)
├── SQLGlot (SQL AST Parsing, Transpilation & Safety Linter)
└── Pydantic v2 & FastAPI (REST/WebSocket API Gateway & ElevenLabs Tool Webhook)

Mobile Citizen Cockpit (Flutter Client):
├── Flutter 3.x / Dart (Cross-Platform Android & iOS)
├── flutter_shaders / CustomPainter (Audio-Reactive Morphing Spherical Blob)
├── elevenlabs_conversational_ai / web_socket_channel (Real-Time Audio Streaming)
├── fl_chart (Mobile Civic Data Visualizations)
└── speech_to_text (Zero-Credit On-Device Mobile STT Fallback)
```

------------------------------------------------------------------------

## 21. Academic & Social Impact Positioning

IndicSQL is positioned at the intersection of **cutting-edge agentic systems research** and **civic data democratization**:

1. **Academic Impact:** First empirical solution resolving the open challenge posed by the April 2026 IndicDB benchmark, proving that targeted architectural specialization (phonetic schema-linking + aggregation fine-tuning) outperforms brute-force LLM scaling on vernacular data tasks.
2. **Democratization Impact:** Unlocks India's national data wealth (NDAP) for village sarpanches, local journalists, students, and farmers, allowing any citizen to ask questions in their mother tongue and receive immediate, verified public evidence.
