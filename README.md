# Agentic RAG with LangGraph & Google Gemini

This project implements an **Agentic RAG (Retrieval Augmented Generation)** system using LangGraph and Google's Gemini models.

## Features

- **Agentic Workflow:** Uses a "Retrieve -> Grade -> Generate" loop.
- **Google Gemini:** powered by `gemini-2.0-flash` (LLM) and `embedding-001`.
- **Local Vector DB:** Uses ChromaDB to store and index PDF documents.
- **Directory Ingestion:** Automatically ingests all PDFs from the `database/` directory.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/fatihsaribiyik2003/agentic_rag.git
    cd agentic_rag
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up environment variables:
    Create a `.env` file and add your Google API Key:
    ```bash
    GOOGLE_API_KEY=your_api_key_here
    ```

## Usage

1.  Place your PDF files into the `database/` folder.
2.  Run the agent:
    ```bash
    python agentic_rag.py
    ```
3.  Ask questions in the terminal!

## Files

- `agentic_rag.py`: Main agentic RAG implementation.
- `chatbot_google.py`: Simple chatbot using Gemini.
- `simple_graph.py`: Basic LangGraph example.
