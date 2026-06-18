import sys
import runpy

def main():
    if len(sys.argv) < 2:
        print("Syntiox MCP CLI")
        print("Usage: syntiox-mcp <server_name> [args]")
        print("Available servers:")
        print("  System:   system, clipboard, file, reminder, screenshot")
        print("  Web:      search, sri-news, weather")
        print("  Advanced: master-router, python-sandbox")
        print("  Google:   gmail, calendar, drive, docs, sheets, slides, tasks, forms, google-news")
        sys.exit(1)

    server = sys.argv[1].lower()
    
    mapping = {
        "system": "system_mcp",
        "clipboard": "clipboard_mcp",
        "file": "file_mcp",
        "reminder": "reminder_mcp",
        "screenshot": "screenshot_mcp",
        "search": "search_mcp",
        "sri-news": "sri_news_mcp",
        "weather": "weather_mcp",
        "python-sandbox": "python_sandbox_mcp",
        "master-router": "master_router",
        "gmail": "google.gmail_handlers",
        "calendar": "google.calendar_handlers",
        "drive": "google.drive_handlers",
        "docs": "google.docs_handlers",
        "sheets": "google.sheets_handlers",
        "slides": "google.slides_handlers",
        "tasks": "google.tasks_handlers",
        "forms": "google.forms_handlers",
        "google-news": "google.google_news_handlers"
    }

    if server not in mapping:
        print(f"Unknown server: {server}")
        print("Available servers: " + ", ".join(mapping.keys()))
        sys.exit(1)

    module_name = mapping[server]
    
    # Modify sys.argv so the underlying FastMCP argparse doesn't see our server name argument
    sys.argv.pop(1)
    sys.argv[0] = module_name
    
    try:
        runpy.run_module(module_name, run_name="__main__", alter_sys=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error running {server}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
