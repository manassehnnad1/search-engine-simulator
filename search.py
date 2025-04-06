import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import requests
from bs4 import BeautifulSoup
import difflib
from urllib.parse import urljoin
import threading
import webview  # For embedding a real browser view

class SearchProgram:
    def __init__(self, root):
        self.root = root
        self.search_history = {}  # Tracks search term counts
        self.results = []         # Stores current search results

        # Configure styling
        root.configure(bg="#f0f0f0")
        self.default_font = ("Helvetica", 11)

        # Entry Frame for search input
        self.entry_frame = tk.Frame(root, bg="#f0f0f0")
        self.entry_label = tk.Label(self.entry_frame, text='Search Term:', font=("Helvetica", 12), bg="#f0f0f0")
        self.entry_label.pack(side=tk.LEFT, padx=5)
        self.entry_field = tk.Entry(self.entry_frame, width=50, font=self.default_font)
        self.entry_field.pack(side=tk.LEFT, padx=5)
        self.search_button = tk.Button(self.entry_frame, text='Search', font=self.default_font, command=self.start_search)
        self.search_button.pack(side=tk.LEFT, padx=5)
        self.entry_frame.pack(pady=10)

        # Loader Frame (hidden by default)
        self.loader_frame = tk.Frame(root, bg="#f0f0f0")
        self.loader_label = tk.Label(self.loader_frame, text="Loading...", font=("Helvetica", 12), bg="#f0f0f0", fg="green")
        self.loader_label.pack()
        self.loader_frame.pack_forget()

        # Results Frame for displaying search results and history
        self.result_frame = tk.Frame(root, bg="#f0f0f0")
        self.result_label = tk.Label(self.result_frame, text='Search Results:', font=("Helvetica", 12, "bold"), bg="#f0f0f0")
        self.result_label.pack(anchor='w', padx=5)
        # Scroll effect and text-wrapping
        self.result_text = ScrolledText(self.result_frame, wrap=tk.WORD, width=80, height=20, font=self.default_font)
        self.result_text.pack(padx=5, pady=5)
        self.result_frame.pack(pady=10)

    def start_search(self):
        search_term = self.entry_field.get().strip()
        if not search_term:
            return

        # Update search history
        self.search_history[search_term] = self.search_history.get(search_term, 0) + 1

        # Disable search button and show loader
        self.search_button.config(state=tk.DISABLED)
        self.loader_frame.pack(pady=5)

        # Start search in a new thread to keep UI responsive
        threading.Thread(target=self.search, args=(search_term,), daemon=True).start()

    def search(self, search_term):
        # Find similar search terms from history
        similar_terms = difflib.get_close_matches(search_term, self.search_history.keys(), cutoff=0.6)
        # Perform search using DuckDuckGo's HTML interface
        results = self.perform_search(search_term)
        self.results = results
        # Update the UI in the main thread
        self.root.after(0, self.update_results, search_term, results, similar_terms)

    def update_results(self, search_term, results, similar_terms):
        # Clear previous results and display new ones
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, f"Results for '{search_term}':\n\n")
        for idx, (title, link) in enumerate(results, start=1):
            display_text = f"{idx}. {title}\n{link}\n\n"
            start_index = self.result_text.index(tk.END)
            self.result_text.insert(tk.END, display_text)
            tag_name = f"link{idx}"
            self.result_text.tag_add(tag_name, start_index, f"{start_index} + {len(display_text)}c")
            self.result_text.tag_config(tag_name, foreground="blue", underline=True)
            # Bind events to change cursor on hover
            self.result_text.tag_bind(tag_name, "<Enter>", lambda e: self.result_text.config(cursor="hand2"))
            self.result_text.tag_bind(tag_name, "<Leave>", lambda e: self.result_text.config(cursor=""))
            # Bind click event to open full content in embedded browser; capture current link with default argument
            self.result_text.tag_bind(tag_name, "<Button-1>", lambda e, link_url=link: self.fetch_content(link_url))

        # Append search history and similar search terms
        self.result_text.insert(tk.END, "\nSearch History:\n")
        for term, count in self.search_history.items():
            self.result_text.insert(tk.END, f"{term}: {count}\n")
        if similar_terms:
            self.result_text.insert(tk.END, "\nSimilar Search Terms:\n")
            for term in similar_terms:
                self.result_text.insert(tk.END, f"{term}\n")

        # Hide loader and re-enable search button
        self.loader_frame.pack_forget()
        self.search_button.config(state=tk.NORMAL)

    def perform_search(self, query):
        """Uses DuckDuckGo's HTML search to retrieve results."""
        search_url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            # Changed from POST to GET for compatibility
            response = requests.get(search_url, params=params, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            # DuckDuckGo's results are contained in <a> tags with class "result__a"
            for a in soup.find_all("a", class_="result__a"):
                title = a.get_text().strip()
                link = a.get("href")
                results.append((title, link))
            if not results:
                results = [("No results found", "")]
            return results
        except Exception as e:
            return [("Error performing search", str(e))]

    def fetch_content(self, url):
        """Schedules opening the content in an embedded browser view on the main thread."""
        if not url:
            return
        # Schedule open_webview to run on the main thread
        self.root.after(0, self.open_webview, url)

    def open_webview(self, url):
        """Opens the given URL in an embedded browser view using pywebview."""
        webview.create_window("Content Viewer", url, width=900, height=700)
        webview.start()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Search Engine Simulator")
    root.geometry("900x700")
    program = SearchProgram(root)
    root.mainloop()
