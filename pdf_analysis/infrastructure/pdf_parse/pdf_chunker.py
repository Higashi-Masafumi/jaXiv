from pathlib import Path

import pymupdf4llm
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter

from domain.entities.text_chunk import TextChunk
from domain.gateways.pdf_chunker import PdfChunkerGateway


class PyMuPdfChunker(PdfChunkerGateway):
    """PDF chunker using pymupdf4llm + llama-index two-stage strategy.

    Stage 1: MarkdownNodeParser splits by section headers (Abstract, Introduction, etc.)
    Stage 2: SentenceSplitter enforces 512-token limit without mid-sentence cuts.
    This hybrid approach is optimal for academic papers (arXiv).
    """

    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50

    def chunk_pdf(self, pdf_path: Path) -> list[TextChunk]:
        raw_chunks = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True)

        llama_docs = [
            Document(
                text=chunk["text"],
                metadata={"page_number": chunk["metadata"]["page_number"]},
            )
            for chunk in raw_chunks
        ]

        section_nodes = MarkdownNodeParser(
            include_metadata=True
        ).get_nodes_from_documents(llama_docs)
        final_nodes = SentenceSplitter(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
        ).get_nodes_from_documents(section_nodes)

        return [
            TextChunk(text=node.text, page_number=node.metadata["page_number"])
            for node in final_nodes
            if node.text.strip()
        ]
