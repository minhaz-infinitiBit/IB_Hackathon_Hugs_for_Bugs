"""
LLM Client for Document Processing

Uses GraphBit's LlmClient with Azure LLM for document structuring, 
summarization, and keyword extraction.
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from graphbit import LlmConfig, LlmClient
from dotenv import load_dotenv

from .config import settings, LLMSettings
from .prompts import DocumentProcessingPrompts

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class DocumentAnalysisResult:
    """Result of document analysis by LLM."""
    success: bool = False
    structured_content: str = ""
    summary: str = ""
    keywords: List[str] = None
    document_type: str = ""
    key_entities: Dict[str, List[str]] = None
    error_message: str = ""
    raw_response: str = ""
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.key_entities is None:
            self.key_entities = {}


class DocumentLLMClient:
    """
    LLM Client for document processing operations.
    
    Uses GraphBit's LlmClient with Azure LLM for document analysis, 
    structuring, and summarization.
    
    Example:
        >>> client = DocumentLLMClient()
        >>> result = client.analyze_document(content, "document.pdf")
        >>> if result.success:
        ...     print(result.summary)
        ...     print(result.keywords)
    """
    
    def __init__(
        self,
        api_key: str = None,
        endpoint: str = None,
        deployment: str = None,
        api_version: str = None,
        max_tokens: int = None,
        temperature: float = None,
    ):
        """
        Initialize the DocumentLLMClient with GraphBit Azure LLM.
        
        Args:
            api_key: Azure LLM API key (defaults to env var AZURE_OPENAI_API_KEY)
            endpoint: Azure LLM endpoint (defaults to env var AZURE_OPENAI_ENDPOINT)
            deployment: Azure deployment name (defaults to env var AZURE_OPENAI_DEPLOYMENT)
            api_version: Azure API version (defaults to env var AZURE_OPENAI_API_VERSION)
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation
        """
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY") or settings.azure_api_key
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT") or settings.azure_endpoint
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT") or settings.azure_deployment
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        self.max_tokens = max_tokens or settings.max_tokens
        self.temperature = temperature or settings.temperature
        
        self._llm_config: Optional[LlmConfig] = None
        self._client: Optional[LlmClient] = None
        self._initialized = False
        
    def _initialize_client(self) -> None:
        """Initialize the GraphBit LlmClient with Azure LLM."""
        if self._initialized:
            return
            
        if not self.api_key:
            raise ValueError(
                "Azure LLM API key not provided. Set AZURE_OPENAI_API_KEY environment variable "
                "or pass api_key to constructor."
            )
        
        if not self.endpoint:
            raise ValueError(
                "Azure LLM endpoint not provided. Set AZURE_OPENAI_ENDPOINT environment variable "
                "or pass endpoint to constructor."
            )
            
        if not self.deployment:
            raise ValueError(
                "Azure LLM deployment not provided. Set AZURE_OPENAI_DEPLOYMENT environment variable "
                "or pass deployment to constructor."
            )
        
        logger.info(f"Initializing GraphBit LlmClient with Azure LLM deployment: {self.deployment}")
        
        # Create LLM config using GraphBit's azure_openai
        self._llm_config = LlmConfig.azure_openai(
            api_key=self.api_key,
            deployment_name=self.deployment,
            endpoint=self.endpoint,
            api_version=self.api_version
        )
        
        # Create the GraphBit LlmClient
        self._client = LlmClient(self._llm_config)
        self._initialized = True
        
        logger.info(f"GraphBit LlmClient initialized successfully with provider: {self._llm_config.provider()}")
    
    def analyze_document(
        self, 
        content: str, 
        file_name: str,
        simple_mode: bool = False
    ) -> DocumentAnalysisResult:
        """
        Analyze document content using LLM.
        
        Args:
            content: Extracted document content
            file_name: Name of the source file
            simple_mode: If True, use simpler prompt for faster processing
            
        Returns:
            DocumentAnalysisResult with structured content, summary, and keywords
        """
        result = DocumentAnalysisResult()
        
        try:
            # Initialize client if needed
            self._initialize_client()
            
            # Get appropriate prompt
            if simple_mode:
                prompt = DocumentProcessingPrompts.get_simple_summary_prompt(content)
            else:
                prompt = DocumentProcessingPrompts.get_structure_and_summarize_prompt(content, file_name)
            
            logger.info(f"Sending document to LLM for analysis: {file_name}")
            
            # Call the GraphBit LlmClient
            response = self._client.complete(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # LlmClient.complete() returns the response text directly
            result.raw_response = response
            
            # Parse the JSON response
            parsed = self._parse_llm_response(response)
            
            if parsed:
                result.success = True
                result.structured_content = parsed.get("structured_content", content)
                result.summary = parsed.get("summary", "")
                result.keywords = parsed.get("keywords", [])
                result.document_type = parsed.get("document_type", "Unknown")
                result.key_entities = parsed.get("key_entities", {})
                
                logger.info(f"Document analysis complete. Type: {result.document_type}")
            else:
                result.error_message = "Failed to parse LLM response as JSON"
                logger.warning(result.error_message)
                
        except Exception as e:
            result.error_message = f"LLM analysis failed: {str(e)}"
            logger.exception(result.error_message)
        
        return result
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse the LLM response as JSON.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed dictionary or None if parsing fails
        """
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from the response
        try:
            # Look for JSON block in markdown
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    return json.loads(json_str)
            
            # Look for JSON block without language specifier
            if "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    return json.loads(json_str)
            
            # Try to find JSON object in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
                
        except json.JSONDecodeError:
            pass
        
        logger.warning(f"Could not parse LLM response as JSON: {response[:200]}...")
        return None
    
    def get_summary_only(self, content: str) -> tuple:
        """
        Get just summary and keywords (faster, simpler call).
        
        Args:
            content: Document content
            
        Returns:
            Tuple of (summary, keywords, document_type)
        """
        result = self.analyze_document(content, "document", simple_mode=True)
        
        if result.success:
            return result.summary, result.keywords, result.document_type
        else:
            return "", [], "Unknown"


# Convenience function
def analyze_document_content(
    content: str, 
    file_name: str,
    api_key: str = None,
    endpoint: str = None,
    deployment: str = None
) -> DocumentAnalysisResult:
    """
    Convenience function to analyze document content.
    
    Args:
        content: Extracted document content
        file_name: Name of the source file
        api_key: Optional Azure LLM API key
        endpoint: Optional Azure LLM endpoint
        deployment: Optional Azure deployment name
        
    Returns:
        DocumentAnalysisResult
    """
    client = DocumentLLMClient(api_key=api_key, endpoint=endpoint, deployment=deployment)
    return client.analyze_document(content, file_name)
