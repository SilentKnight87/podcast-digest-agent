"""
Test basic ADK agent to understand real patterns.
"""
from google.adk.agents import Agent
from google.adk.tools import google_search

# Test basic agent creation (from real documentation)
test_agent = Agent(
    name="test_agent",
    model="gemini-2.5-flash-preview-04-17",
    instruction="You are a helpful assistant.",
    description="Test agent to verify ADK patterns",
    tools=[google_search],  # Built-in tool
)

print(f"✅ Created agent: {test_agent.name}")
print(f"✅ Model: {test_agent.model}")
print(f"✅ Tools: {len(test_agent.tools)}")
