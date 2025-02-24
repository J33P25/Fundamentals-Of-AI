import heapq
import threading
import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import json
import re
import time
from collections import defaultdict

# ----------------------------- Helper Functions ----------------------------- #
def extract_categories(soup):
    """Extracts category headings from the webpage."""
    categories = {}
    for tag in soup.find_all(['h2', 'h3', 'h4', 'li']):
        text = tag.get_text().strip().lower()
        if len(text) >= 3:
            categories[text] = []
    return categories

def calculate_pagerank(crawled_data):
    """Simulates PageRank by assigning a rank based on link references."""
    rank = defaultdict(float)
    for category, urls in crawled_data.items():
        for url in urls:
            rank[url] += 1
    return dict(sorted(rank.items(), key=lambda item: item[1], reverse=True))

def keyword_heuristic_score(content, keywords):
    """Calculates a heuristic score based on keyword density in the page content."""
    score = 0
    content = content.lower()
    for keyword in keywords:
        score += content.count(keyword.lower())
    return score

def log_error(url, error_message):
    """Logs errors to a file."""
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"Error with URL {url}: {error_message}\n")

# ----------------------------- Algorithms ----------------------------- #
def bfs_crawl(start_url, max_pages, max_depth, keywords=None, progress_callback=None, stop_event=None):
    """Performs Best-First Search (BFS) to crawl web pages."""
    queue = [(0, start_url, 0)]
    visited = set()
    categorized_urls = {}

    while queue and len(visited) < max_pages:
        if stop_event and stop_event.is_set():
            break

        _, current_url, depth = heapq.heappop(queue)
        if current_url in visited or depth > max_depth:
            continue

        try:
            response = urllib.request.urlopen(current_url)
            soup = BeautifulSoup(response, 'html.parser')
            visited.add(current_url)

            categories = extract_categories(soup)
            page_content = soup.get_text()
            for tag in soup.find_all("a", href=True):
                link = urljoin(current_url, tag['href']).rstrip('/')

                if link not in visited:
                    score = keyword_heuristic_score(page_content, keywords) if keywords else len(link)
                    heapq.heappush(queue, (score, link, depth + 1))

                    for category in categories:
                        if category in tag.get_text().strip().lower():
                            categories[category].append(link)

            for category, urls in categories.items():
                if urls:
                    categorized_urls.setdefault(category, []).extend(set(urls))

        except Exception as e:
            log_error(current_url, str(e))

        if progress_callback:
            progress_callback(len(visited), max_pages)

    return categorized_urls

def dfs_crawl(start_url, max_pages, max_depth, keywords=None, progress_callback=None, stop_event=None):
    """Performs Depth-First Search (DFS) to crawl web pages."""
    stack = [(start_url, 0)]
    visited = set()
    categorized_urls = {}

    while stack and len(visited) < max_pages:
        if stop_event and stop_event.is_set():
            break

        current_url, depth = stack.pop()
        if current_url in visited or depth > max_depth:
            continue

        try:
            response = urllib.request.urlopen(current_url)
            soup = BeautifulSoup(response, 'html.parser')
            visited.add(current_url)

            categories = extract_categories(soup)
            page_content = soup.get_text()
            for tag in soup.find_all("a", href=True):
                link = urljoin(current_url, tag['href']).rstrip('/')

                if link not in visited:
                    stack.append((link, depth + 1))

                    for category in categories:
                        if category in tag.get_text().strip().lower():
                            categories[category].append(link)

            for category, urls in categories.items():
                if urls:
                    categorized_urls.setdefault(category, []).extend(set(urls))

        except Exception as e:
            log_error(current_url, str(e))

        if progress_callback:
            progress_callback(len(visited), max_pages)

    return categorized_urls

# ----------------------------- GUI Logic ----------------------------- #
def update_progress(completed, total, progress_bar):
    """Updates the progress bar with the current crawling progress."""
    progress_bar['value'] = (completed / total) * 100

def display_results(categorized_urls, text_area):
    """Displays the categorized URLs in the text area."""
    text_area.delete("1.0", tk.END)
    for category, urls in categorized_urls.items():
        if urls:
            text_area.insert(tk.END, f"\n[{category.capitalize()}]:\n", "category")
            for url in urls:
                text_area.insert(tk.END, f"{url}\n", "url")

def start_crawl():
    """Starts the crawler in a new thread."""
    global stop_event
    stop_event = threading.Event()

    def run_crawl():
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        progress_bar['value'] = 0
        status_var.set("Crawling in progress...")
        try:
            categorized_urls.clear()
            url = url_entry.get()
            max_pages = int(pages_entry.get())
            keywords = keywords_entry.get().split(",")
            algorithm = algorithm_var.get()

            # Pass the update_progress function as the callback
            progress_callback = lambda completed, total: update_progress(completed, total, progress_bar)

            if algorithm == "Best-First Search (BFS)":
                results = bfs_crawl(url, max_pages, max_depth=3, keywords=keywords, progress_callback=progress_callback, stop_event=stop_event)
            elif algorithm == "Depth-First Search (DFS)":
                results = dfs_crawl(url, max_pages, max_depth=3, keywords=keywords, progress_callback=progress_callback, stop_event=stop_event)
            else:
                results = bfs_crawl(url, max_pages, max_depth=3, progress_callback=progress_callback, stop_event=stop_event)

            categorized_urls.update(results)
            display_results(categorized_urls, text_area)
            status_var.set("Crawling complete!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            start_button.config(state=tk.NORMAL)
            stop_button.config(state=tk.DISABLED)

    threading.Thread(target=run_crawl).start()

def stop_crawl():
    """Stops the crawler."""
    stop_event.set()
    status_var.set("Crawling stopped by user.")
    stop_button.config(state=tk.DISABLED)

def export_results():
    """Exports the results to a file."""
    try:
        with open("categorized_urls.json", "w") as f:
            json.dump(categorized_urls, f, indent=4)
        messagebox.showinfo("Export Complete", "Results exported to categorized_urls.json")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export results: {e}")

# ----------------------------- GUI Elements ----------------------------- #
def display_gui():
    """Displays the GUI for the web crawler."""
    global root, start_button, stop_button, progress_bar, status_var, url_entry, pages_entry, keywords_entry, algorithm_var, categorized_urls, text_area, stop_event

    # Initialize categorized_urls dictionary
    categorized_urls = {}

    root = tk.Tk()
    root.title("Advanced Web Crawler")

    # Frame for URL and other settings
    frame_top = ttk.Frame(root)
    frame_top.pack(pady=10)

    ttk.Label(frame_top, text="Starting URL:").pack(side=tk.LEFT, padx=5)
    url_entry = ttk.Entry(frame_top, width=40)
    url_entry.pack(side=tk.LEFT, padx=5)

    ttk.Label(frame_top, text="Max Pages:").pack(side=tk.LEFT, padx=5)
    pages_entry = ttk.Entry(frame_top, width=5)
    pages_entry.pack(side=tk.LEFT, padx=5)

    ttk.Label(frame_top, text="Keywords (comma separated):").pack(side=tk.LEFT, padx=5)
    keywords_entry = ttk.Entry(frame_top, width=30)
    keywords_entry.pack(side=tk.LEFT, padx=5)

    # Algorithm Selection
    ttk.Label(frame_top, text="Algorithm:").pack(side=tk.LEFT, padx=5)
    algorithm_var = tk.StringVar(value="Best-First Search (BFS)")
    ttk.OptionMenu(frame_top, algorithm_var, "Best-First Search (BFS)", "Best-First Search (BFS)", "Depth-First Search (DFS").pack(side=tk.LEFT, padx=5)

    # Buttons for controlling the crawl process
    frame_buttons = ttk.Frame(root)
    frame_buttons.pack(pady=10)

    start_button = ttk.Button(frame_buttons, text="Start Crawling", command=start_crawl)
    start_button.pack(side=tk.LEFT, padx=10)

    stop_button = ttk.Button(frame_buttons, text="Stop Crawling", command=stop_crawl, state=tk.DISABLED)
    stop_button.pack(side=tk.LEFT, padx=10)

    export_button = ttk.Button(frame_buttons, text="Export Results", command=export_results)
    export_button.pack(side=tk.LEFT, padx=10)

    # Progress bar and status
    progress_bar = ttk.Progressbar(root, length=300, mode="determinate")
    progress_bar.pack(pady=5)

    status_var = tk.StringVar()
    status_var.set("Status: Ready")
    ttk.Label(root, textvariable=status_var).pack(pady=5)

    # Text area for displaying categorized URLs
    text_area = tk.Text(root, wrap=tk.WORD, width=80, height=20)
    text_area.pack(padx=10, pady=10)

    root.mainloop()

# ----------------------------- Main Execution ----------------------------- #
if __name__ == "_main_":
    display_gui()