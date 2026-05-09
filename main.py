# main.py — Entry point for MiniFIM
# Launch the File Integrity Monitor application.

from app import MiniFIMApp


def main():
    app = MiniFIMApp()
    app.mainloop()


if __name__ == "__main__":
    main()