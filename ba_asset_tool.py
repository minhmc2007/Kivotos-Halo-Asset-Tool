import UnityPy
import os
import sys
import json
from PIL import Image
import argparse
import glob

# --- Blue Archive Specific Configuration ---
BLUE_ARCHIVE_BUNDLE_SRC_PATH = "/sdcard/Android/data/com.nexon.bluearchive/files/PUB/Resource/GameData/Android/"
DEFAULT_EXTRACTED_OUTPUT_BASE_DIR = "/sdcard/extracted/"
DEFAULT_REPACKED_OUTPUT_DIR = "/sdcard/repacked/"
SCRIPT_VERSION = "1.0 BA Global Advanced Search Edition"

# ANSI Color Codes
class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m' # For warnings or important notes
    RESET = '\033[0m'

# --- Helper Functions ---
def print_ba_header():
    print("======================================================")
    print(f" {Colors.CYAN}Kivotos Halo Asset Tool - v{SCRIPT_VERSION}{Colors.RESET}          ")
    print("           せんせい、今日も頑張ってください！             ")
    print("======================================================")
    print(f"Bundle Source: {BLUE_ARCHIVE_BUNDLE_SRC_PATH}")
    print(f"Extracted Output Base: {DEFAULT_EXTRACTED_OUTPUT_BASE_DIR}")
    print(f"Repacked Output: {DEFAULT_REPACKED_OUTPUT_DIR}\n")

def ensure_dir(directory):
    if not os.path.exists(directory):
        print(f"Creating directory: {directory}")
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"{Colors.YELLOW}Error: Could not create directory {directory}. Details: {e}{Colors.RESET}")
            sys.exit(1)

def sanitize_name(name):
    if not name: return ""
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip()

def get_ingame_name_from_bundle(filename):
    prefix1 = "assets-_mx-spinecharacters-"
    suffix1_marker = "_spr-"
    if filename.startswith(prefix1) and suffix1_marker in filename:
        try:
            start_idx = len(prefix1)
            end_idx = filename.index(suffix1_marker, start_idx)
            name_part = filename[start_idx:end_idx]
            if name_part: return name_part.replace('_', ' ').strip().title()
        except ValueError: pass

    prefix2 = "uis-"
    suffix2_marker = "-sprite-"
    if filename.startswith(prefix2) and suffix2_marker in filename:
        try:
            parts = filename.split('-')
            for i, part in enumerate(parts):
                if part == "sprite" and i > 0:
                    name_part = parts[i-1]
                    if "_" in name_part: name_part = name_part.split('_',1)[1]
                    return name_part.replace('_', ' ').strip().title()
            if "emoticon-sprite" in filename: return "Emoticon"
        except Exception: pass
    return None

def select_bundle_interactive(base_path):
    print(f"\n[Interactive Bundle Selection]")
    if not os.path.isdir(base_path):
        print(f"{Colors.YELLOW}Error: Bundle source path '{base_path}' not found.{Colors.RESET}")
        return None, None

    master_bundle_list = []
    master_bundle_basenames = set()

    # Part 1: Initial Smart Scan
    print("Performing initial smart scan for character/item sprites...")
    initial_finds = 0
    for item_name in os.listdir(base_path):
        if not item_name.lower().endswith(".bundle"):
            continue
        if "spr" in item_name.lower() or "sprite" in item_name.lower():
            full_path = os.path.join(base_path, item_name)
            if os.path.isfile(full_path):
                basename = os.path.basename(full_path)
                if basename not in master_bundle_basenames:
                    ingame_name = get_ingame_name_from_bundle(basename)
                    master_bundle_list.append({
                        "path": full_path, "basename": basename, "ingame_name": ingame_name, "source": "smart_scan"
                    })
                    master_bundle_basenames.add(basename)
                    initial_finds +=1
    master_bundle_list.sort(key=lambda x: x["basename"])
    current_display_list = list(master_bundle_list) # Start with smart scan results
    print(f"Initial scan found {initial_finds} potential sprite bundles.")

    while True:
        print("\n--- Bundle List ---")
        if not current_display_list:
            print(f"{Colors.YELLOW}No bundles to display with current filter/search.{Colors.RESET}")
        else:
            for i, item_data in enumerate(current_display_list):
                display_name = item_data["basename"]
                filename_display_length = 100
                truncated_display_name = (display_name[:filename_display_length-3] + '...') if len(display_name) > filename_display_length else display_name
                source_indicator = "" # Could add (Source: Smart/Broad) if needed

                if item_data["ingame_name"]:
                    print(f"  [{i+1:3d}] {truncated_display_name:<{filename_display_length}} ({Colors.CYAN}Detected: {item_data['ingame_name']}{Colors.RESET}){source_indicator}")
                else:
                    print(f"  [{i+1:3d}] {truncated_display_name}{source_indicator}")
        
        print("-" * 30)
        prompt_text = "Select #: Bundle | 'f': Filter list | Name (e.g. yuuka): Broad Search | 'q': Quit : "
        user_input = input(prompt_text).strip().lower()

        if user_input == 'q':
            return None, None
        elif user_input == 'f':
            filter_text = input("Filter by (text in filename/detected name | Enter to clear | 'c' to cancel filter): ").lower()
            if filter_text == 'c':
                continue 
            elif not filter_text:
                current_display_list = list(master_bundle_list) # Reset to full master list
                print("Filter cleared.")
            else:
                temp_list = [b for b in master_bundle_list if filter_text in b['basename'].lower() or (b['ingame_name'] and filter_text in b['ingame_name'].lower())]
                if not temp_list:
                    print(f"{Colors.YELLOW}No items match filter '{filter_text}'. Displaying previous list.{Colors.RESET}")
                    # Keep current_display_list as is, or reset to master_bundle_list if preferred
                    # current_display_list = list(master_bundle_list)
                else:
                    current_display_list = temp_list
            continue
        elif user_input.isdigit():
            try:
                choice_num = int(user_input)
                if 1 <= choice_num <= len(current_display_list):
                    selected_item = current_display_list[choice_num - 1]
                    selected_path = selected_item["path"]
                    selected_bundle_name_no_ext = os.path.splitext(os.path.basename(selected_path))[0]
                    return selected_path, selected_bundle_name_no_ext
                else:
                    print(f"{Colors.YELLOW}Invalid selection. Number out of range.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.YELLOW}Invalid input. Please enter a number, 'f', 'q', or a name.{Colors.RESET}")
        elif user_input: # Assumed to be a name for broad search
            term_to_search = user_input
            print(f"\nPerforming broad search for '{Colors.CYAN}{term_to_search}{Colors.RESET}' across all bundles...")
            print(f"{Colors.YELLOW}Note: Broad search may include non-sprite bundles or unrelated files.{Colors.RESET}")
            
            new_finds_broad_search = 0
            found_during_this_broad_search = []

            for item_name in os.listdir(base_path): # Scan all files in base_path
                if not item_name.lower().endswith(".bundle"):
                    continue
                if term_to_search in item_name.lower():
                    full_path = os.path.join(base_path, item_name)
                    basename = os.path.basename(full_path)
                    if basename not in master_bundle_basenames: # Only add if truly new
                        ingame_name = get_ingame_name_from_bundle(basename) # Try to get a name anyway
                        bundle_data = {"path": full_path, "basename": basename, "ingame_name": ingame_name, "source": "broad_search"}
                        master_bundle_list.append(bundle_data)
                        found_during_this_broad_search.append(bundle_data)
                        master_bundle_basenames.add(basename)
                        new_finds_broad_search += 1
            
            if new_finds_broad_search > 0:
                master_bundle_list.sort(key=lambda x: x["basename"]) # Re-sort master list
                current_display_list = list(master_bundle_list) # Update display list to the new master
                print(f"Found {new_finds_broad_search} additional bundle(s) containing '{term_to_search}'. List updated.")
            else:
                print(f"No new bundles found containing '{term_to_search}'.")
        else: # Empty input, just re-prompt
            continue


# --- Core Extraction Logic (remains the same) ---
def extract_bundle(bundle_path, output_dir_for_bundle):
    print(f"\n[Sensei's Workshop] Starting extraction for: '{os.path.basename(bundle_path)}'")
    print(f"Outputting to: '{output_dir_for_bundle}'")
    ensure_dir(output_dir_for_bundle)
    try:
        env = UnityPy.load(bundle_path)
        print("Bundle loaded successfully. Reading objects...")
    except Exception as e:
        print(f"{Colors.YELLOW}Error: Failed to load bundle '{bundle_path}'. It might be corrupted, protected, or not a valid Unity bundle.{Colors.RESET}")
        print(f"Details: {e}")
        sys.exit(1)

    manifest = {
        "original_bundle_path": os.path.abspath(bundle_path),
        "script_version": SCRIPT_VERSION,
        "assets": []
    }

    dir_textures = os.path.join(output_dir_for_bundle, "Textures")
    dir_textassets = os.path.join(output_dir_for_bundle, "TextAssets")
    dir_monobehaviours_json = os.path.join(output_dir_for_bundle, "MonoBehaviours_JSON")
    dir_monobehaviours_dat = os.path.join(output_dir_for_bundle, "MonoBehaviours_DAT")
    dir_audioclips = os.path.join(output_dir_for_bundle, "AudioClips")
    dir_other = os.path.join(output_dir_for_bundle, "OtherAssets")

    ensure_dir(dir_textures); ensure_dir(dir_textassets); ensure_dir(dir_monobehaviours_json);
    ensure_dir(dir_monobehaviours_dat); ensure_dir(dir_audioclips); ensure_dir(dir_other)

    total_objects = len(env.objects)
    print(f"Found {total_objects} assets in the bundle.")

    for i, obj in enumerate(env.objects):
        asset_info = {"path_id": obj.path_id, "type": str(obj.type.name), "name": "", "extracted_filename": ""}
        print(f"\rProcessing asset {i+1}/{total_objects} (Type: {obj.type.name})...", end="", flush=True)
        try:
            data = obj.read()
            asset_name_original = getattr(data, "m_Name", "")
            asset_name = sanitize_name(asset_name_original)
            if not asset_name: asset_name = f"{sanitize_name(str(obj.type.name))}_{obj.path_id}"
            asset_info["name"] = asset_name_original 
            processed = False
            if obj.type.name in ["Texture2D", "Sprite"]:
                try:
                    filename = f"{asset_name}_{obj.path_id}.png"
                    filepath = os.path.join(dir_textures, filename)
                    img = data.image
                    if img: img.save(filepath); asset_info["extracted_filename"] = os.path.join("Textures", filename); processed = True
                except Exception as e: print(f"\n    {Colors.YELLOW}Warning: Error saving {obj.type.name} {asset_name}: {e}{Colors.RESET}")
            elif obj.type.name == "TextAsset":
                filename_txt = f"{asset_name}_{obj.path_id}.txt"; filepath_txt = os.path.join(dir_textassets, filename_txt)
                filename_bytes = f"{asset_name}_{obj.path_id}.bytes"; filepath_bytes = os.path.join(dir_textassets, filename_bytes)
                saved_as = ""
                try:
                    script_content = data.script
                    if isinstance(script_content, bytes):
                        try: text_content = script_content.decode('utf-8', errors='replace'); open(filepath_txt, "w", encoding="utf-8").write(text_content); saved_as = os.path.join("TextAssets", filename_txt)
                        except UnicodeDecodeError: open(filepath_bytes, "wb").write(script_content); saved_as = os.path.join("TextAssets", filename_bytes)
                    elif isinstance(script_content, str): open(filepath_txt, "w", encoding="utf-8").write(script_content); saved_as = os.path.join("TextAssets", filename_txt)
                    if saved_as: asset_info["extracted_filename"] = saved_as; processed = True
                except Exception as e: print(f"\n    {Colors.YELLOW}Warning: Error saving TextAsset {asset_name}: {e}{Colors.RESET}")
            elif obj.type.name == "MonoBehaviour":
                if obj.serialized_type and obj.serialized_type.nodes:
                    try:
                        tree = obj.read_typetree(); filename = f"{asset_name}_{obj.path_id}.json"; filepath = os.path.join(dir_monobehaviours_json, filename)
                        with open(filepath, "w", encoding="utf-8") as f: json.dump(tree, f, indent=4)
                        asset_info["extracted_filename"] = os.path.join("MonoBehaviours_JSON", filename); processed = True
                    except Exception: pass
                if not processed:
                    try:
                        raw_data_bytes = None
                        if hasattr(obj, 'raw_data'): raw_data_bytes = obj.raw_data
                        elif hasattr(data, 'raw_data') and isinstance(data.raw_data, bytes): raw_data_bytes = data.raw_data
                        elif hasattr(data, 'm_Script') and isinstance(data.m_Script, bytes): raw_data_bytes = data.m_Script
                        if raw_data_bytes:
                            filename_dat = f"{asset_name}_{obj.path_id}.dat"; filepath_dat = os.path.join(dir_monobehaviours_dat, filename_dat)
                            open(filepath_dat, "wb").write(raw_data_bytes)
                            asset_info["extracted_filename"] = os.path.join("MonoBehaviours_DAT", filename_dat); asset_info["type"] = "MonoBehaviour_DAT"; processed = True
                    except Exception as e_raw: print(f"\n    {Colors.YELLOW}Warning: Failed to save MonoBehaviour {asset_name} as raw data: {e_raw}{Colors.RESET}")
            elif obj.type.name == "AudioClip":
                try:
                    if data.m_AudioData:
                        exported_name = f"{asset_name}_{obj.path_id}"; potential_export_result = data.export()
                        if isinstance(potential_export_result, str) and os.path.exists(potential_export_result):
                            actual_export_filename = os.path.basename(potential_export_result); target_filepath = os.path.join(dir_audioclips, actual_export_filename)
                            if os.path.abspath(potential_export_result) != os.path.abspath(target_filepath): os.rename(potential_export_result, target_filepath)
                            asset_info["extracted_filename"] = os.path.join("AudioClips", actual_export_filename); processed = True
                        elif isinstance(potential_export_result, bytes):
                            audio_filename = f"{exported_name}.wav"; target_filepath = os.path.join(dir_audioclips, audio_filename)
                            open(target_filepath, "wb").write(potential_export_result)
                            asset_info["extracted_filename"] = os.path.join("AudioClips", audio_filename); processed = True
                        else:
                            filename = f"{asset_name}_{obj.path_id}.audioclipraw"; filepath = os.path.join(dir_audioclips, filename)
                            open(filepath, "wb").write(data.m_AudioData)
                            asset_info["extracted_filename"] = os.path.join("AudioClips", filename); processed = True
                except Exception as e: print(f"\n    {Colors.YELLOW}Warning: Error saving AudioClip {asset_name}: {e}{Colors.RESET}")
            if not processed:
                try:
                    raw_obj_data = obj.get_raw_data() if hasattr(obj, 'get_raw_data') else obj.raw_data
                    if raw_obj_data and isinstance(raw_obj_data, bytes):
                        filename = f"{asset_name}_{obj.path_id}.genericdat"; filepath = os.path.join(dir_other, filename)
                        open(filepath, "wb").write(raw_obj_data)
                        asset_info["extracted_filename"] = os.path.join("OtherAssets", filename); asset_info["type"] += "_genericdat"
                except Exception as e_gen: print(f"\n    {Colors.YELLOW}Warning: Could not save generic asset {asset_name} (Type: {obj.type.name}): {e_gen}{Colors.RESET}")
            if asset_info["extracted_filename"]: manifest["assets"].append(asset_info)
        except Exception as e:
            print(f"\n  {Colors.YELLOW}Major error processing object PathID {obj.path_id} (Type: {obj.type.name}): {e}{Colors.RESET}")
            asset_info["extracted_filename"] = "ERROR_EXTRACTING"; asset_info["name"] = asset_info.get("name") or f"UnknownName_{obj.path_id}"; manifest["assets"].append(asset_info)
    print("\nExtraction process finished.")
    manifest_path = os.path.join(output_dir_for_bundle, "manifest.json")
    open(manifest_path, "w", encoding="utf-8").write(json.dumps(manifest, indent=4))
    print(f"Manifest saved to '{manifest_path}'")
    print(f"{Colors.CYAN}せんせい、抽出が完了しました！{Colors.RESET} (Extraction complete, Sensei!)")

# --- Core Repacking Logic (remains the same) ---
def repack_bundle(input_dir_with_manifest, output_bundle_full_path):
    print(f"\n[Sensei's Workshop] Repacking assets from: '{input_dir_with_manifest}'")
    print(f"Outputting new bundle to: '{output_bundle_full_path}'")
    manifest_path = os.path.join(input_dir_with_manifest, "manifest.json")
    if not os.path.exists(manifest_path): print(f"{Colors.YELLOW}Error: manifest.json not found in '{input_dir_with_manifest}'. Cannot repack.{Colors.RESET}"); return
    with open(manifest_path, "r", encoding="utf-8") as f: manifest = json.load(f)
    original_bundle_path = manifest.get("original_bundle_path")
    if not original_bundle_path or not os.path.exists(original_bundle_path): print(f"{Colors.YELLOW}Error: Original bundle path '{original_bundle_path}' from manifest is invalid or not found.{Colors.RESET}"); return
    print(f"Using original bundle '{os.path.basename(original_bundle_path)}' as template.")
    env = UnityPy.load(original_bundle_path)
    modified_count = 0; total_assets_in_manifest = len(manifest["assets"])
    print(f"Found {total_assets_in_manifest} assets in manifest to process.")
    for idx, asset_entry in enumerate(manifest["assets"]):
        if asset_entry["extracted_filename"] == "ERROR_EXTRACTING" or not asset_entry["extracted_filename"]: continue
        original_path_id = asset_entry["path_id"]; extracted_file_rel_path = asset_entry["extracted_filename"]
        asset_type = asset_entry["type"]; asset_name_from_manifest = asset_entry.get("name", f"Unnamed_PathID_{original_path_id}")
        modified_file_path = os.path.join(input_dir_with_manifest, extracted_file_rel_path)
        print(f"\rProcessing asset {idx+1}/{total_assets_in_manifest} (PathID: {original_path_id}, Name: {asset_name_from_manifest[:30]}...).", end="", flush=True)
        if os.path.exists(modified_file_path):
            target_obj = next((obj for obj in env.objects if obj.path_id == original_path_id), None)
            if target_obj:
                try:
                    data = target_obj.read(); asset_updated = False
                    if asset_type in ["Texture2D", "Sprite"]: img = Image.open(modified_file_path); data.image = img; data.save(); asset_updated = True
                    elif asset_type == "TextAsset":
                        with open(modified_file_path, "rb") as f: new_script_bytes = f.read()
                        if isinstance(data.script, str):
                            try: data.script = new_script_bytes.decode('utf-8')
                            except UnicodeDecodeError: data.script = new_script_bytes
                        else: data.script = new_script_bytes
                        data.save(); asset_updated = True
                    elif asset_type == "MonoBehaviour_JSON":
                        with open(modified_file_path, "r", encoding="utf-8") as f: new_tree = json.load(f)
                        target_obj.save_typetree(new_tree); asset_updated = True
                    elif asset_type == "MonoBehaviour_DAT":
                        with open(modified_file_path, "rb") as f: raw_mb_data = f.read()
                        if hasattr(data, 'm_Script') and isinstance(data.m_Script, bytes): data.m_Script = raw_mb_data; data.save(); asset_updated = True
                        elif hasattr(data, 'raw_data') and isinstance(data.raw_data, bytes): data.raw_data = raw_mb_data; data.save(); asset_updated = True
                    elif asset_type.startswith("AudioClip"):
                        if hasattr(data, 'm_AudioData'):
                            with open(modified_file_path, "rb") as f: new_audio_data_bytes = f.read()
                            data.m_AudioData = new_audio_data_bytes
                            if hasattr(data, 'm_Size'): data.m_Size = len(new_audio_data_bytes)
                            data.save(); asset_updated = True
                    elif asset_type.endswith("_genericdat"):
                        with open(modified_file_path, "rb") as f: raw_generic_data = f.read()
                        if hasattr(target_obj, 'raw_data'): target_obj.raw_data = raw_generic_data; asset_updated = True
                        else: print(f"\n    {Colors.YELLOW}Generic asset {asset_name_from_manifest}: No direct raw_data field on target_obj. Skipped repacking.{Colors.RESET}")
                    if asset_updated: modified_count += 1
                except Exception as e: print(f"\n    {Colors.YELLOW}Error updating PathID {original_path_id} ({asset_name_from_manifest}) from '{extracted_file_rel_path}': {e}{Colors.RESET}")
    print("\nRepacking process finished.")
    if modified_count > 0:
        try:
            output_bundle_dir = os.path.dirname(os.path.abspath(output_bundle_full_path)); ensure_dir(output_bundle_dir)
            with open(output_bundle_full_path, "wb") as f: f.write(env.file.save())
            print(f"Repacking complete! {modified_count} asset(s) potentially modified.")
            print(f"New bundle saved to: '{output_bundle_full_path}'")
            print(f"{Colors.CYAN}任務完了、せんせい！{Colors.RESET} (Mission complete, Sensei!)")
        except Exception as e: print(f"{Colors.YELLOW}Error saving repacked bundle to '{output_bundle_full_path}': {e}{Colors.RESET}")
    else:
        print("Repacking complete. No assets were modified or no modifiable files were found/matched.")
        if not os.path.exists(output_bundle_full_path) and original_bundle_path and os.path.exists(original_bundle_path):
            print(f"'{output_bundle_full_path}' was not written as no changes were applied.")
        elif os.path.exists(output_bundle_full_path):
            print(f"'{output_bundle_full_path}' might be identical to the original or previous version if no effective changes were made.")

# --- Main Function and Argparse (remains the same) ---
def main():
    print_ba_header()
    ensure_dir(DEFAULT_EXTRACTED_OUTPUT_BASE_DIR)
    ensure_dir(DEFAULT_REPACKED_OUTPUT_DIR)

    parser = argparse.ArgumentParser(
        description=f"Kivotos Halo Asset Tool (v{SCRIPT_VERSION}) - Extract and repack Unity .bundle files for Blue Archive.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"""
Default Paths:
  Bundle Source: {BLUE_ARCHIVE_BUNDLE_SRC_PATH}
  Extracted Output: {DEFAULT_EXTRACTED_OUTPUT_BASE_DIR}<bundle_name_or_custom_name>/
  Repacked Output: {DEFAULT_REPACKED_OUTPUT_DIR}<output_filename.bundle>

Examples:
  To extract (bundle selected interactively, output to {DEFAULT_EXTRACTED_OUTPUT_BASE_DIR}<bundle_name>/):
    python %(prog)s extract

  To extract (bundle selected interactively, output to {DEFAULT_EXTRACTED_OUTPUT_BASE_DIR}MyCustomStudentFolder/):
    python %(prog)s extract MyCustomStudentFolder

  To repack (e.g., from {DEFAULT_EXTRACTED_OUTPUT_BASE_DIR}MyCustomStudentFolder/):
    python %(prog)s repack "{os.path.join(DEFAULT_EXTRACTED_OUTPUT_BASE_DIR, "MyCustomStudentFolder")}" RepackedStudent.bundle
      (Output will be: {os.path.join(DEFAULT_REPACKED_OUTPUT_DIR, "RepackedStudent.bundle")})
"""
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command to execute: 'extract' or 'repack'")

    parser_extract = subparsers.add_parser("extract", help="Extract a bundle (selected interactively from Blue Archive path).")
    parser_extract.add_argument(
        "output_subfolder_name", nargs='?', default=None,
        help=(f"Optional: Custom name for the subfolder within '{DEFAULT_EXTRACTED_OUTPUT_BASE_DIR}'. If omitted, uses the bundle's name.")
    )

    parser_repack = subparsers.add_parser("repack", help="Repack a directory into a new .bundle file.")
    parser_repack.add_argument(
        "input_dir",
        help=f"Directory containing extracted assets and manifest.json (e.g., a subfolder within '{DEFAULT_EXTRACTED_OUTPUT_BASE_DIR}')."
    )
    parser_repack.add_argument(
        "output_filename",
        help=f"Filename for the new repacked .bundle (e.g., 'MyRepackedBundle.bundle'). It will be saved in '{DEFAULT_REPACKED_OUTPUT_DIR}'."
    )

    args = parser.parse_args()

    if args.command == "extract":
        selected_bundle_path, selected_bundle_name_no_ext = select_bundle_interactive(BLUE_ARCHIVE_BUNDLE_SRC_PATH)
        if not selected_bundle_path:
            print("No bundle selected for extraction. Exiting, Sensei.")
            sys.exit(0)
        print(f"Selected bundle for extraction: {os.path.basename(selected_bundle_path)}")
        output_dir_name_base = sanitize_name(args.output_subfolder_name) if args.output_subfolder_name else sanitize_name(selected_bundle_name_no_ext)
        if not output_dir_name_base: # Fallback if sanitization results in empty
            output_dir_name_base = "untitled_extraction"
            print(f"{Colors.YELLOW}Warning: Output folder name was invalid or empty after sanitization. Using '{output_dir_name_base}'.{Colors.RESET}")
        output_directory_for_this_bundle = os.path.join(DEFAULT_EXTRACTED_OUTPUT_BASE_DIR, output_dir_name_base)
        extract_bundle(selected_bundle_path, output_directory_for_this_bundle)

    elif args.command == "repack":
        input_dir_abs = os.path.abspath(args.input_dir)
        if not os.path.isdir(input_dir_abs): print(f"{Colors.YELLOW}Error: Input directory for repacking '{input_dir_abs}' not found.{Colors.RESET}"); sys.exit(1)
        if not os.path.exists(os.path.join(input_dir_abs, "manifest.json")): print(f"{Colors.YELLOW}Error: manifest.json not found in '{input_dir_abs}'. Not a valid extracted bundle folder.{Colors.RESET}"); sys.exit(1)
        sane_output_filename = sanitize_name(args.output_filename)
        if not sane_output_filename: print(f"{Colors.YELLOW}Error: Output filename is invalid after sanitization.{Colors.RESET}"); sys.exit(1)
        if not any(sane_output_filename.lower().endswith(ext) for ext in ['.bundle', '.unity3d', '.asset', '.assets']):
            print(f"{Colors.YELLOW}Warning: Output filename '{sane_output_filename}' lacks a common bundle extension (e.g., '.bundle').{Colors.RESET}")
        final_repacked_bundle_path = os.path.join(DEFAULT_REPACKED_OUTPUT_DIR, sane_output_filename)
        repack_bundle(input_dir_abs, final_repacked_bundle_path)

if __name__ == "__main__":
    if "com.termux" in os.environ.get("PREFIX", "") or "/sdcard/" in str(os.getcwd()):
        print("Android-like environment detected. Using /sdcard/ paths.")
    # This simple check for os.name helps with color on Windows if an ANSI-supporting terminal isn't used.
    # However, most modern Windows terminals (Windows Terminal, VSCode terminal) support ANSI.
    # if os.name == 'nt': # For Windows, if not using a modern terminal, ANSI codes might not work.
    #     os.system('color') # This sometimes enables ANSI support in older cmd.exe, but not reliably.
    main()
