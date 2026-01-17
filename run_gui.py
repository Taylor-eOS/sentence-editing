import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import pysbd

class SentenceEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sentence Search and Edit Tool")
        self.geometry("1450x850")
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load File", command=self.load_file)
        filemenu.add_command(label="Save File", command=self.save_file)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(search_frame, text="Search terms (space-separated for AND):").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=60)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Find Matches", command=self.find_matches).pack(side=tk.LEFT)
        content_frame = tk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True)
        list_frame = tk.Frame(content_frame, width=300)
        list_frame.pack(side=tk.LEFT, fill=tk.Y)
        list_frame.pack_propagate(False)
        self.listbox = tk.Listbox(list_frame)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        list_scroll = tk.Scrollbar(list_frame, command=self.listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=list_scroll.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)
        text_frame = tk.Frame(content_frame)
        text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.main_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=("Segoe UI", 11))
        self.main_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.main_text.tag_config("marker", foreground="blue", font=("Segoe UI", 16, "bold"))
        edit_frame = tk.Frame(self)
        edit_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(edit_frame, text="Edit selected sentence:").pack(side=tk.LEFT)
        self.edit_text = tk.Text(edit_frame, height=8, wrap=tk.WORD, font=("Segoe UI", 11))
        self.edit_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        button_frame = tk.Frame(edit_frame)
        button_frame.pack(side=tk.RIGHT)
        tk.Button(button_frame, text="Previous", command=self.go_previous).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Next", command=self.go_next).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Replace", command=self.replace_current).pack(side=tk.LEFT, padx=2)
        self.full_text = ""
        self.matches = []
        self.current_index = -1
        self.segmenter = pysbd.Segmenter(language="en", clean=False, char_span=True)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.full_text = content
                self.main_text.delete("1.0", tk.END)
                self.main_text.insert("1.0", content)
                self.matches = []
                self.listbox.delete(0, tk.END)
                self.current_index = -1
                self.edit_text.delete("1.0", tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load file:\n{e}")

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.full_text)
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")

    def find_matches(self):
        terms = [t.strip().lower() for t in self.search_entry.get().split() if t.strip()]
        if not terms:
            self.matches = []
            self.listbox.delete(0, tk.END)
            return
        try:
            sent_spans = self.segmenter.segment(self.full_text)
        except:
            messagebox.showerror("Error", "Sentence segmentation failed. Check pysbd installation.")
            return
        self.matches = []
        for span in sent_spans:
            if all(term in span.sent.lower() for term in terms):
                self.matches.append((span.sent, span.start, span.end))
        self.listbox.delete(0, tk.END)
        for i, (sent, _, _) in enumerate(self.matches):
            display = sent.replace("\n", " ").replace("\r", " ")
            if len(display) > 120:
                display = display[:117] + "..."
            self.listbox.insert(tk.END, f"{i+1:4d}: {display}")
        self.current_index = -1
        self.edit_text.delete("1.0", tk.END)

    def on_list_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            self.current_index = selection[0]
            self.load_current()

    def load_current(self):
        if self.current_index < 0 or self.current_index >= len(self.matches):
            return
        sent, start, end = self.matches[self.current_index]
        self.edit_text.delete("1.0", tk.END)
        self.edit_text.insert("1.0", sent)
        self.main_text.tag_remove("marker", "1.0", tk.END)
        prefix = self.full_text[:start].split('\n')[-1]
        search_text = prefix + sent[:min(50, len(sent))]
        search_start = "1.0"
        pos = self.main_text.search(search_text, search_start, tk.END)
        if pos:
            line_start = pos.split('.')[0] + '.0'
            self.main_text.see(line_start)
            marker_pos = f"{pos}+{len(prefix)}c"
            self.main_text.insert(marker_pos, "● ")
            self.main_text.tag_add("marker", marker_pos, f"{marker_pos}+2c")

    def go_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.listbox.see(self.current_index)
            self.load_current()

    def go_next(self):
        if self.current_index < len(self.matches) - 1:
            self.current_index += 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.listbox.see(self.current_index)
            self.load_current()

    def replace_current(self):
        if self.current_index < 0 or self.current_index >= len(self.matches):
            return
        new_sent = self.edit_text.get("1.0", "end-1c")
        old_sent, old_start, old_end = self.matches[self.current_index]
        self.full_text = self.full_text[:old_start] + new_sent + self.full_text[old_end:]
        self.main_text.delete("1.0", tk.END)
        self.main_text.insert("1.0", self.full_text)
        old_len = old_end - old_start
        new_len = len(new_sent)
        length_diff = new_len - old_len
        self.matches[self.current_index] = (new_sent, old_start, old_start + new_len)
        display = new_sent.replace("\n", " ").replace("\r", " ")
        if len(display) > 120:
            display = display[:117] + "..."
        self.listbox.delete(self.current_index)
        self.listbox.insert(self.current_index, f"{self.current_index+1:4d}: {display}")
        self.listbox.selection_set(self.current_index)
        for i in range(self.current_index + 1, len(self.matches)):
            sent, start, end = self.matches[i]
            self.matches[i] = (sent, start + length_diff, end + length_diff)

if __name__ == "__main__":
    app = SentenceEditor()
    app.mainloop()
