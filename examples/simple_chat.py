"""Example: Simple chat interaction (OpenAI-compatible)."""
from ai_cli_server.client import OpenAICompatibleClient


def main():
    """Run a simple chat example."""
    client = OpenAICompatibleClient("http://localhost:8000")

    prompt = "Explain what HTTP SSE is in one sentence"
    print(f"Sending prompt: '{prompt}'")
    print("-" * 60)

    stream = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        delta = chunk["choices"][0]["delta"]
        if "content" in delta:
            print(delta["content"], end="", flush=True)

    print("\n")


if __name__ == "__main__":
    main()
