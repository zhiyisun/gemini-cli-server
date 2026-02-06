"""Example: Error handling and recovery (OpenAI-compatible)."""
from gemini_cli_server.client import OpenAICompatibleClient, GeminiClientError


def main():
    """Demonstrate error handling strategies."""
    print("Error Handling Example")
    print("=" * 60)
    
    # Example 1: Handle connection errors
    print("\n1. Connection Error Handling")
    print("-" * 60)
    client = OpenAICompatibleClient("http://localhost:9999")  # Wrong port

    try:
        client.chat.completions.create(messages=[{"role": "user", "content": "Hello"}])
    except GeminiClientError as e:
        print(f"✗ Cannot connect to server: {e}")
        print("  → Make sure the server is running on the correct port")
    
    # Example 2: Handle server errors
    print("\n2. Server Error Handling")
    print("-" * 60)
    client = OpenAICompatibleClient("http://localhost:8000")
    
    try:
        # Try to chat with very long prompt that might cause issues
        extremely_long_prompt = "a" * 1000000  # 1MB of text
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": extremely_long_prompt}],
        )
        print(response)
    except GeminiClientError as e:
        print(f"✗ Client error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print(f"  Type: {type(e).__name__}")
    
    # Example 3: Handle malformed responses gracefully
    print("\n3. Graceful Degradation")
    print("-" * 60)
    
    try:
        stream = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello!"}],
            stream=True,
        )

        for chunk in stream:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                print(delta["content"], end="", flush=True)

        print("\n✓ Response completed successfully")
                
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error during chat: {e}")
        print("  Reset not required for per-request mode")
    
    # Example 4: Basic request
    print("\n4. Basic Request")
    print("-" * 60)

    try:
        response = client.chat.completions.create(messages=[{"role": "user", "content": "What is 2+2?"}])
        print(response["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Error handling examples complete!")


if __name__ == "__main__":
    main()
