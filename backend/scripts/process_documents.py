"""
Document Processing Pipeline for DRRM Knowledge Base
Processes large documents into chunks for vector storage
"""

import sys
from pathlib import Path
from typing import List, Dict
import re

backend_dir = Path(__file__).parent.parent
data_dir = backend_dir.parent / "data"
sys.path.insert(0, str(backend_dir))

class DocumentProcessor:
    """Process DRRM documents for vector database storage."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """Initialize document processor.

        Args:
            chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, doc_id: str, metadata: Dict) -> List[Dict]:
        """Split text into overlapping chunks."""

        text = self._clean_text(text)

        chunks = []
        start = 0
        chunk_num = 0

        while start < len(text):
            end = start + self.chunk_size

            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period > start + self.chunk_size // 2:
                    end = last_period + 1
            
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_number': chunk_num,
                    'chunk_start': start,
                    'chunk_end': end
                })
                
                chunks.append({
                    'text': chunk_text,
                    'id': f"{doc_id}_chunk_{chunk_num}",
                    'metadata': chunk_metadata
                })
                
                chunk_num += 1
            
            # Move start position with overlap
            start = max(start + self.chunk_size - self.overlap, end)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        return text.strip()
    
    
if __name__ == "__main__":
    processor = DocumentProcessor()

    sample_text = """
    The National Disaster Risk Reduction and Management Plan (NDRRMP) 2020-2030 provides the framework for disaster risk reduction in the Philippines. The plan focuses on four thematic areas: prevention and mitigation, preparedness, response, and rehabilitation and recovery. 
    
    Prevention and mitigation activities include hazard mapping, early warning systems, and structural mitigation measures. Land use planning and building codes enforcement are critical components.
    
    Preparedness involves capacity building, contingency planning, and resource mobilization. Local government units must develop comprehensive disaster preparedness plans.
    """

    chunks = processor.chunk_text(
        sample_text, 
        "ndrrmp_2020_2030", 
        {"type": "policy", "source": "NDRRMC", "category": "framework"}
    )
    
    print(f"Generated {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"- {chunk['id']}: {len(chunk['text'])} chars")
