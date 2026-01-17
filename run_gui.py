import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import pysbd

class SentenceEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sentence Search and Edit Tool")
        self.geometry("1450x800")
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
        self.main_text.tag_config("match", background="yellow")
        self.main_text.tag_config("current", background="lightgreen")
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
        self.matches = []
        self.current_index = -1
        self.segmenter = pysbd.Segmenter(language="en", clean=False, char_span=True)
        self.search_terms = []

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
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
                content = self.main_text.get("1.0", "end-1c")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")

    def get_current_text(self):
        return self.main_text.get("1.0", "end-1c")

    def find_matches(self):
        terms = [t.strip().lower() for t in self.search_entry.get().split() if t.strip()]
        if not terms:
            self.matches = []
            self.listbox.delete(0, tk.END)
            self.main_text.tag_remove("match", "1.0", tk.END)
            return
        self.search_terms = terms
        text = self.get_current_text()
        try:
            sent_spans = self.segmenter.segment(text)
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
        self.main_text.tag_remove("match", "1.0", tk.END)
        for _, start, end in self.matches:
            s_idx = f"1.0 + {start}c"
            e_idx = f"1.0 + {end}c"
            self.main_text.tag_add("match", s_idx, e_idx)

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
        s_idx = f"1.0 + {start}c"
        e_idx = f"1.0 + {end}c"
        self.main_text.tag_remove("current", "1.0", tk.END)
        self.main_text.tag_add("current", s_idx, e_idx)
        self.main_text.see(s_idx)

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
        old_len = old_end - old_start
        new_len = len(new_sent)
        length_diff = new_len - old_len
        s_idx = f"1.0 + {old_start}c"
        e_idx = f"1.0 + {old_end}c"
        self.main_text.delete(s_idx, e_idx)
        self.main_text.insert(s_idx, new_sent)
        still_matches = all(term in new_sent.lower() for term in self.search_terms)
        if still_matches:
            self.matches[self.current_index] = (new_sent, old_start, old_start + new_len)
            display = new_sent.replace("\n", " ").replace("\r", " ")
            if len(display) > 120:
                display = display[:117] + "..."
            self.listbox.delete(self.current_index)
            self.listbox.insert(self.current_index, f"{self.current_index+1:4d}: {display}")
            self.listbox.selection_set(self.current_index)
        else:
            self.matches.pop(self.current_index)
            self.listbox.delete(self.current_index)
            if self.current_index >= len(self.matches):
                self.current_index = len(self.matches) - 1
            if self.current_index >= 0:
                self.listbox.selection_set(self.current_index)
        for i in range(self.current_index + 1, len(self.matches)):
            sent, start, end = self.matches[i]
            self.matches[i] = (sent, start + length_diff, end + length_diff)
        self.main_text.tag_remove("match", "1.0", tk.END)
        self.main_text.tag_remove("current", "1.0", tk.END)
        for _, start, end in self.matches:
            s_idx = f"1.0 + {start}c"
            e_idx = f"1.0 + {end}c"
            self.main_text.tag_add("match", s_idx, e_idx)
        if self.current_index >= 0 and self.current_index < len(self.matches):
            self.load_current()
        else:
            self.edit_text.delete("1.0", tk.END)

if __name__ == "__main__":
    app = SentenceEditor()
    app.mainloop()
