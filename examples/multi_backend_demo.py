#!/usr/bin/env python3
"""
Example demonstrating how to use the AI CLI Server with different backends.

This example shows how to:
1. Use Gemini CLI backend
2. Use Qwen Code backend
3. Switch between them easily

Note: Make sure you have the appropriate backend built and authenticated
before running this example.
"""

import os
from ai_cli_server.client import GeminiClient


def demo_cli(cli_name: str, base_url: str = "http://localhost:8000"):
    """
    Demonstrate using the AI CLI server.
    
    Args:
        cli_name: Name of the CLI backend (for display)
        base_url: Server URL
    """
    print(f"\n{'='*60}")
    print(f"Testing with {cli_name}")
    print(f"{'='*60}\n")
    
    client = GeminiClient(base_url=base_url)
    
    # Check health
    health = client.health()
    print(f"Server status: {health['status']}")
    if health.get('session_id'):
        print(f"Session ID: {health['session_id']}")
    
    # Send a simple prompt
    prompt = "Write a haiku about coding"
    print(f"\nPrompt: {prompt}\n")
    print("Response:")
    print("-" * 40)
    
    full_response = []
    for event in client.chat(prompt):
        # Handle Gemini format: type="message", role="assistant", content field
        if event.get("type") == "message" and event.get("role") == "assistant":
            content = event.get("content", "")
            print(content, end="", flush=True)
            full_response.append(content)
        # Handle Qwen format: type="assistant", message.content
        elif event.get("type") == "assistant":
            if isinstance(event.get("message"), dict):
                content = ""
                # Extract text from message content
                msg_content = event.get("message", {}).get("content", [])
                if isinstance(msg_content, list):
                    for item in msg_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content = item.get("text", "")
                            break
                else:
                    content = str(msg_content)
                if content:
                    print(content, end="", flush=True)
                    full_response.append(content)
        # Handle result: works for both Gemini and Qwen
        elif event.get("type") == "result":
            print("\n" + "-" * 40)
            print(f"\nStats:")
            # Gemini uses duration_ms, Qwen uses duration_ms as well
            duration = event.get('duration_ms', event.get('duration_api_ms', 0))
            print(f"  Duration: {duration}ms")
            # Gemini has stats field, Qwen has it too
            if 'stats' in event:
                stats = event['stats']
                print(f"  Input tokens: {stats.get('input_tokens', 0)}")
                print(f"  Output tokens: {stats.get('output_tokens', 0)}")
    
    print("\n")


def main():
    """Main function."""
    print("=" * 60)
    print("AI CLI Server - Multi-Backend Demo")
    print("=" * 60)
    print("\nThis demo requires the server to be running.")
    print("Start the server in another terminal with:")
    print("  For Gemini: python -m ai_cli_server.server")
    print("  For Qwen:   CLI_TYPE=qwen python -m ai_cli_server.server")
    print()
    
    # Ask which backend to test
    backend = input("Which backend to test? (gemini/qwen/both) [gemini]: ").strip().lower()
    if not backend:
        backend = "gemini"
    
    if backend in ("gemini", "both"):
        print("\n📝 Make sure Gemini CLI server is running!")
        input("Press Enter when ready...")
        demo_cli("Gemini CLI")
    
    if backend in ("qwen", "both"):
        if backend == "both":
            print("\n" + "=" * 60)
            print("Now testing Qwen Code...")
            print("=" * 60)
            print("\n📝 Restart the server with: CLI_TYPE=qwen python -m ai_cli_server.server")
            input("Press Enter when ready...")
        demo_cli("Qwen Code")
    
    print("\n✅ Demo completed!")
    print("\nKey takeaways:")
    print("  • Both CLIs use the same API")
    print("  • Switch backends via CLI_TYPE environment variable")
    print("  • Client code remains unchanged")
    print("  • Perfect for comparing different AI models")


if __name__ == "__main__":
    main()
