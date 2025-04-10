from __future__ import annotations
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import os

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai import Agent, RunContext

load_dotenv()

class AgentService:
    def __init__(self):
        self.agents = {}
        self.mcp_servers = []
        self.primary_agent = None
        self.initialized = False

    async def initialize(self):
        """Initialize all agents and MCP servers"""
        if self.initialized:
            return

        model = self._get_model()
        
        # Initialize MCP servers
        self.mcp_servers = [
            MCPServerStdio('npx', ['-y', '@modelcontextprotocol/server-brave-search'],
                env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}),
            MCPServerStdio('npx', ['-y', '@modelcontextprotocol/server-filesystem', 
                os.getenv("LOCAL_FILE_DIR")]),
            MCPServerStdio('npx', ['-y', '@modelcontextprotocol/server-github'],
                env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN")})
        ]

        # Initialize agents
        self.agents = {
            "brave": Agent(model,
                system_prompt="Brave Search specialist for web searches",
                mcp_servers=[self.mcp_servers[0]]),
            "filesystem": Agent(model,
                system_prompt="Filesystem specialist for file operations",
                mcp_servers=[self.mcp_servers[1]]),
            "github": Agent(model,
                system_prompt="GitHub specialist for repository operations", 
                mcp_servers=[self.mcp_servers[2]])
        }

        # Initialize primary agent
        self.primary_agent = Agent(model,
            system_prompt="Primary orchestration agent that delegates to specialists")

        # Register tools
        self._register_tools()
        self.initialized = True

    def _get_model(self):
        """Helper to get LLM model configuration"""
        llm = os.getenv('MODEL_CHOICE', 'gpt-4o-mini')
        base_url = os.getenv('BASE_URL', 'https://api.openai.com/v1')
        api_key = os.getenv('LLM_API_KEY', 'no-api-key-provided')
        return OpenAIModel(llm, provider=OpenAIProvider(base_url=base_url, api_key=api_key))

    def _register_tools(self):
        """Register all agent tools with the primary agent"""
        
        @self.primary_agent.tool_plain
        async def use_brave_search(query: str) -> dict[str, str]:
            result = await self.agents["brave"].run(query)
            return {"result": result.data}

        @self.primary_agent.tool_plain
        async def use_filesystem(query: str) -> dict[str, str]:
            result = await self.agents["filesystem"].run(query)
            return {"result": result.data}

        @self.primary_agent.tool_plain
        async def use_github(query: str) -> dict[str, str]:
            result = await self.agents["github"].run(query)
            return {"result": result.data}

    async def process_query(self, query: str, message_history: Optional[List[Dict]] = None):
        """Process a user query using the agent system"""
        if not self.initialized:
            await self.initialize()

        async with AsyncExitStack() as stack:
            # Start all MCP servers
            for agent in self.agents.values():
                await stack.enter_async_context(agent.run_mcp_servers())

            # Run the query
            result = await self.primary_agent.run(query, message_history=message_history or [])
            return result.data

# Global service instance
service = AgentService()
