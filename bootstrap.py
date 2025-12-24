from pathlib import Path
import sqlite3

WORKSPACE = Path("workspace")
DB_PATH = Path("assistant.db")

def main():
    WORKSPACE.mkdir(exist_ok=True)

    if not DB_PATH.exists():
        con = sqlite3.connect(DB_PATH)
        con.close()
        print("Initialized database.")
    else:
        print("Database already exists.")

    print("\nAssistant ready.")
    print("Open: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
