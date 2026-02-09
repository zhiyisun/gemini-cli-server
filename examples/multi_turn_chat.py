"""Example: Multi-turn conversation (OpenAI-compatible)."""
from ai_cli_server.client import OpenAICompatibleClient


def stream_response(client, messages):
    """Stream a response and return the assistant text."""
    full_response = ""
    stream = client.chat.completions.create(messages=messages, stream=True)
    for chunk in stream:
        delta = chunk["choices"][0]["delta"]
        if "content" in delta:
            text = delta["content"]
            print(text, end="", flush=True)
            full_response += text
    print("\n")
    return full_response


def main():
    """Run a multi-turn conversation example."""
    client = OpenAICompatibleClient("http://localhost:8000")
    
    print("Multi-turn conversation example")
    print("=" * 60)
    
    history = []

    # Turn 1
    user_1 = "What is quantum computing?"
    print(f"\nYou: {user_1}")
    print("Assistant: ", end="")
    history.append({"role": "user", "content": user_1})
    assistant_1 = stream_response(client, history)
    history.append({"role": "assistant", "content": assistant_1})

    # Turn 2
    user_2 = "Can you give a simple analogy?"
    print(f"You: {user_2}")
    print("Assistant: ", end="")
    history.append({"role": "user", "content": user_2})
    assistant_2 = stream_response(client, history)
    history.append({"role": "assistant", "content": assistant_2})

    # Turn 3
    user_3 = "What are some real-world applications?"
    print(f"You: {user_3}")
    print("Assistant: ", end="")
    history.append({"role": "user", "content": user_3})
    assistant_3 = stream_response(client, history)
    history.append({"role": "assistant", "content": assistant_3})
    
    print("\n" + "=" * 60)
    print("Conversation complete!")


if __name__ == "__main__":
    main()
