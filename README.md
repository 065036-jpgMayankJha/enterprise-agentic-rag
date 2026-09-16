# enterprise-agentic-rag

Agent multi-department enterprise RAG system using Docling, LlamaIndex, CrewAI, Qdrant and Ollama Cloud.

## Document Parser

The parser uses Docling to convert supported documents into Markdown and generate JSON metadata sidecar files.

### Supported Formats

- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Microsoft Excel (`.xlsx`)

### Supported Departments

- HR
- Finance
- Legal
- Customer

### Features

- Scans department folders recursively.
- Converts supported documents into Markdown.
- Generates a separate JSON metadata file for each converted document.
- Preserves the department folder structure in the output.
- Skips unsupported file formats and departments.
- Rejects empty Markdown output.
- Logs parsing activity and conversion errors.

### Metadata Fields

Each JSON metadata file contains:

- `department`
- `source_file`
- `file_type`
- `source_path`

### Project Structure

```text
enterprise-agentic-rag/
├── data/
│   ├── input/
│   └── processed/
├── docs/
├── parser/
│   └── document_parser.py
├── logs/
├── agents/
├── rag/
├── frontend/
├── tests/
├── requirements.txt
└── README.md
