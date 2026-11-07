# 🇮🇳 BharatQuery Cockpit (Frontend)

> **Production-grade Next.js 14 Web Cockpit for IndicSQL — Autonomous Cross-Lingual Text-to-SQL Swarm for Indian Open Government Data (NDAP)**

---

## 📌 Architecture Overview

BharatQuery Cockpit is built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, and **Recharts**. It is engineered to provide an intuitive, transparent, and accessible mother-tongue data exploration interface for 1.4 billion citizens across **7 Indian languages** (*Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, English*).

### ✨ Key Features

1. **🎙️ Zero-Dropdown Voice Mic:**
   - Speak naturally in any Indian language. The system and backend automatically detect the language with zero manual dropdown selection.
   - Animated visual recording pulse and clean audio transcription.
2. **🗣️ Natural-Language Mother-Tongue Answers:**
   - Locale-aware Indian number formatting (Lakhs, Crores, ₹).
   - **🔊 Text-to-Speech (Speaker):** Read aloud in native mother-tongue accents with one click.
   - Instant copy action.
3. **🤖 Agent Swarm Transparency Stepper:**
   - Live visual audit of all 5 execution stages:
     - Language & Script detection (`SupervisorAgent`)
     - Schema Linking (`SchemaLinkerAgent` -> NDAP Table)
     - Dialect SQL Generation with expandable formatted code view
     - AST Security Critic (`Read-Only SELECT Verified`)
     - DuckDB In-Memory Execution Latency (e.g., `0.67 ms`)
4. **📊 Dynamic Visualizer & Civic Data Grid:**
   - **Visual Charts:** Auto Bar/Line charts using Recharts for categorical or temporal distributions. Bold KPI Metric cards for single scalar answers.
   - **Data Table:** Dynamic columns, right-aligned numbers, and client-side pagination.
   - **CSV Export:** RFC 4180 compliant CSV export with UTF-8 BOM to preserve Indic scripts in Excel.
5. **🏛️ 20 NDAP Database Explorer:**
   - Slide-over drawer categorized across 4 sectors: **Agriculture, Education, Health and Demographics, Rural Development**.
   - Live table schema, record counts, and column definitions populated directly from `GET /schemas`.
6. **Honest Connectivity State:**
   - Live status indicator displaying whether the local backend (`localhost:8000`) is connected or disconnected.

---

## 🚀 Quickstart

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.local` (copied from `.env.example`):

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Run the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production

```bash
npm run build
npm start
```

### 5. Run Utility Tests

```bash
npm test
```

---

## 📂 Directory Layout

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css         # Tailwind & theme variables
│   │   ├── layout.tsx          # Root HTML layout & metadata
│   │   └── page.tsx            # Main single-page query cockpit
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx           # Brand, connectivity indicator, explorer trigger
│   │   │   └── DatabaseDrawer.tsx   # 20 NDAP database slide-over catalog
│   │   ├── query/
│   │   │   ├── QueryComposer.tsx    # Multiline input with keyboard shortcuts
│   │   │   ├── SampleQuestions.tsx  # Selectable 7-language sample chips
│   │   │   └── VoiceInput.tsx       # Zero-dropdown audio mic recorder
│   │   ├── results/
│   │   │   ├── ResultsWorkspace.tsx # Coordinated results orchestrator
│   │   │   ├── AnswerCard.tsx       # Hero mother-tongue answer + TTS
│   │   │   ├── ExecutionPipeline.tsx# 5-stage swarm transparency stepper
│   │   │   ├── SqlViewer.tsx        # Syntax-highlighted expandable SQL viewer
│   │   │   ├── DataExplorer.tsx     # Chart/Table tab coordinator + CSV download
│   │   │   ├── ChartRenderer.tsx    # Recharts Bar/Line/KPI visualizer
│   │   │   └── DataTable.tsx        # Paginated civic data grid
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Tabs.tsx
│   │       ├── Skeleton.tsx
│   │       └── StatusIndicator.tsx
│   ├── lib/
│   │   ├── api-client.ts       # Typed centralized API client with runtime validation
│   │   ├── chart-utils.ts      # Auto-chart type detection logic
│   │   ├── csv-export.ts       # UTF-8 BOM CSV exporter
│   │   ├── formatters.ts       # Indian numbering (Lakhs/Crores) & latency formatters
│   │   └── speech.ts           # Web Speech API & MediaRecorder voice integration
│   └── types/
│       ├── api.ts              # Strongly-typed API contracts
│       └── datasets.ts         # Sector mappings & dataset metadata
├── scripts/
│   └── test-utils.js           # Unit tests for formatters and CSV escaping
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

## 📌 Architecture Overview

BharatQuery Cockpit is built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, and **Recharts**. It is engineered to provide an intuitive, transparent, and accessible mother-tongue data exploration interface for 1.4 billion citizens across **7 Indian languages** (*Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, English*).

### ✨ Key Features

1. **🎙️ Zero-Dropdown Voice Mic:**
   - Speak naturally in any Indian language. The system and backend automatically detect the language with zero manual dropdown selection.
   - Animated visual recording pulse and clean audio transcription.
2. **🗣️ Natural-Language Mother-Tongue Answers:**
   - Locale-aware Indian number formatting (Lakhs, Crores, ₹).
   - **🔊 Text-to-Speech (Speaker):** Read aloud in native mother-tongue accents with one click.
   - Instant copy action.
3. **🤖 Agent Swarm Transparency Stepper:**
   - Live visual audit of all 5 execution stages:
     - Language & Script detection (`SupervisorAgent`)
     - Schema Linking (`SchemaLinkerAgent` -> NDAP Table)
     - Dialect SQL Generation with expandable formatted code view
     - AST Security Critic (`Read-Only SELECT Verified`)
     - DuckDB In-Memory Execution Latency (e.g., `0.67 ms`)
4. **📊 Dynamic Visualizer & Civic Data Grid:**
   - **Visual Charts:** Auto Bar/Line charts using Recharts for categorical or temporal distributions. Bold KPI Metric cards for single scalar answers.
   - **Data Table:** Dynamic columns, right-aligned numbers, and client-side pagination.
   - **CSV Export:** RFC 4180 compliant CSV export with UTF-8 BOM to preserve Indic scripts in Excel.
5. **🏛️ 20 NDAP Database Explorer:**
   - Slide-over drawer categorized across 4 sectors: **Agriculture, Education, Health and Demographics, Rural Development**.
   - Live table schema, record counts, and column definitions populated directly from `GET /schemas`.
6. **Honest Connectivity State:**
   - Live status indicator displaying whether the local backend (`localhost:8000`) is connected or disconnected.

---

## 🚀 Quickstart

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.local` (copied from `.env.example`):

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Run the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production

```bash
npm run build
npm start
```

### 5. Run Utility Tests

```bash
npm test
```

---

## 📂 Directory Layout

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css         # Tailwind & theme variables
│   │   ├── layout.tsx          # Root HTML layout & metadata
│   │   └── page.tsx            # Main single-page query cockpit
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx           # Brand, connectivity indicator, explorer trigger
│   │   │   └── DatabaseDrawer.tsx   # 20 NDAP database slide-over catalog
│   │   ├── query/
│   │   │   ├── QueryComposer.tsx    # Multiline input with keyboard shortcuts
│   │   │   ├── SampleQuestions.tsx  # Selectable 7-language sample chips
│   │   │   └── VoiceInput.tsx       # Zero-dropdown audio mic recorder
│   │   ├── results/
│   │   │   ├── ResultsWorkspace.tsx # Coordinated results orchestrator
│   │   │   ├── AnswerCard.tsx       # Hero mother-tongue answer + TTS
│   │   │   ├── ExecutionPipeline.tsx# 5-stage swarm transparency stepper
│   │   │   ├── SqlViewer.tsx        # Syntax-highlighted expandable SQL viewer
│   │   │   ├── DataExplorer.tsx     # Chart/Table tab coordinator + CSV download
│   │   │   ├── ChartRenderer.tsx    # Recharts Bar/Line/KPI visualizer
│   │   │   └── DataTable.tsx        # Paginated civic data grid
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Tabs.tsx
│   │       ├── Skeleton.tsx
│   │       └── StatusIndicator.tsx
│   ├── lib/
│   │   ├── api-client.ts       # Typed centralized API client with runtime validation
│   │   ├── chart-utils.ts      # Auto-chart type detection logic
│   │   ├── csv-export.ts       # UTF-8 BOM CSV exporter
│   │   ├── formatters.ts       # Indian numbering (Lakhs/Crores) & latency formatters
│   │   └── speech.ts           # Web Speech API & MediaRecorder voice integration
│   └── types/
│       ├── api.ts              # Strongly-typed API contracts
│       └── datasets.ts         # Sector mappings & dataset metadata
├── scripts/
│   └── test-utils.js           # Unit tests for formatters and CSV escaping
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

