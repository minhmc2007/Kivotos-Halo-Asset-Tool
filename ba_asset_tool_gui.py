# Kivotos Halo Asset Tool - GUI
# Version: 2.0 Windows Edition
# Author: minhmc2007
#
# This tool provides a graphical interface for extracting and repacking Unity asset bundles.
# It is intended for educational and personal use only.
# Use at your own risk. The developer is not responsible for any issues caused by its use.
# Dependencies: UnityPy, Pillow (PIL)

import UnityPy
import os
import sys
import json
from PIL import Image
import glob
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- Configuration ---
SCRIPT_VERSION = "2.0 Windows Edition"
AUTHOR = "minhmc2007"

# --- Helper Functions (Unchanged) ---
def ensure_dir(directory):
    if not os.path.exists(directory):
        try: os.makedirs(directory, exist_ok=True)
        except OSError as e: messagebox.showerror("Directory Error", f"Could not create directory {directory}.\nDetails: {e}"); return False
    return True

def sanitize_name(name):
    if not name: return ""
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip()

def get_ingame_name_from_bundle(filename):
    filename_lower = filename.lower()
    prefix1 = "assets-_mx-spinecharacters-"
    suffix1_marker = "_spr-"
    if filename_lower.startswith(prefix1) and suffix1_marker in filename_lower:
        try:
            start_idx = len(prefix1); end_idx = filename_lower.index(suffix1_marker, start_idx); name_part = filename[start_idx:end_idx]
            if name_part: return name_part.replace('_', ' ').strip().title()
        except ValueError: pass
    prefix2 = "uis-"; suffix2_marker = "-sprite-"
    if filename_lower.startswith(prefix2) and suffix2_marker in filename_lower:
        try:
            parts = filename_lower.split('-')
            for i, part in enumerate(parts):
                if part == "sprite" and i > 0: name_part = parts[i-1]; return name_part.replace('_', ' ').strip().title()
            if "emoticon-sprite" in filename_lower: return "Emoticon"
        except Exception: pass
    return "Unknown"

# --- Core Logic (FIXED) ---
def extract_bundle(bundle_path, output_dir_for_bundle):
    print(f"\n[Sensei's Workshop] Starting extraction for: '{os.path.basename(bundle_path)}'")
    print(f"Outputting to: '{output_dir_for_bundle}'")
    if not ensure_dir(output_dir_for_bundle): return False
    try:
        env = UnityPy.load(bundle_path)
        print("Bundle loaded successfully. Reading objects...")
    except Exception as e:
        print(f"Error: Failed to load bundle '{bundle_path}'.\nDetails: {e}")
        return False

    manifest = {"original_bundle_path": os.path.abspath(bundle_path), "script_version": SCRIPT_VERSION, "assets": []}
    sub_dirs = {"Textures": os.path.join(output_dir_for_bundle, "Textures"),"TextAssets": os.path.join(output_dir_for_bundle, "TextAssets"),"MonoBehaviours_JSON": os.path.join(output_dir_for_bundle, "MonoBehaviours_JSON"),"AudioClips": os.path.join(output_dir_for_bundle, "AudioClips"),"OtherAssets": os.path.join(output_dir_for_bundle, "OtherAssets")}
    for d in sub_dirs.values(): ensure_dir(d)

    total_objects = len(env.objects)
    print(f"Found {total_objects} assets in the bundle.")
    for i, obj in enumerate(env.objects):
        asset_info = {"path_id": obj.path_id, "type": str(obj.type.name), "name": "", "extracted_filename": ""}
        print(f"\rProcessing asset {i+1}/{total_objects} (Type: {obj.type.name})...", end="", flush=True)
        try:
            data = obj.read()
            asset_name_original = getattr(data, "m_Name", "")
            asset_name = sanitize_name(asset_name_original) or f"{sanitize_name(str(obj.type.name))}_{obj.path_id}"
            asset_info["name"] = asset_name_original
            processed = False

            # THIS IS THE SECTION THAT WAS FIXED
            if obj.type.name in ["Texture2D", "Sprite"]:
                try:
                    filename = f"{asset_name}_{obj.path_id}.png"
                    filepath = os.path.join(sub_dirs["Textures"], filename)
                    if data.image:
                        data.image.save(filepath)
                        asset_info["extracted_filename"] = os.path.join("Textures", filename)
                        processed = True
                except Exception as e:
                    print(f"\n    Warning: Error saving {obj.type.name} {asset_name}: {e}")

            elif obj.type.name == "TextAsset":
                try:
                    script_content = data.script.decode('utf-8', errors='replace')
                    filepath = os.path.join(sub_dirs["TextAssets"], f"{asset_name}_{obj.path_id}.txt")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(script_content)
                    asset_info["extracted_filename"] = os.path.join("TextAssets", os.path.basename(filepath))
                    processed = True
                except Exception as e:
                    print(f"\n    Warning: Error saving TextAsset {asset_name}: {e}")
            # END OF FIXED SECTION

            if asset_info["extracted_filename"]:
                manifest["assets"].append(asset_info)
        except Exception as e:
            print(f"\n  Major error processing object PathID {obj.path_id} (Type: {obj.type.name}): {e}")

    print("\nExtraction process finished.")
    manifest_path = os.path.join(output_dir_for_bundle, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, indent=4))
    print(f"Manifest saved. せんせい、抽出が完了しました！ (Extraction complete!)")
    return True

def repack_bundle(input_dir_with_manifest, output_bundle_full_path):
    print(f"\n[Sensei's Workshop] Repacking assets from: '{input_dir_with_manifest}'")
    manifest_path = os.path.join(input_dir_with_manifest, "manifest.json")
    if not os.path.exists(manifest_path): print(f"Error: manifest.json not found."); return False
    with open(manifest_path, "r", encoding="utf-8") as f: manifest = json.load(f)
    original_bundle_path = manifest.get("original_bundle_path")
    if not original_bundle_path or not os.path.exists(original_bundle_path): print(f"Error: Original bundle path not found."); return False
    print(f"Using template: '{os.path.basename(original_bundle_path)}'"); env = UnityPy.load(original_bundle_path); modified_count = 0
    for idx, asset_entry in enumerate(manifest["assets"]):
        if not asset_entry.get("extracted_filename"): continue
        path_id = asset_entry["path_id"]; print(f"\rProcessing asset {idx+1}/{len(manifest['assets'])} (PathID: {path_id})...", end="", flush=True)
        modified_file_path = os.path.join(input_dir_with_manifest, asset_entry["extracted_filename"])
        if os.path.exists(modified_file_path):
            target_obj = next((obj for obj in env.objects if obj.path_id == path_id), None)
            if target_obj:
                try:
                    data = target_obj.read(); asset_type = asset_entry["type"]
                    if asset_type in ["Texture2D", "Sprite"]: data.image = Image.open(modified_file_path); data.save(); modified_count += 1
                    elif asset_type == "TextAsset":
                        with open(modified_file_path, "rb") as f: data.script = f.read()
                        data.save(); modified_count += 1
                except Exception as e: print(f"\n    Warning: Error updating PathID {path_id}: {e}")
    print("\nRepacking process finished.")
    if modified_count > 0:
        try:
            ensure_dir(os.path.dirname(output_bundle_full_path))
            with open(output_bundle_full_path, "wb") as f: f.write(env.file.save())
            print(f"Repacking complete! {modified_count} asset(s) modified."); print(f"New bundle: '{output_bundle_full_path}'"); print(f"任務完了、せんせい！ (Mission complete!)")
        except Exception as e: print(f"Error saving repacked bundle: {e}"); return False
    else: print("Repacking complete. No assets were modified.")
    return True


# --- Animated Splash Screen ---
class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True) # Borderless window
        self.config(bg='#f0f0f0', borderwidth=2, relief='raised')
        disclaimer_text = ("This is a third-party tool created for educational and personal use. Modifying game files can be against the game's Terms of Service and may lead to unforeseen consequences, including account suspension. Use this tool responsibly and at your own risk. The developer is not responsible for any issues that may arise from its use.")
        ttk.Label(self, text="Disclaimer", font=('Segoe UI', 14, 'bold'), background='#f0f0f0').pack(pady=(20, 10))
        ttk.Label(self, text=disclaimer_text, wraplength=400, justify='center', background='#f0f0f0', font=('Segoe UI', 10)).pack(padx=20, pady=10)
        style = ttk.Style(self); style.configure('Splash.TButton', font=('Segoe UI', 10, 'bold'), foreground='white', background='#0078D7'); style.map('Splash.TButton', background=[('active', '#005a9e')])
        ok_button = ttk.Button(self, text="I Understand", style='Splash.TButton', command=self.close_splash); ok_button.pack(pady=20)
        self.center_window(); self.fade_in()
    def center_window(self):
        self.update_idletasks(); width = self.winfo_width(); height = self.winfo_height(); x = (self.winfo_screenwidth() // 2) - (width // 2); y = (self.winfo_screenheight() // 2) - (height // 2); self.geometry(f'{width}x{height}+{x}+{y}')
    def fade_in(self): self.attributes('-alpha', 0.0); self.after(100, self._fade_step, 0.0)
    def _fade_step(self, alpha):
        alpha += 0.05
        if alpha < 1.0: self.attributes('-alpha', alpha); self.after(15, self._fade_step, alpha)
        else: self.attributes('-alpha', 1.0)
    def close_splash(self): self.destroy()

# --- Main GUI Application ---
class TextRedirector(object):
    def __init__(self, widget, tag="stdout"): self.widget, self.tag = widget, tag
    def write(self, s): self.widget.configure(state='normal'); self.widget.insert(tk.END, s, (self.tag,)); self.widget.see(tk.END); self.widget.configure(state='disabled')
    def flush(self): pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Kivotos Halo Asset Tool - v{SCRIPT_VERSION}"); self.geometry("850x750"); self.minsize(700, 600); self.config(bg='#f0f0f0')
        self.bundle_source_dir = tk.StringVar(); self.extract_output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "extracted")); self.repack_input_dir = tk.StringVar(); self.repack_output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "repacked")); self.all_bundles = []; self.current_frame = None; self.is_transitioning = False
        self._setup_styles(); self._setup_ui()
        self.log_text = self.log_frame.winfo_children()[0]; sys.stdout = TextRedirector(self.log_text, "stdout"); sys.stderr = TextRedirector(self.log_text, "stderr")
        self.after(100, lambda: self.switch_frame("Home")); print("Welcome, Sensei! Please select an action from the menu (☰).")
    def _setup_styles(self):
        style = ttk.Style(self); style.theme_use('clam'); style.configure('TFrame', background='#f0f0f0'); style.configure('Top.TFrame', background='#e1e1e1'); style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), foreground='white', background='#0078D7', borderwidth=0); style.map('Accent.TButton', background=[('active', '#005a9e'), ('hover', '#006ac1')]); style.configure('Menu.TButton', font=('Segoe UI', 12), relief='flat', background='#e1e1e1', borderwidth=0); style.map('Menu.TButton', background=[('active', '#cccccc'), ('hover', '#d9d9d9')])
    def _setup_ui(self):
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        top_bar = ttk.Frame(self, style='Top.TFrame', height=40); top_bar.grid(row=0, column=0, sticky='ew'); self._setup_menu(top_bar)
        self.container = ttk.Frame(self); self.container.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.log_frame = ttk.LabelFrame(self, text="Log", padding=10); self.log_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 10))
        log_text = tk.Text(self.log_frame, height=8, wrap='word', state='disabled', bg="#fdfdfd", font=('Consolas', 9), relief='sunken', borderwidth=1); log_scroll = ttk.Scrollbar(self.log_frame, orient="vertical", command=log_text.yview); log_text['yscrollcommand'] = log_scroll.set; log_text.tag_configure("stderr", foreground="#FF0000"); log_scroll.pack(side="right", fill="y"); log_text.pack(side="left", fill="both", expand=True)
        self.frames = {}
        for F in (HomeFrame, ExtractFrame, RepackFrame, AboutFrame):
            page_name = F.__name__.replace("Frame", ""); frame = F(parent=self.container, controller=self); self.frames[page_name] = frame; frame.place(x=0, y=0, relwidth=1, relheight=1)
    def _setup_menu(self, parent):
        menu_button = ttk.Button(parent, text='\u2630', style='Menu.TButton', width=3); menu_button.pack(side='left', padx=5, pady=5)
        menu = tk.Menu(self, tearoff=0); menu.add_command(label="Home", command=lambda: self.switch_frame("Home")); menu.add_separator(); menu.add_command(label="Extract Bundles", command=lambda: self.switch_frame("Extract")); menu.add_command(label="Repack Bundles", command=lambda: self.switch_frame("Repack")); menu.add_separator(); menu.add_command(label="About", command=lambda: self.switch_frame("About")); menu_button.bind("<Button-1>", lambda e: menu.post(e.x_root, e.y_root))
    def switch_frame(self, page_name):
        if self.is_transitioning or self.frames.get(page_name) == self.current_frame: return
        self.is_transitioning = True; new_frame = self.frames[page_name]; old_frame = self.current_frame; new_frame.place(relx=1, rely=0, relwidth=1, relheight=1); new_frame.tkraise()
        self._animate_slide(old_frame, new_frame)
    def _animate_slide(self, old_frame, new_frame, step=0):
        total_steps = 20; progress = step / total_steps
        if old_frame: old_frame.place(relx=-progress, rely=0, relwidth=1, relheight=1)
        new_frame.place(relx=1-progress, rely=0, relwidth=1, relheight=1)
        if step < total_steps: self.after(10, self._animate_slide, old_frame, new_frame, step + 1)
        else: self.current_frame = new_frame; self.is_transitioning = False
    def run_threaded_task(self, task_function, *args): threading.Thread(target=task_function, args=args, daemon=True).start()

class PageFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='TFrame'); self.controller = controller; self.bind_hover(self)
    def bind_hover(self, widget):
        for child in widget.winfo_children():
            if isinstance(child, ttk.Button) and ('Accent.TButton' in str(child.cget('style')) or 'Splash.TButton' in str(child.cget('style'))): child.bind("<Enter>", lambda e, w=child: w.state(['!active', 'hover'])); child.bind("<Leave>", lambda e, w=child: w.state(['!active']))
            elif isinstance(child, (ttk.Frame, ttk.LabelFrame)): self.bind_hover(child)

class HomeFrame(PageFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = ttk.Label(self, text="Kivotos Halo Asset Tool", font=('Segoe UI', 24, 'bold'), background='#f0f0f0'); label.pack(pady=(40, 10))
        info_label = ttk.Label(self, text="Welcome, Sensei!\n\nUse the menu (☰) in the top-left to navigate.", justify='center', font=('Segoe UI', 12), background='#f0f0f0'); info_label.pack(pady=20, padx=20)
class AboutFrame(PageFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = ttk.Label(self, text="About This Tool", font=('Segoe UI', 24, 'bold'), background='#f0f0f0'); label.pack(pady=(40, 20))
        info_label = ttk.Label(self, text=f"Version: {SCRIPT_VERSION}\nMade by: {AUTHOR}\n\nせんせい、今日も頑張ってください！", justify='center', font=('Segoe UI', 12), background='#f0f0f0'); info_label.pack(pady=20, padx=20)

class ExtractFrame(PageFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        src_frame = ttk.Labelframe(self, text="Step 1: Select Bundle Source Directory", padding=10); src_frame.pack(fill='x', padx=10, pady=10)
        ttk.Entry(src_frame, textvariable=controller.bundle_source_dir, state='readonly').pack(side='left', fill='x', expand=True, padx=(0,5))
        ttk.Button(src_frame, text="Browse...", command=self._select_bundle_source, style='Accent.TButton').pack(side='left')
        list_frame = ttk.Labelframe(self, text="Step 2: Find and Select a Bundle", padding=10); list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        ttk.Label(list_frame, text="Filter:").pack(side='top', anchor='w'); self.filter_var = tk.StringVar(); self.filter_var.trace_add("write", self._update_bundle_list); ttk.Entry(list_frame, textvariable=self.filter_var).pack(side='top', fill='x', pady=(0, 5))
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical"); self.bundle_listbox = tk.Listbox(list_frame, yscrollcommand=list_scroll.set, selectmode=tk.SINGLE, font=('Consolas', 9), relief='sunken', borderwidth=1); list_scroll.config(command=self.bundle_listbox.yview); list_scroll.pack(side="right", fill="y"); self.bundle_listbox.pack(side="left", fill="both", expand=True)
        bottom_frame = ttk.Frame(self); bottom_frame.pack(fill='x', padx=10, pady=10)
        out_frame = ttk.Labelframe(bottom_frame, text="Step 3: Set Output Directory", padding=10); out_frame.pack(side='left', fill='x', expand=True)
        ttk.Entry(out_frame, textvariable=controller.extract_output_dir).pack(side='left', fill='x', expand=True, padx=(0,5))
        ttk.Button(out_frame, text="Browse...", command=lambda: self._select_dir_for_var(controller.extract_output_dir, "Select Extraction Parent Directory"), style='Accent.TButton').pack(side='left')
        ttk.Button(bottom_frame, text="Extract", style='Accent.TButton', command=self._run_extract).pack(side='right', padx=(10,0), ipady=5, ipadx=10)
        self.bind_hover(self)
    def _select_dir_for_var(self, str_var, title): directory = filedialog.askdirectory(title=title); (str_var.set(directory) if directory else None)
    def _select_bundle_source(self):
        directory = filedialog.askdirectory(title="Select Bundle Directory")
        if directory: 
            self.controller.bundle_source_dir.set(directory)
            print(f"Scanning: {directory}")
            self.controller.all_bundles.clear()
            bundle_files = glob.glob(os.path.join(directory, '**', '*.bundle'), recursive=True)
            for path in bundle_files:
                self.controller.all_bundles.append({'path': path, 'display': f"{os.path.basename(path):<80} ({get_ingame_name_from_bundle(os.path.basename(path))})"})
            self.controller.all_bundles.sort(key=lambda x: x['display'])
            self._update_bundle_list()
            print(f"Found {len(self.controller.all_bundles)} bundles.")
    def _update_bundle_list(self, *args):
        self.bundle_listbox.delete(0, tk.END); filter_text = self.filter_var.get().lower()
        for bundle in self.controller.all_bundles:
            if filter_text in bundle['display'].lower(): self.bundle_listbox.insert(tk.END, bundle['display'])
    def _run_extract(self):
        selection_indices = self.bundle_listbox.curselection()
        if not selection_indices: messagebox.showerror("Error", "No bundle selected."); return
        selected_display_name = self.bundle_listbox.get(selection_indices[0]); selected_bundle_info = next((b for b in self.controller.all_bundles if b['display'] == selected_display_name), None)
        if not selected_bundle_info: messagebox.showerror("Error", "Could not find bundle data."); return
        bundle_path = selected_bundle_info['path']; output_parent_dir = self.controller.extract_output_dir.get()
        if not output_parent_dir or not bundle_path: messagebox.showerror("Error", "Output directory or bundle path is missing."); return
        bundle_name_no_ext = os.path.splitext(os.path.basename(bundle_path))[0]; output_dir_for_bundle = os.path.join(output_parent_dir, sanitize_name(bundle_name_no_ext))
        self.controller.run_threaded_task(self._extract_thread_target, bundle_path, output_dir_for_bundle)
    def _extract_thread_target(self, bundle_path, output_dir):
        if extract_bundle(bundle_path, output_dir): messagebox.showinfo("Success", f"Extraction complete!\nFiles are in: {output_dir}")
        else: messagebox.showerror("Extraction Failed", "An error occurred. Check the log for details.")

class RepackFrame(PageFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        in_frame = ttk.Labelframe(self, text="Step 1: Select Folder to Repack", padding=10); in_frame.pack(fill='x', padx=10, pady=(20, 10))
        ttk.Entry(in_frame, textvariable=controller.repack_input_dir, state='readonly').pack(side='left', fill='x', expand=True, padx=(0,5))
        ttk.Button(in_frame, text="Select Folder...", command=self._select_repack_input, style='Accent.TButton').pack(side='left')
        out_dir_frame = ttk.Labelframe(self, text="Step 2: Select Repack Output Directory", padding=10); out_dir_frame.pack(fill='x', padx=10, pady=10)
        ttk.Entry(out_dir_frame, textvariable=controller.repack_output_dir).pack(side='left', fill='x', expand=True, padx=(0,5))
        ttk.Button(out_dir_frame, text="Browse...", command=lambda: self._select_dir_for_var(controller.repack_output_dir, "Select Repack Output Directory"), style='Accent.TButton').pack(side='left')
        out_file_frame = ttk.Labelframe(self, text="Step 3: Set Output Filename", padding=10); out_file_frame.pack(fill='x', padx=10, pady=10)
        self.repack_output_filename = tk.StringVar(value="repacked_new.bundle"); ttk.Entry(out_file_frame, textvariable=self.repack_output_filename).pack(fill='x', expand=True)
        ttk.Button(self, text="Repack Folder", style='Accent.TButton', command=self._run_repack).pack(pady=20, ipady=5, ipadx=10)
        self.bind_hover(self)
    def _select_dir_for_var(self, str_var, title): directory = filedialog.askdirectory(title=title); (str_var.set(directory) if directory else None)
    def _select_repack_input(self):
        directory = filedialog.askdirectory(title="Select Extracted Folder (containing manifest.json)")
        if directory and os.path.exists(os.path.join(directory, "manifest.json")): self.controller.repack_input_dir.set(directory)
        elif directory: messagebox.showwarning("Invalid Folder", "The selected folder does not contain 'manifest.json'.")
    def _run_repack(self):
        input_dir = self.controller.repack_input_dir.get(); output_dir = self.controller.repack_output_dir.get(); output_filename = sanitize_name(self.repack_output_filename.get())
        if not all([input_dir, output_dir, output_filename]): messagebox.showerror("Error", "All fields are required."); return
        if not os.path.isdir(input_dir): messagebox.showerror("Error", f"Input directory not found:\n{input_dir}"); return
        output_path = os.path.join(output_dir, output_filename)
        self.controller.run_threaded_task(self._repack_thread_target, input_dir, output_path)
    def _repack_thread_target(self, input_dir, output_path):
        if repack_bundle(input_dir, output_path): messagebox.showinfo("Success", f"Repacking complete!\nNew bundle: {output_path}")
        else: messagebox.showerror("Repack Failed", "An error occurred. Check the log.")

# --- Main Entry Point ---
if __name__ == "__main__":
    try:
        import UnityPy, PIL
    except ImportError as e:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Dependency Error", f"Missing library: {e.name}\nPlease run: pip install UnityPy Pillow"); sys.exit(1)

    root = tk.Tk()
    root.withdraw() # Hide the root window
    splash = SplashScreen(root)
    root.wait_window(splash) # Wait for splash to be closed
    
    app = App()
    app.mainloop()