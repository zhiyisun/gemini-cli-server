"""Example: Monitoring tool execution (OpenAI-compatible)."""
from ai_cli_server.client import OpenAICompatibleClient


def main():
    """Monitor tool execution in real-time."""
    client = OpenAICompatibleClient("http://localhost:8000")
    
    print("Tool Execution Monitoring Example")
    print("=" * 60)
    
    # Ask a question that might trigger tool use
    prompt = "What files are in the current directory?"
    print(f"\nPrompt: {prompt}")
    print("-" * 60)
    
    print("\nNote: The OpenAI-compatible API does not expose tool_use/tool_result events.")
    print("For tool monitoring, use the GeminiClient event stream instead.")
    print("\nStreaming response:")

    stream = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        delta = chunk["choices"][0]["delta"]
        if "content" in delta:
            print(delta["content"], end="", flush=True)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
