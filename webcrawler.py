import heapq
import threading
import urllib.request
import urllib.error
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import json


# ----------------------------- Helper Functions ----------------------------- #
def extract_categories(soup):
    """Extracts category headings from the webpage."""
    categories = {}
    for tag in soup.find_all(['h2', 'h3', 'h4', 'li']):
        text = tag.get_text().strip().lower()
        if len(text) >= 3:
            categories[text] = []
    return categories


#Breadth First Search
def simple_bfs_crawl(start_url, max_pages, max_depth=3, progress_callback=None, stop_event=None):
    """Performs Simple Breadth-First Search (BFS) to crawl web pages without heuristics."""
    queue = [(start_url, 0)]  # Simple BFS with a queue (URL, depth)
    visited = set()
    categorized_urls = {}

    while queue and len(visited) < max_pages:
        if stop_event and stop_event.is_set():
            break

        current_url, depth = queue.pop(0)  # Dequeue the first element
        if current_url in visited or depth > max_depth:
            continue

        try:
            response = urllib.request.urlopen(current_url)
            soup = BeautifulSoup(response, 'html.parser')
            visited.add(current_url)

            categories = extract_categories(soup)
            # Check all anchor tags for links to follow
            for tag in soup.find_all("a", href=True):
                link = urljoin(current_url, tag['href']).rstrip('/')

                # Add the link to the queue if it hasn't been visited yet
                if link not in visited:
                    queue.append((link, depth + 1))
                    visited.add(link)  # Mark it as visited immediately

                    # Categorize the link based on the current page's categories
                    for category in categories:
                        if category in tag.get_text().strip().lower():
                            if link not in categorized_urls.get(category, []):  # Avoid duplicates
                                categorized_urls.setdefault(category, []).append(link)


        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason} for {current_url}")
        except Exception as e:
            print(f"Error: {str(e)} occurred for {current_url}")

        if progress_callback:
            progress_callback(len(visited), max_pages)

    return categorized_urls


#Depth First Search
def depth_first_search_crawl(start_url, max_pages, max_depth=3, progress_callback=None, stop_event=None):
    """Performs Depth-First Search (DFS) to crawl web pages."""
    stack = [(start_url, 0)]  # Stack for DFS (URL, depth)
    visited = set()
    categorized_urls = {}

    while stack and len(visited) < max_pages:
        if stop_event and stop_event.is_set():
            break

        current_url, depth = stack.pop()  # Pop the last element from the stack (DFS)
        if current_url in visited or depth > max_depth:
            continue

        try:
            response = urllib.request.urlopen(current_url)
            soup = BeautifulSoup(response, 'html.parser')
            visited.add(current_url)

            categories = extract_categories(soup)
            for tag in soup.find_all("a", href=True):
                link = urljoin(current_url, tag['href']).rstrip('/')

                if link not in visited:
                    stack.append((link, depth + 1))
                    visited.add(link)  # Mark as visited immediately

                    for category in categories:
                        if category in tag.get_text().strip().lower():
                            if link not in categories[category]:  # Avoid duplicate URLs in category
                                categories[category].append(link)

            # Avoid adding duplicate URLs to categorized_urls
            for category, urls in categories.items():
                if urls:
                    categorized_urls.setdefault(category, []).extend(url for url in urls if url not in categorized_urls.get(category, []))

        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason} for {current_url}")
        except Exception as e:
            print(f"Error: {str(e)} occurred for {current_url}")

        if progress_callback:
            progress_callback(len(visited), max_pages)

    return categorized_urls


#Best First Search
def best_first_search_crawl(start_url, max_pages, max_depth=3, progress_callback=None, stop_event=None):
    """Performs Best-First Search (BFS) using a heuristic function based on URL length."""
    # Priority queue initialized with the start URL
    queue = [(len(start_url), start_url, 0)]  # Use the length of the start URL as its heuristic
    visited = set()
    categorized_urls = {}

    while queue and len(visited) < max_pages:
        if stop_event and stop_event.is_set():
            break

        # Pop the URL with the smallest heuristic first
        _, current_url, depth = heapq.heappop(queue)

        if current_url in visited or depth > max_depth:
            continue

        try:
            response = urllib.request.urlopen(current_url)
            soup = BeautifulSoup(response, 'html.parser')
            visited.add(current_url)  # Mark as visited

            categories = extract_categories(soup)  # Assuming this function is defined elsewhere

            for tag in soup.find_all("a", href=True):
                link = urljoin(current_url, tag['href']).rstrip('/')

                if link not in visited:  # Only process if not previously visited
                    # Push new link with its heuristic value
                    heapq.heappush(queue, (len(link), link, depth + 1))  # Use length as heuristic
                    visited.add(link)  # Important to mark it immediately as visited

                    # Categorize the link based on extracted categories
                    for category in categories:
                        if category in tag.get_text().strip().lower():
                            if link not in categories[category]:  # Avoid duplicates
                                categories[category].append(link)

            # Avoid duplicate entries in categorized_urls
            for category, urls in categories.items():
                if urls:
                    categorized_urls.setdefault(category, []).extend(
                        url for url in urls if url not in categorized_urls.get(category, [])
                    )

        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason} for {current_url}")
        except Exception as e:
            print(f"Error: {str(e)} occurred for {current_url}")

        # Update progress if the callback is provided
        if progress_callback:
            progress_callback(len(visited), max_pages)

    return categorized_urls


#Iterative Deepening Search
def ids_crawl(start_url, max_pages, max_depth=3, progress_callback=None, stop_event=None):
    """Performs Iterative Deepening Search (IDS) to crawl web pages with a heuristic."""
    categorized_urls = {}

    for depth in range(max_depth + 1):
        if stop_event and stop_event.is_set():
            break
        stack = [(start_url, 0)]
        visited = set()

        while stack and len(visited) < max_pages:
            if stop_event and stop_event.is_set():
                break

            current_url, current_depth = stack.pop()
            if current_url in visited or current_depth > depth:
                continue

            try:
                response = urllib.request.urlopen(current_url)
                soup = BeautifulSoup(response, 'html.parser')
                visited.add(current_url)

                categories = extract_categories(soup)
                for tag in soup.find_all("a", href=True):
                    link = urljoin(current_url, tag['href']).rstrip('/')

                    if link not in visited:
                        stack.append((link, current_depth + 1))
                        visited.add(link)  # Ensure it's marked visited immediately

                        for category in categories:
                            if category in tag.get_text().strip().lower():
                                if link not in categories[category]:  # Avoid duplicate URLs in category
                                    categories[category].append(link)

                # Avoid adding duplicate URLs to categorized_urls
                for category, urls in categories.items():
                    if urls:
                        categorized_urls.setdefault(category, []).extend(url for url in urls if url not in categorized_urls.get(category, []))


            except urllib.error.URLError as e:
                print(f"URL Error: {e.reason} for {current_url}")
            except Exception as e:
                print(f"Error: {str(e)} occurred for {current_url}")

            if progress_callback:
                progress_callback(len(visited), max_pages)

    return categorized_urls



# ----------------------------- GUI Logic ----------------------------- #
def update_progress(completed, total, progress_bar):
    """Updates the progress bar."""
    progress_bar['value'] = (completed / total) * 100


def display_results(categorized_urls, results_frame, canvas):
    """Displays the categorized URLs as clickable links."""
    # Set the background color for the results_frame
    results_frame.configure(bg="#FFEFDB")

    # Clear any existing widgets in the results_frame
    for widget in results_frame.winfo_children():
        widget.destroy()

    for category, urls in categorized_urls.items():
        if urls:
            # Create a label for each category and set background color using tk.Label
            category_label = tk.Label(results_frame, text=f"{category.capitalize()}:", font=("Arial", 12, "bold"), anchor="w", bg="#FFEFDB")
            category_label.pack(fill=tk.X, padx=5, pady=2)

            for url in urls:
                # Create a label for each URL and set background color using tk.Label
                link = tk.Label(results_frame, text=url, fg="blue", cursor="hand2", anchor="w", bg="#FFEFDB")
                link.pack(fill=tk.X, padx=10)
                link.bind("<Button-1>", lambda e, u=url: webbrowser.open_new(u))


    results_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))  # Adjust scroll region after content update


def start_crawl():
    """Starts the crawl in a separate thread."""
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
            algorithm = algorithm_var.get()

            progress_callback = lambda completed, total: update_progress(completed, total, progress_bar)

            if algorithm == "Best-First Search (BFS)":
                results = best_first_search_crawl(url, max_pages, progress_callback=progress_callback, stop_event=stop_event)
            elif algorithm == "Iterative Deepening Search (IDS)":
                results = ids_crawl(url, max_pages, progress_callback=progress_callback, stop_event=stop_event)
            elif algorithm == "Depth-First Search (DFS)":  # Added DFS condition
                results = depth_first_search_crawl(url, max_pages, progress_callback=progress_callback, stop_event=stop_event)
            else:
                results = simple_bfs_crawl(url, max_pages, progress_callback=progress_callback, stop_event=stop_event)

            categorized_urls.update(results)
            display_results(categorized_urls, results_frame, canvas)
            status_var.set("Crawling complete!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            start_button.config(state=tk.NORMAL)
            stop_button.config(state=tk.DISABLED)

    threading.Thread(target=run_crawl).start()



def stop_crawl():
    """Stops the crawl."""
    stop_event.set()
    status_var.set("Crawling stopped by user.")
    stop_button.config(state=tk.DISABLED)


def export_results():
    """Exports results to JSON."""
    with open("categorized_urls.json", "w") as f:
        json.dump(categorized_urls, f, indent=4)
    messagebox.showinfo("Export Complete", "Results exported to categorized_urls.json")


# ----------------------------- GUI Components ----------------------------- #
def display_gui():
    global root, start_button, stop_button, progress_bar, status_var, url_entry, pages_entry, algorithm_var, categorized_urls, results_frame, canvas, stop_event

    categorized_urls = {}

    root = tk.Tk()
    root.title("Advanced Web Crawler")

    # Set background color
    root.configure(bg="#FFEFDB")

    # Set window size to be large and full windowed
    root.state('zoomed')

    # Input Fields
    frame_top = tk.Frame(root, bg="#FFEFDB")  # Use tk.Frame instead of ttk.Frame to add bg color
    frame_top.pack(pady=10)

    tk.Label(frame_top, text="Input URL:", bg="#FFEFDB").grid(row=0, column=0, padx=5,pady=5)
    url_entry = ttk.Entry(frame_top, width=50)
    url_entry.grid(row=0, column=1, padx=5)

    tk.Label(frame_top, text="Max Pages:", bg="#FFEFDB").grid(row=1, column=0, padx=5,pady=15)
    pages_entry = ttk.Entry(frame_top, width=10)
    pages_entry.grid(row=1, column=1, padx=5)

    tk.Label(frame_top, text="Algorithm:", bg="#FFEFDB").grid(row=2, column=0, padx=5,pady=5)
    algorithm_var = tk.StringVar(value="Breadth-First Search (BFS)")
    # Replace ttk.OptionMenu with tk.OptionMenu for background color support
    algorithm_menu = tk.OptionMenu(frame_top, algorithm_var,
                                   "Breadth-First Search (BFS)",
                                   "Depth-First Search (DFS)",
                                   "Best-First Search (BFS)",
                                   "Iterative Deepening Search (IDS)",
                                   )
    algorithm_menu.config(bg="#FFEFDB")
    algorithm_menu['menu'].config(bg="#FFEFDB")
    algorithm_menu.grid(row=2, column=1, padx=5)

    # Buttons
    frame_buttons = tk.Frame(root, bg="#FFEFDB")
    frame_buttons.pack(pady=10)

    start_button = tk.Button(frame_buttons, text="Start Crawl", command=start_crawl, bg="#FFEFDB")
    start_button.grid(row=0, column=0, padx=40)

    stop_button = tk.Button(frame_buttons, text="Stop Crawl", command=stop_crawl, state=tk.DISABLED, bg="#FFEFDB")
    stop_button.grid(row=0, column=1, padx=40)

    export_button = tk.Button(frame_buttons, text="Export Results", command=export_results, bg="#FFEFDB")
    export_button.grid(row=0, column=2, padx=40)

    # Progress Bar
    progress_bar = ttk.Progressbar(root, length=500, mode="determinate")
    progress_bar.pack(pady=10)

    # Status Label
    status_var = tk.StringVar(value="Ready to start crawling.")
    tk.Label(root, textvariable=status_var, bg="#FFEFDB").pack(pady=5)

    # Results Canvas with black outline
    canvas = tk.Canvas(root, bg="#FFEFDB", borderwidth=2, relief="solid", height=500)  # Adjust the height here
    canvas.pack(pady=20, fill=tk.BOTH, expand=True)

    # Change results_frame to tk.Frame to allow bg color configuration
    results_frame = tk.Frame(canvas, bg="#FFEFDB")  # Changed to tk.Frame for background color
    canvas.create_window((0, 0), window=results_frame, anchor="nw")

    # Bind Mouse Scroll to Canvas for Direct Scrolling
    def on_mouse_wheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_mouse_wheel)  # Windows
    canvas.bind_all("<Button-4>", on_mouse_wheel)  # Linux
    canvas.bind_all("<Button-5>", on_mouse_wheel)  # Linux

    # Update scroll region when the frame size changes
    results_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    root.mainloop()



# ----------------------------- Main ----------------------------- #
if __name__ == "__main__":
    display_gui()
