"""Terminal menu for the agent debate project."""

from __future__ import annotations

from pathlib import Path

from agent_debate.config import load_config
from agent_debate.llm.factory import build_llm_client, provider_name, provider_names_by_role
from agent_debate.llm.mock_client import MockLLMClient
from agent_debate.logging_utils.debate_logger import DebateLogger
from agent_debate.orchestration.debate_orchestrator import DebateOrchestrator

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "configs" / "debate_config.yaml"


def run_debate(config_path: Path = DEFAULT_CONFIG, topic: str | None = None) -> None:
    """Run one configured debate."""

    _suppress_provider_noise()
    _load_dotenv_if_available()
    config = load_config(config_path)
    config = config.with_topic(topic or _ask_topic(config.topic))
    llm = build_llm_client(config, "judge")
    if isinstance(llm, MockLLMClient):
        print("\nJudge provider key not found. Running the judge in mock mode for a dry run.")
        print("Add GEMINI_API_KEY, GROQ_API_KEY, and OPENAI_API_KEY to .env for a real debate.\n")
    else:
        providers = provider_names_by_role(config)
        provider_text = ", ".join(f"{role}={provider}" for role, provider in providers.items())
        print(f"\nUsing LLM providers: {provider_text}\n")
    try:
        decision = DebateOrchestrator(config, llm).run()
    except RuntimeError as exc:
        print(f"\nDebate failed: {exc}")
        print("Check your API quota/billing or enable mock fallback in the config.")
        return
    if decision.metadata.get("provider_fallback") == "mock":
        fallback_error = decision.metadata.get("provider_error", "provider unavailable")
        failed_provider = _provider_from_error(fallback_error) or provider_name(config)
        print(f"\n{failed_provider.title()} failed, so this run used mock fallback.")
        print(f"Provider error: {_short_error(fallback_error)}")
    print("\nFinal decision:\n")
    print(decision.content)


def show_last_transcript(config_path: Path = DEFAULT_CONFIG) -> None:
    """Print the most recent transcript."""

    config = load_config(config_path)
    print(DebateLogger(config).last_transcript())


def save_last_transcript(config_path: Path = DEFAULT_CONFIG) -> Path:
    """Save the latest transcript as a timestamped file and print its path."""

    config = load_config(config_path)
    saved_path = DebateLogger(config).export_transcript()
    print(f"Transcript saved to: {saved_path}")
    return saved_path


def validate_config(config_path: Path = DEFAULT_CONFIG) -> None:
    """Validate and summarize the config."""

    config = load_config(config_path)
    print(f"Config OK: {config.topic} ({config.turns_per_side * 2} total pings)")


def _ask_topic(default_topic: str) -> str:
    """Ask the user to choose the debate topic before starting."""

    print("\nChoose a debate topic first.")
    print(f"Press Enter to use the default: {default_topic}")
    topic = input("Topic: ").strip()
    return topic or default_topic


def main() -> None:
    """Keyboard-operated terminal menu."""

    while True:
        print("\nAI Agent Debate")
        print("1. Run debate")
        print("2. Show last transcript")
        print("3. Save transcript")
        print("4. Validate config")
        print("5. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            run_debate()
        elif choice == "2":
            show_last_transcript()
        elif choice == "3":
            try:
                save_last_transcript()
            except FileNotFoundError as exc:
                print(exc)
        elif choice == "4":
            validate_config()
        elif choice == "5":
            return
        else:
            print("Invalid choice.")


def _load_dotenv_if_available() -> None:
    """Load .env when python-dotenv is installed; otherwise continue normally."""

    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv()


def _suppress_provider_noise() -> None:
    """Hide third-party runtime warnings that clutter the terminal menu."""

    import warnings

    warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\..*")


def _provider_from_error(error: str) -> str | None:
    lowered = error.lower()
    if "gemini" in lowered:
        return "gemini"
    if "groq" in lowered:
        return "groq"
    if "mistral" in lowered:
        return "mistral"
    if "openai" in lowered:
        return "openai"
    return None


def _short_error(error: str, limit: int = 260) -> str:
    return error if len(error) <= limit else f"{error[:limit].rstrip()}..."


if __name__ == "__main__":
    main()
