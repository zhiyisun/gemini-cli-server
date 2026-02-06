"""Example: Session behavior with OpenAI-compatible client."""
from gemini_cli_server.client import OpenAICompatibleClient


def main():
    """Demonstrate stateless requests and manual history."""
    client = OpenAICompatibleClient("http://localhost:8000")
    
    print("Session Reset Example")
    print("=" * 60)
    
    print("Per-request mode is stateless unless you include history.")

    # First request
    print("\nFirst request:")
    print("You: Remember the number 42")
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Remember the number 42"}],
    )
    first_answer = response["choices"][0]["message"]["content"]
    print("Assistant:", first_answer)

    # Second request without history
    print("\nSecond request (no history):")
    print("You: What number did I ask you to remember?")
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "What number did I ask you to remember?"}],
    )
    print("Assistant:", response["choices"][0]["message"]["content"])

    # Third request with history
    print("\nThird request (with history):")
    history = [
        {"role": "user", "content": "Remember the number 42"},
        {"role": "assistant", "content": first_answer},
        {"role": "user", "content": "What number did I ask you to remember?"},
    ]
    response = client.chat.completions.create(messages=history)
    print("Assistant:", response["choices"][0]["message"]["content"])

    print("\n" + "=" * 60)
    print("Context only persists when you include it in the messages.")


if __name__ == "__main__":
    main()
