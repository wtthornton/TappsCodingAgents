"""Quick script to check service availability for Phase 2 validation."""
import os
import httpx

print("=== Service Availability Check ===\n")

# Check Ollama
ollama_available = False
try:
    response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
    ollama_available = response.status_code == 200
except Exception:
    pass

print(f"Ollama: {'[OK] Available' if ollama_available else '[X] Not available'}")

# Check API Keys
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
context7_key = os.getenv("CONTEXT7_API_KEY")

print(f"Anthropic API Key: {'[OK] Set' if anthropic_key else '[X] Not set'}")
print(f"OpenAI API Key: {'[OK] Set' if openai_key else '[X] Not set'}")
print(f"Context7 API Key: {'[OK] Set' if context7_key else '[X] Not set'}")

# Summary
has_llm = ollama_available or bool(anthropic_key) or bool(openai_key)
print(f"\nLLM Service Available: {'[OK] Yes' if has_llm else '[X] No'}")
print(f"Context7 Available: {'[OK] Yes' if context7_key else '[X] No'}")

