"""
Memory Manager for Document Classification Agent

Uses mem0 as the memory layer with GraphBit EmbeddingClient for embeddings.
Provides:
- Storing agent execution history
- Tracking document classification context  
- Semantic search over past classifications
- Document summary storage and retrieval
"""

import os
import json
import logging
import atexit
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from dotenv import load_dotenv

# Load .env from backend directory
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# Try to import mem0
try:
    from mem0 import Memory, MemoryClient
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.warning("mem0 not installed. Install with: pip install mem0ai")

# Try to import GraphBit embedding client for custom embeddings
try:
    from graphbit import EmbeddingConfig, EmbeddingClient
    GRAPHBIT_AVAILABLE = True
except ImportError:
    GRAPHBIT_AVAILABLE = False
    logger.warning("graphbit not installed. Install with: pip install graphbit")


class GraphBitEmbedder:
    """
    Custom embedder using GraphBit EmbeddingClient.
    This class wraps GraphBit to provide embeddings for mem0.
    """

    def __init__(self):
        """Initialize the GraphBit embedder with OpenAI."""
        self._client: Optional[EmbeddingClient] = None
        self._initialized = False
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    def _ensure_initialized(self):
        """Lazy initialization of the embedding client."""
        if self._initialized:
            return

        if not GRAPHBIT_AVAILABLE:
            raise RuntimeError("GraphBit is not installed")

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")

        embedding_config = EmbeddingConfig.openai(
            api_key=api_key,
            model=self.model
        )
        self._client = EmbeddingClient(embedding_config)
        self._initialized = True
        logger.info(f"GraphBit EmbeddingClient initialized with OpenAI model: {self.model}")

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        self._ensure_initialized()
        return self._client.embed(text)

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        self._ensure_initialized()
        return self._client.embed_many(texts)


class MemoryManager:
    """
    Memory manager for document classification agent.

    Uses mem0 for memory management with GraphBit for embeddings.
    Falls back to simple in-memory storage if mem0 is not available.

    Memory Types:
    - classification: Document classification results
    - summary: Document summaries
    - context: Agent context and history
    """

    def __init__(
        self,
        user_id: str = "classifier_agent",
        agent_id: str = "document_classifier"
    ):
        """
        Initialize memory manager.

        Args:
            user_id: User ID for mem0 memory association
            agent_id: Agent ID for mem0
        """
        self.user_id = user_id
        self.agent_id = agent_id

        # mem0 memory instance
        self._memory: Optional[Memory] = None

        # GraphBit embedder
        self._embedder: Optional[GraphBitEmbedder] = None

        # Fallback storage
        self._simple_memory: List[Dict] = []
        self._initialized = False

        # Register cleanup on exit
        atexit.register(self.close)

    def close(self) -> None:
        """Properly close mem0 and Qdrant connections."""
        if self._memory is not None:
            try:
                # Access the internal vector store and close it if it's Qdrant
                if hasattr(self._memory, 'vector_store') and self._memory.vector_store is not None:
                    vs = self._memory.vector_store
                    if hasattr(vs, 'client') and vs.client is not None:
                        try:
                            vs.client.close()
                        except Exception:
                            pass  # Ignore errors during cleanup
                self._memory = None
            except Exception:
                pass  # Ignore errors during cleanup
        self._initialized = False

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during destruction

    def _initialize(self) -> None:
        """Initialize mem0 with GraphBit embeddings."""
        if self._initialized:
            return

        if MEM0_AVAILABLE and GRAPHBIT_AVAILABLE:
            try:
                # Initialize GraphBit embedder
                self._embedder = GraphBitEmbedder()

                # Test embedding to ensure it works
                try:
                    test_embedding = self._embedder.embed("test")
                    if test_embedding is None or len(test_embedding) == 0:
                        logger.warning("GraphBit embedder returned empty embedding. Using simple memory.")
                        self._embedder = None
                        self._initialized = True
                        return
                    embedding_dim = len(test_embedding)
                    logger.info(f"GraphBit embeddings working. Dimension: {embedding_dim}")
                except Exception as embed_error:
                    logger.warning(f"GraphBit embedding test failed: {embed_error}. Using simple memory.")
                    self._embedder = None
                    self._initialized = True
                    return

                # Get OpenAI API key for both LLM and embeddings
                openai_api_key = os.getenv("OPENAI_API_KEY")
                llm_model = os.getenv("OPENAI_LLM_MODEL", "gpt-4o")
                embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

                if not openai_api_key:
                    logger.warning("OPENAI_API_KEY not configured. Using simple memory.")
                    self._initialized = True
                    return

                # Determine embedding dimensions based on model
                # text-embedding-3-small: 1536, text-embedding-3-large: 3072, text-embedding-ada-002: 1536
                embedding_dims = {
                    "text-embedding-3-small": 1536,
                    "text-embedding-3-large": 3072,
                    "text-embedding-ada-002": 1536,
                }
                embedding_dim = embedding_dims.get(embedding_model, embedding_dim if embedding_dim else 1536)

                # Configure mem0 with OpenAI for both LLM and embeddings
                # Include vector_store config to ensure proper Qdrant integration
                config = {
                    "llm": {
                        "provider": "openai",
                        "config": {
                            "model": llm_model,
                            "api_key": openai_api_key,
                        }
                    },
                    "embedder": {
                        "provider": "openai",
                        "config": {
                            "model": embedding_model,
                            "api_key": openai_api_key,
                            "embedding_dims": embedding_dim,
                        }
                    },
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "collection_name": "document_classifier_memory",
                            "embedding_model_dims": embedding_dim,
                            "on_disk": True,
                        }
                    },
                    "version": "v1.1"
                }

                # Try to initialize mem0
                self._memory = Memory.from_config(config)
                logger.info(f"mem0 initialized successfully with OpenAI and Qdrant (embedding_dim={embedding_dim})")

            except Exception as e:
                logger.warning(f"Failed to initialize mem0: {e}. Using simple memory.")
                self._memory = None
                self._embedder = None
        else:
            missing = []
            if not MEM0_AVAILABLE:
                missing.append("mem0ai")
            if not GRAPHBIT_AVAILABLE:
                missing.append("graphbit")
            logger.info(f"Missing packages: {missing}. Using simple in-memory storage.")

        self._initialized = True

    def add_memory(
        self, 
        content: str, 
        metadata: Dict[str, Any] = None,
        memory_type: str = "classification"
    ) -> str:
        """
        Add a memory entry to mem0.

        Args:
            content: The memory content
            metadata: Additional metadata to store
            memory_type: Type of memory (classification, summary, context)

        Returns:
            Memory ID
        """
        self._initialize()

        timestamp = datetime.now().isoformat()
        full_metadata = {
            **(metadata or {}),
            "type": memory_type,
            "timestamp": timestamp
        }

        if self._memory:
            try:
                # Add to mem0 with infer=False to store content directly
                # without LLM fact extraction (which can cause embedding issues)
                result = self._memory.add(
                    content,
                    user_id=self.user_id,
                    agent_id=self.agent_id,
                    metadata=full_metadata,
                    infer=False  # Disable LLM inference to prevent embedding errors
                )

                # Extract memory ID from result
                memory_id = self._extract_memory_id(result)
                logger.info(f"Added memory to mem0: {memory_id}")
                return memory_id

            except Exception as e:
                logger.warning(f"Failed to add to mem0: {e}. Using simple storage.")

        # Fallback to simple storage
        memory_id = f"mem_{len(self._simple_memory)}_{timestamp.replace(':', '-')}"
        full_metadata["id"] = memory_id
        full_metadata["content"] = content
        self._simple_memory.append(full_metadata)
        logger.info(f"Added memory to simple storage: {memory_id}")
        return memory_id

    def _extract_memory_id(self, result) -> str:
        """Extract memory ID from mem0 result."""
        if isinstance(result, dict):
            if "results" in result:
                results = result.get("results", [])
                if results:
                    return results[0].get("id") or results[0].get("memory_id") or "unknown"
            return result.get("id") or result.get("memory_id") or "unknown"
        elif isinstance(result, list) and result:
            return result[0].get("id") or result[0].get("memory_id") or "unknown"
        return f"mem0_{datetime.now().timestamp()}"

    def search_memory(
        self, 
        query: str, 
        limit: int = 5,
        memory_type: str = None
    ) -> List[Dict]:
        """
        Search memory for relevant entries.

        Args:
            query: Search query
            limit: Maximum number of results
            memory_type: Filter by memory type

        Returns:
            List of relevant memory entries
        """
        self._initialize()

        if self._memory:
            try:
                results = self._memory.search(
                    query=query,
                    user_id=self.user_id,
                    agent_id=self.agent_id,
                    limit=limit
                )

                # Normalize results
                memories = self._normalize_search_results(results)

                # Filter by type if specified (with safe access)
                if memory_type:
                    memories = [
                        m for m in memories 
                        if m and (m.get("metadata") or {}).get("type") == memory_type
                    ]

                return memories

            except Exception as e:
                logger.warning(f"Failed to search mem0: {e}. Using simple search.")

        # Fallback to simple keyword search
        results = []
        query_lower = query.lower()

        for entry in self._simple_memory:
            if memory_type and entry.get("type") != memory_type:
                continue
            content = entry.get("content", "")
            if query_lower in content.lower():
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def _normalize_search_results(self, results) -> List[Dict]:
        """Normalize mem0 search results to consistent format."""
        normalized = []
        if results is None:
            return normalized
        if isinstance(results, dict):
            if "results" in results:
                normalized = results.get("results") or []
            elif "memories" in results:
                normalized = results.get("memories") or []
            else:
                normalized = [results] if results else []
        elif isinstance(results, list):
            normalized = results
        # Filter out None entries
        return [r for r in normalized if r is not None]

    def get_all_memories(self, limit: int = 100, memory_type: str = None) -> List[Dict]:
        """
        Get all memories.

        Args:
            limit: Maximum number of memories
            memory_type: Filter by memory type

        Returns:
            List of memory entries
        """
        self._initialize()

        if self._memory:
            try:
                results = self._memory.get_all(
                    user_id=self.user_id,
                    agent_id=self.agent_id,
                    limit=limit
                )

                memories = self._normalize_search_results(results)

                if memory_type:
                    memories = [
                        m for m in memories 
                        if m and (m.get("metadata") or {}).get("type") == memory_type
                    ]

                return memories

            except Exception as e:
                logger.warning(f"Failed to get from mem0: {e}. Using simple storage.")

        # Fallback to simple storage
        filtered = self._simple_memory
        if memory_type:
            filtered = [e for e in filtered if e.get("type") == memory_type]
        return filtered[-limit:]

    def get_recent_memories(self, limit: int = 10, memory_type: str = None) -> List[Dict]:
        """
        Get recent memory entries.

        Args:
            limit: Maximum number of entries
            memory_type: Filter by memory type

        Returns:
            List of recent memory entries
        """
        memories = self.get_all_memories(limit=limit, memory_type=memory_type)
        # Sort by timestamp if available
        memories.sort(key=lambda x: x.get("metadata", {}).get("timestamp", x.get("timestamp", "")), reverse=True)
        return memories[:limit]

    def update_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Update an existing memory entry.

        Args:
            memory_id: ID of the memory to update
            content: New content
            metadata: New metadata

        Returns:
            True if successful
        """
        self._initialize()

        if self._memory:
            try:
                # mem0 Memory.update() only accepts memory_id and data
                self._memory.update(
                    memory_id=memory_id,
                    data=content
                )
                logger.info(f"Updated memory in mem0: {memory_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to update mem0: {e}")
                return False

        # Fallback to simple storage
        for entry in self._simple_memory:
            if entry.get("id") == memory_id:
                entry["content"] = content
                if metadata:
                    entry.update(metadata)
                entry["timestamp"] = datetime.now().isoformat()
                return True

        return False

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory entry.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if successful
        """
        self._initialize()

        if self._memory:
            try:
                self._memory.delete(memory_id=memory_id)
                logger.info(f"Deleted memory from mem0: {memory_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to delete from mem0: {e}")
                return False

        # Fallback to simple storage
        self._simple_memory = [e for e in self._simple_memory if e.get("id") != memory_id]
        return True

    def find_classification_by_filename(self, file_name: str) -> Optional[Dict]:
        """
        Find an existing classification for a file.

        Args:
            file_name: Name of the file

        Returns:
            Memory entry if found
        """
        self._initialize()

        # Search for the file classification
        results = self.search_memory(
            query=f"classification {file_name}",
            limit=10,
            memory_type="classification"
        )

        # Find exact match
        for r in results:
            metadata = r.get("metadata", {})
            if metadata.get("file_name") == file_name:
                return r

        # Fallback check in simple memory
        for entry in self._simple_memory:
            if entry.get("type") == "classification":
                if entry.get("file_name") == file_name or entry.get("metadata", {}).get("file_name") == file_name:
                    return entry

        return None

    def add_classification_result(
        self, 
        file_name: str, 
        category_id: int, 
        category_name: str,
        confidence: float = None,
        reasoning: str = None
    ) -> str:
        """
        Add a classification result to memory.

        Args:
            file_name: Name of the classified file
            category_id: Assigned category ID
            category_name: Assigned category name
            confidence: Classification confidence score
            reasoning: Reasoning for the classification

        Returns:
            Memory ID
        """
        content = f"Classified document '{file_name}' as category {category_id} ({category_name})"
        if reasoning:
            content += f". Reason: {reasoning}"

        metadata = {
            "file_name": file_name,
            "category_id": category_id,
            "category_name": category_name,
            "confidence": confidence,
            "reasoning": reasoning
        }

        return self.add_memory(content, metadata, memory_type="classification")

    def update_classification(
        self,
        file_name: str,
        category_id: int,
        category_name: str,
        confidence: float = None,
        reasoning: str = None
    ) -> str:
        """
        Update or add a classification result.

        Args:
            file_name: Name of the classified file
            category_id: Assigned category ID
            category_name: Assigned category name
            confidence: Classification confidence score
            reasoning: Reasoning for the classification

        Returns:
            Memory ID
        """
        # Check if classification exists
        existing = self.find_classification_by_filename(file_name)

        content = f"Classified document '{file_name}' as category {category_id} ({category_name})"
        if reasoning:
            content += f". Reason: {reasoning}"

        metadata = {
            "file_name": file_name,
            "category_id": category_id,
            "category_name": category_name,
            "confidence": confidence,
            "reasoning": reasoning,
            "type": "classification"
        }

        if existing:
            memory_id = existing.get("id") or existing.get("memory_id")
            if memory_id:
                if self.update_memory(memory_id, content, metadata):
                    logger.info(f"Updated classification for '{file_name}'")
                    return memory_id

        # Add new classification
        return self.add_memory(content, metadata, memory_type="classification")

    def add_document_summary(
        self,
        file_name: str,
        summary: str,
        keywords: List[str] = None,
        document_type: str = None,
        key_entities: Dict[str, Any] = None
    ) -> str:
        """
        Add a document summary to memory.

        Args:
            file_name: Name of the document
            summary: Document summary
            keywords: Extracted keywords
            document_type: Type of document
            key_entities: Extracted entities

        Returns:
            Memory ID
        """
        # Create rich content for the memory
        content_parts = [f"Document: {file_name}", f"Summary: {summary}"]
        if keywords:
            content_parts.append(f"Keywords: {', '.join(keywords)}")
        if document_type:
            content_parts.append(f"Document Type: {document_type}")

        content = "\n".join(content_parts)

        metadata = {
            "file_name": file_name,
            "summary": summary,
            "keywords": keywords or [],
            "document_type": document_type or "",
            "key_entities": key_entities or {}
        }

        return self.add_memory(content, metadata, memory_type="summary")

    def find_similar_documents(self, summary: str, limit: int = 5) -> List[Dict]:
        """
        Find documents with similar summaries.

        Args:
            summary: Summary to search for
            limit: Maximum results

        Returns:
            List of similar documents
        """
        return self.search_memory(summary, limit=limit, memory_type="summary")

    def get_classification_context(self, file_name: str = None) -> str:
        """
        Get classification context from memory for the agent.

        Args:
            file_name: Optional file name for context

        Returns:
            Context string
        """
        self._initialize()

        recent = self.get_recent_memories(limit=10, memory_type="classification")

        if not recent:
            return "No previous classification history available."

        context_parts = ["Previous classification history:"]

        for entry in recent:
            # Try to get content from different possible locations
            memory_text = entry.get("memory") or entry.get("content") or entry.get("text")

            if not memory_text:
                # Build from metadata
                metadata = entry.get("metadata", entry)
                fn = metadata.get("file_name", "unknown")
                cat_id = metadata.get("category_id", "?")
                cat_name = metadata.get("category_name", "")
                memory_text = f"Classified '{fn}' as category {cat_id} ({cat_name})"

            if memory_text:
                context_parts.append(f"- {memory_text}")

        return "\n".join(context_parts)

    def get_all_summaries(self, limit: int = 100) -> List[Dict]:
        """Get all document summaries."""
        return self.get_all_memories(limit=limit, memory_type="summary")

    def clear_memory(self) -> None:
        """Clear all memory entries."""
        self._initialize()

        if self._memory:
            try:
                self._memory.delete_all(user_id=self.user_id)
                logger.info("Cleared mem0 memory")
            except Exception as e:
                logger.warning(f"Failed to clear mem0: {e}")

        self._simple_memory = []
        logger.info("Cleared memory storage")

    def get_history(self, memory_id: str) -> List[Dict]:
        """
        Get history of changes for a memory entry.

        Args:
            memory_id: Memory ID

        Returns:
            List of history entries
        """
        self._initialize()

        if self._memory:
            try:
                history = self._memory.history(memory_id=memory_id)
                return history if isinstance(history, list) else []
            except Exception as e:
                logger.warning(f"Failed to get history from mem0: {e}")

        return []

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        self._initialize()

        stats = {
            "backend": "simple" if not self._memory else "mem0",
            "user_id": self.user_id,
            "agent_id": self.agent_id,
        }

        if self._memory:
            try:
                all_memories = self.get_all_memories(limit=1000)
                stats["total_memories"] = len(all_memories)

                # Count by type
                type_counts = {}
                for m in all_memories:
                    mem_type = m.get("metadata", {}).get("type", "unknown")
                    type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
                stats["memories_by_type"] = type_counts

            except Exception as e:
                logger.warning(f"Failed to get stats: {e}")
                stats["total_memories"] = "unknown"
        else:
            stats["total_memories"] = len(self._simple_memory)

        return stats

    # ==================== PROJECT-SCOPED MEMORY METHODS ====================
    
    def save_project_results(
        self,
        project_id: int,
        classifications: List[Dict],
        documents: List[Dict] = None,
        merged_pdf_path: str = None
    ) -> str:
        """
        Save complete classification results for a project.
        
        This stores all classification results keyed by project_id for later retrieval
        in the human-in-the-loop flow.
        
        Args:
            project_id: The project ID to use as identifier
            classifications: List of classification result dictionaries
            documents: List of original document data (optional)
            merged_pdf_path: Path to the merged PDF (optional)
            
        Returns:
            Memory ID
        """
        self._initialize()
        
        # Build a comprehensive content for semantic search
        content_parts = [f"Project {project_id} classification results:"]
        for cls in classifications:
            content_parts.append(
                f"- {cls.get('file_name', 'unknown')}: Category {cls.get('category_id')} ({cls.get('category_name', '')})"
            )
        content = "\n".join(content_parts)
        
        # Store full data in metadata
        metadata = {
            "project_id": project_id,
            "classifications": classifications,
            "documents": documents or [],
            "merged_pdf_path": merged_pdf_path,
            "total_documents": len(classifications),
            "type": "project_results",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if we already have results for this project, update if so
        existing = self.get_project_results(project_id)
        if existing:
            memory_id = existing.get("id") or existing.get("memory_id")
            if memory_id:
                # For simple memory, remove old and add new
                if not self._memory:
                    self._simple_memory = [
                        e for e in self._simple_memory 
                        if not (e.get("type") == "project_results" and e.get("project_id") == project_id)
                    ]
        
        return self.add_memory(content, metadata, memory_type="project_results")
    
    def get_project_results(self, project_id: int) -> Optional[Dict]:
        """
        Retrieve classification results for a specific project.
        
        Args:
            project_id: The project ID
            
        Returns:
            Dictionary containing project results or None if not found
        """
        self._initialize()
        
        # Search for project results
        results = self.search_memory(
            query=f"Project {project_id} classification results",
            limit=10,
            memory_type="project_results"
        )
        
        # Find exact match by project_id
        for r in results:
            metadata = r.get("metadata", {})
            if metadata.get("project_id") == project_id:
                return {
                    "id": r.get("id") or r.get("memory_id"),
                    "project_id": project_id,
                    "classifications": metadata.get("classifications", []),
                    "documents": metadata.get("documents", []),
                    "merged_pdf_path": metadata.get("merged_pdf_path"),
                    "total_documents": metadata.get("total_documents", 0),
                    "timestamp": metadata.get("timestamp")
                }
        
        # Fallback check in simple memory
        for entry in self._simple_memory:
            if entry.get("type") == "project_results" and entry.get("project_id") == project_id:
                return {
                    "id": entry.get("id"),
                    "project_id": project_id,
                    "classifications": entry.get("classifications", []),
                    "documents": entry.get("documents", []),
                    "merged_pdf_path": entry.get("merged_pdf_path"),
                    "total_documents": entry.get("total_documents", 0),
                    "timestamp": entry.get("timestamp")
                }
        
        return None
    
    def update_project_classification(
        self,
        project_id: int,
        file_id: int,
        new_category_id: int,
        new_category_name: str = None,
        new_category_english: str = None,
        reasoning: str = None
    ) -> bool:
        """
        Update a single file's classification within a project's results.
        
        Args:
            project_id: The project ID
            file_id: The file ID to update
            new_category_id: The new category ID
            new_category_name: The new German category name (optional)
            new_category_english: The new English category name (optional)
            reasoning: Reasoning for the change (optional)
            
        Returns:
            True if successful, False otherwise
        """
        self._initialize()
        
        project_results = self.get_project_results(project_id)
        if not project_results:
            logger.warning(f"No project results found for project {project_id}")
            return False
        
        classifications = project_results.get("classifications", [])
        updated = False
        
        for cls in classifications:
            if cls.get("file_id") == file_id:
                cls["category_id"] = new_category_id
                if new_category_name:
                    cls["category_name"] = new_category_name
                if new_category_english:
                    cls["category_english"] = new_category_english
                if reasoning:
                    cls["reasoning"] = reasoning
                    cls["reclassified"] = True
                    cls["reclassification_timestamp"] = datetime.now().isoformat()
                updated = True
                break
        
        if not updated:
            logger.warning(f"File {file_id} not found in project {project_id} classifications")
            return False
        
        # Re-save the project results with updated classifications
        self.save_project_results(
            project_id=project_id,
            classifications=classifications,
            documents=project_results.get("documents"),
            merged_pdf_path=project_results.get("merged_pdf_path")
        )
        
        logger.info(f"Updated file {file_id} classification to category {new_category_id} in project {project_id}")
        return True
    
    def update_project_classifications_bulk(
        self,
        project_id: int,
        updates: List[Dict]
    ) -> Dict[str, Any]:
        """
        Update multiple file classifications within a project's results.
        
        Args:
            project_id: The project ID
            updates: List of update dictionaries, each containing:
                - file_id: The file ID to update
                - new_category_id: The new category ID
                - new_category_name: The new German category name (optional)
                - new_category_english: The new English category name (optional)
                - reasoning: Reasoning for the change (optional)
                
        Returns:
            Dictionary with success count and failed updates
        """
        self._initialize()
        
        project_results = self.get_project_results(project_id)
        if not project_results:
            return {
                "success": False,
                "error": f"No project results found for project {project_id}",
                "updated_count": 0,
                "failed_updates": updates
            }
        
        classifications = project_results.get("classifications", [])
        
        # Build file_id to classification index mapping
        cls_by_file_id = {cls.get("file_id"): idx for idx, cls in enumerate(classifications)}
        
        updated_count = 0
        failed_updates = []
        
        for update in updates:
            file_id = update.get("file_id")
            
            if file_id not in cls_by_file_id:
                failed_updates.append({
                    "file_id": file_id,
                    "error": "File not found in project"
                })
                continue
            
            idx = cls_by_file_id[file_id]
            cls = classifications[idx]
            
            cls["category_id"] = update.get("new_category_id")
            if update.get("new_category_name"):
                cls["category_name"] = update["new_category_name"]
            if update.get("new_category_english"):
                cls["category_english"] = update["new_category_english"]
            if update.get("reasoning"):
                cls["reasoning"] = update["reasoning"]
            
            cls["reclassified"] = True
            cls["reclassification_timestamp"] = datetime.now().isoformat()
            updated_count += 1
        
        # Re-save the project results with updated classifications
        self.save_project_results(
            project_id=project_id,
            classifications=classifications,
            documents=project_results.get("documents"),
            merged_pdf_path=project_results.get("merged_pdf_path")
        )
        
        logger.info(f"Bulk updated {updated_count} classifications in project {project_id}")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "failed_updates": failed_updates
        }
    
    def get_project_classification_by_file(
        self,
        project_id: int,
        file_id: int
    ) -> Optional[Dict]:
        """
        Get a specific file's classification from project memory.
        
        Args:
            project_id: The project ID
            file_id: The file ID
            
        Returns:
            Classification dictionary or None if not found
        """
        project_results = self.get_project_results(project_id)
        if not project_results:
            return None
        
        for cls in project_results.get("classifications", []):
            if cls.get("file_id") == file_id:
                return cls
        
        return None


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def reset_memory_manager() -> None:
    """Reset the global memory manager instance."""
    global _memory_manager
    if _memory_manager is not None:
        _memory_manager.close()
    _memory_manager = None


def cleanup_memory_manager() -> None:
    """Cleanup function for atexit."""
    global _memory_manager
    if _memory_manager is not None:
        try:
            _memory_manager.close()
        except Exception:
            pass  # Ignore errors during shutdown
        _memory_manager = None


# Register global cleanup
atexit.register(cleanup_memory_manager)
 