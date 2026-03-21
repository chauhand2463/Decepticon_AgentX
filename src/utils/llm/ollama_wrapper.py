from typing import Any, List, Optional, Union, Dict
import json
import re
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, SystemMessage
from langchain_ollama import ChatOllama
import logging

logger = logging.getLogger(__name__)

def _extract_messages(input: Any) -> Any:
    if isinstance(input, dict):
        return input.get("messages", input)
    return input

class OllamaToolWrapper:
    def __init__(self, llm: ChatOllama):
        self.llm = llm
        self.name = getattr(llm, "model", "Ollama Model")

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> Any:
        self.tools = tools
        try:
            return self.llm.bind_tools(tools, **kwargs)
        except Exception as e:
            logger.warning(f"Native tool binding failed for {self.name}: {e}")
            return self

    def __call__(self, input, config=None, **kwargs):
        input = _extract_messages(input)
        safe_config = config if isinstance(config, dict) else {}
        return self.invoke(input, config=safe_config, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.llm, name)

    async def ainvoke(self, input, config=None, **kwargs):
        input = _extract_messages(input)
        safe_config = config if isinstance(config, dict) else {}
        try:
            return await self.llm.ainvoke(input, config=safe_config, **kwargs)
        except Exception as e:
            error_str = str(e)
            if "does not support tools" in error_str or "400" in error_str:
                logger.warning(f"Falling back to text-prompting for {self.name}")
                return await self._fallback_ainvoke(input, config=safe_config, **kwargs)
            else:
                logger.error(f"Unexpected error: {error_str}")
                raise e

    async def _fallback_ainvoke(self, input, config=None, **kwargs):
        input = _extract_messages(input)
        if not hasattr(self, "tools") or not self.tools:
            safe_config = config if isinstance(config, dict) else {}
            return await self.llm.ainvoke(input, config=safe_config, **kwargs)
        tool_desc = []
        for tool in self.tools:
            if hasattr(tool, "name"):
                tool_desc.append(f"- {tool.name}: {getattr(tool, 'description', '')} (Args: {json.dumps(getattr(tool, 'args', {}))})")
        system_instruction = f"Use tools via JSON:\n{chr(10).join(tool_desc)}\nFormat: ```json\n{{\"action\": \"tool_name\", \"action_input\": {{\"arg\": \"val\"}}}}\n```"
        messages = [SystemMessage(content=system_instruction)] + (list(input) if not isinstance(input, str) else [AIMessage(content=input)])
        safe_config = config if isinstance(config, dict) else {}
        response = await self.llm.ainvoke(messages, config=safe_config)
        json_match = re.search(r"```json\s*(.*?)\s*```", response.content, re.DOTALL)
        if json_match:
            try:
                tool_data = json.loads(json_match.group(1))
                action = tool_data.get("action")
                args = tool_data.get("action_input", {})
                if action:
                    return AIMessage(content=response.content, tool_calls=[{"name": action, "args": args, "id": f"call_{re.sub(r'[^a-zA-Z0-9]', '', action)}"}])
            except Exception as parse_err:
                logger.error(f"Failed to parse fallback tool call: {parse_err}")
        return response

    def invoke(self, input, config=None, **kwargs):
        input = _extract_messages(input)
        safe_config = config if isinstance(config, dict) else {}
        return self.llm.invoke(input, config=safe_config, **kwargs)
