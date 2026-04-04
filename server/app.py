"""Root-level OpenEnv server wrapper for repo-root validation."""

from finance_env.server.app import app, main as _finance_main


def main(host: str = "0.0.0.0", port: int = 8000):
    """Delegate to the packaged finance environment server entry point."""

    return _finance_main(host=host, port=port)


__all__ = ["app", "main"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.port == 8000:
        main()
    else:
        main(port=args.port)
