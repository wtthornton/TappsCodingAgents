"""Test Ollama connection for TappsCodingAgents"""

import asyncio
from tapps_agents.core.mal import MAL
from tapps_agents.core.config import MALConfig

async def test_connection():
    """Test if Ollama is accessible"""
    print("Testing Ollama connection...")
    
    # Create default config
    config = MALConfig()
    print(f"Ollama URL: {config.ollama_url}")
    print(f"Default Model: {config.default_model}")
    print(f"Default Provider: {config.default_provider}")
    
    # Create MAL instance
    mal = MAL(config=config)
    
    try:
        # Test with a simple prompt
        print("\nSending test prompt to Ollama...")
        response = await mal.generate(
            prompt="Say 'Hello, TappsCodingAgents!' in one sentence.",
            model="qwen2.5-coder:7b"
        )
        print(f"\n✅ SUCCESS! Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await mal.client.aclose()

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)

