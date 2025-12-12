"""
Test script for streaming implementation in MAL.

This script tests both streaming and non-streaming modes to verify
the implementation works correctly.
"""

import asyncio

from tapps_agents.core.config import MALConfig
from tapps_agents.core.mal import MAL


async def test_streaming():
    """Test streaming mode with a large prompt"""
    print("Testing streaming mode...")

    config = MALConfig(
        use_streaming=True,
        streaming_threshold=100,  # Low threshold for testing
    )
    mal = MAL(config=config)

    # Large prompt to trigger streaming
    large_prompt = "Write a Python function to calculate fibonacci numbers. " * 20

    try:
        response = await mal.generate(prompt=large_prompt, model="qwen2.5-coder:7b")
        print(f"✅ Streaming test passed! Response length: {len(response)} chars")
        print(f"Response preview: {response[:100]}...")
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
    finally:
        await mal.close()


async def test_non_streaming():
    """Test non-streaming mode with a small prompt"""
    print("\nTesting non-streaming mode...")

    config = MALConfig(use_streaming=False)
    mal = MAL(config=config)

    # Small prompt
    small_prompt = "Write a hello world function in Python."

    try:
        response = await mal.generate(prompt=small_prompt, model="qwen2.5-coder:7b")
        print(f"✅ Non-streaming test passed! Response length: {len(response)} chars")
        print(f"Response preview: {response[:100]}...")
    except Exception as e:
        print(f"❌ Non-streaming test failed: {e}")
    finally:
        await mal.close()


async def test_progress_callback():
    """Test streaming with progress callback"""
    print("\nTesting streaming with progress callback...")

    config = MALConfig(use_streaming=True, streaming_threshold=100)
    mal = MAL(config=config)

    chunks_received = []

    def progress_callback(chunk: str):
        chunks_received.append(chunk)
        print(
            f"📦 Received chunk: {len(chunk)} chars (total chunks: {len(chunks_received)})"
        )

    large_prompt = "Write a Python class for a simple calculator. " * 15

    try:
        response = await mal.generate(
            prompt=large_prompt,
            model="qwen2.5-coder:7b",
            progress_callback=progress_callback,
        )
        print("✅ Progress callback test passed!")
        print(f"Total chunks received: {len(chunks_received)}")
        print(f"Total response length: {len(response)} chars")
    except Exception as e:
        print(f"❌ Progress callback test failed: {e}")
    finally:
        await mal.close()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("MAL Streaming Implementation Tests")
    print("=" * 60)

    await test_non_streaming()
    await test_streaming()
    await test_progress_callback()

    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
