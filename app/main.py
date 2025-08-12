"""Entry point for the translator application."""
from . import settings


def main() -> None:
    """Run a simple demo using the configured settings."""
    print("Translator app started")
    print(f"Model path: {settings.MODEL_PATH}")


if __name__ == "__main__":
    main()
