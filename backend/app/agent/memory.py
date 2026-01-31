"""
Memory Manager for Document Classification Agent

Uses mem0 with Qdrant vector database for:
- Storing agent execution history
- Tracking document classification context
- Enabling semantic search over past classifications
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import mem0, fall back to simple in-memory storage if not available
try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.warning("mem0 not installed. Using simple in-memory storage. Install with: pip install mem0ai")


class MemoryManager:
    """
    Memory manager for document classification agent.
    
    Uses mem0 with Qdrant for persistent memory storage and semantic search.
    Falls back to simple in-memory storage if mem0 is not available.
    """
    
    def __init__(
        self,
        qdrant_host: str = None,
        qdrant_port: int = None,
        collection_name: str = "document_classifications",
        user_id: str = "classifier_agent"
    ):
        """
        Initialize memory manager.
        
        Args:
            qdrant_host: Qdrant server host (default: localhost)
            qdrant_port: Qdrant server port (default: 6333)
            collection_name: Name of the Qdrant collection
            user_id: User ID for mem0 memory association
        """
        self.qdrant_host = qdrant_host or os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = qdrant_port or int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = collection_name
        self.user_id = user_id
        
        self._memory: Optional[Any] = None
        self._simple_memory: List[Dict] = []  # Fallback storage
        self._initialized = False
        
    def _initialize(self) -> None:
        """Initialize the memory backend."""
        if self._initialized:
            return
            
        if MEM0_AVAILABLE:
            try:
                # Configure mem0 with Qdrant and Azure OpenAI
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "host": self.qdrant_host,
                            "port": self.qdrant_port,
                            "collection_name": self.collection_name,
                        }
                    },
                    "llm": {
                        "provider": "azure_openai",
                        "config": {
                            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
                        }
                    },
                    "embedder": {
                        "provider": "azure_openai",
                        "config": {
                            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDINGS", "text-embedding-3-small"),
                            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
                        }
                    }
                }
                
                self._memory = Memory.from_config(config)
                logger.info(f"mem0 initialized with Qdrant at {self.qdrant_host}:{self.qdrant_port}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize mem0 with Qdrant: {e}. Using simple memory.")
                self._memory = None
        else:
            logger.info("Using simple in-memory storage (mem0 not available)")
            
        self._initialized = True
    
    def add_memory(
        self, 
        content: str, 
        metadata: Dict[str, Any] = None,
        memory_type: str = "classification"
    ) -> str:
        """
        Add a memory entry.
        
        Args:
            content: The memory content (e.g., classification result)
            metadata: Additional metadata
            memory_type: Type of memory (classification, context, etc.)
            
        Returns:
            Memory ID
        """
        self._initialize()
        
        memory_entry = {
            "content": content,
            "metadata": metadata or {},
            "type": memory_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if self._memory:
            try:
                result = self._memory.add(
                    content,
                    user_id=self.user_id,
                    metadata={
                        **memory_entry["metadata"],
                        "type": memory_type,
                        "timestamp": memory_entry["timestamp"]
                    }
                )
                memory_id = result.get("id", str(len(self._simple_memory)))
                logger.info(f"Added memory to mem0: {memory_id}")
                return memory_id
            except Exception as e:
                logger.warning(f"Failed to add to mem0: {e}. Using simple storage.")
        
        # Fallback to simple storage
        memory_id = f"mem_{len(self._simple_memory)}"
        memory_entry["id"] = memory_id
        self._simple_memory.append(memory_entry)
        logger.info(f"Added memory to simple storage: {memory_id}")
        return memory_id
    
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
                    limit=limit
                )
                
                # Filter by type if specified
                if memory_type:
                    results = [r for r in results if r.get("metadata", {}).get("type") == memory_type]
                
                return results
            except Exception as e:
                logger.warning(f"Failed to search mem0: {e}. Using simple search.")
        
        # Fallback to simple search (basic keyword matching)
        results = []
        query_lower = query.lower()
        
        for entry in self._simple_memory:
            if memory_type and entry.get("type") != memory_type:
                continue
            if query_lower in entry.get("content", "").lower():
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent_memories(self, limit: int = 10, memory_type: str = None) -> List[Dict]:
        """
        Get recent memory entries.
        
        Args:
            limit: Maximum number of entries
            memory_type: Filter by memory type
            
        Returns:
            List of recent memory entries
        """
        self._initialize()
        
        if self._memory:
            try:
                results = self._memory.get_all(user_id=self.user_id, limit=limit)
                
                if memory_type:
                    results = [r for r in results if r.get("metadata", {}).get("type") == memory_type]
                
                return results
            except Exception as e:
                logger.warning(f"Failed to get from mem0: {e}. Using simple storage.")
        
        # Fallback to simple storage
        filtered = self._simple_memory
        if memory_type:
            filtered = [e for e in filtered if e.get("type") == memory_type]
        
        return filtered[-limit:][::-1]  # Most recent first
    
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
        content = f"Classified '{file_name}' as category {category_id} ({category_name})"
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
    
    def get_classification_context(self, file_name: str = None) -> str:
        """
        Get classification context from memory for the agent.
        
        Args:
            file_name: Optional file name to search for related classifications
            
        Returns:
            Context string for the agent
        """
        self._initialize()
        
        recent = self.get_recent_memories(limit=10, memory_type="classification")
        
        if not recent:
            return "No previous classification history available."
        
        context_parts = ["Previous classification history:"]
        
        for entry in recent:
            metadata = entry.get("metadata", {})
            if isinstance(entry, dict) and "content" in entry:
                context_parts.append(f"- {entry['content']}")
            elif isinstance(entry, dict) and "memory" in entry:
                context_parts.append(f"- {entry['memory']}")
        
        return "\n".join(context_parts)
    
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
        logger.info("Cleared simple memory storage")


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
    _memory_manager = None
