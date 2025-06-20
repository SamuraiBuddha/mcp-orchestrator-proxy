"""Core orchestration logic with semantic routing"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class MCPOrchestrator:
    """Intelligent router for MCP tools using semantic embeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize with embedding model and registry"""
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Load registry
        registry_path = Path(__file__).parent.parent / "config" / "registry.json"
        with open(registry_path, 'r') as f:
            self.registry = json.load(f)
        
        # Pre-compute embeddings for all tools
        self._build_tool_index()
    
    def _build_tool_index(self):
        """Build semantic index of all available tools"""
        self.tool_index = []
        self.tool_embeddings = []
        
        for mcp_name, mcp_config in self.registry["mcps"].items():
            # MCP-level description
            mcp_desc = mcp_config.get("description", "")
            
            for tool_name, tool_config in mcp_config.get("tools", {}).items():
                # Combine all searchable text
                search_text = " ".join([
                    tool_name,
                    tool_config.get("description", ""),
                    mcp_desc,
                    " ".join(tool_config.get("keywords", [])),
                    " ".join(mcp_config.get("keywords", []))
                ])
                
                # Store tool info
                self.tool_index.append({
                    "mcp": mcp_name,
                    "tool": tool_name,
                    "description": tool_config.get("description", ""),
                    "search_text": search_text
                })
                
                # Compute embedding
                embedding = self.model.encode(search_text)
                self.tool_embeddings.append(embedding)
        
        # Convert to numpy array for efficient similarity computation
        self.tool_embeddings = np.array(self.tool_embeddings)
        logger.info(f"Indexed {len(self.tool_index)} tools across {len(self.registry['mcps'])} MCPs")
    
    async def find_tools(self, query: str, threshold: float = 0.5, top_k: int = 10) -> List[Dict[str, Any]]:
        """Find tools matching a natural language query"""
        # Encode query
        query_embedding = self.model.encode(query)
        
        # Compute similarities
        similarities = cosine_similarity([query_embedding], self.tool_embeddings)[0]
        
        # Find matches above threshold
        matches = []
        for idx, score in enumerate(similarities):
            if score >= threshold:
                tool_info = self.tool_index[idx].copy()
                tool_info["confidence"] = float(score)
                matches.append(tool_info)
        
        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return matches[:top_k]
    
    async def list_all_capabilities(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """List all available capabilities, optionally filtered by category"""
        capabilities = {}
        
        for mcp_name, mcp_config in self.registry["mcps"].items():
            # Filter by category if specified
            if category and category not in mcp_config.get("categories", []):
                continue
            
            mcp_caps = []
            for tool_name, tool_config in mcp_config.get("tools", {}).items():
                cap_desc = f"{tool_name}: {tool_config.get('description', 'No description')}"
                mcp_caps.append(cap_desc)
            
            if mcp_caps:
                capabilities[mcp_name] = mcp_caps
        
        return capabilities
    
    def get_mcp_info(self, mcp_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific MCP"""
        return self.registry["mcps"].get(mcp_name, {})
    
    def get_tool_info(self, mcp_name: str, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool"""
        mcp_config = self.registry["mcps"].get(mcp_name, {})
        return mcp_config.get("tools", {}).get(tool_name, {})