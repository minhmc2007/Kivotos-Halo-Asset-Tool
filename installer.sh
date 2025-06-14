#!/bin/bash

#================================================================
# Kivotos Hybrid Tool - All-in-One Installer v2 (with Deploy)
#
# This script will:
# 1. Create the 'kivotos_tool.py' orchestrator script with deploy functionality.
# 2. Update Termux packages & install proot-distro.
# 3. Install 'rish' if found locally.
# 4. Install and configure a Debian container.
# 5. Install all Python dependencies inside Debian.
#================================================================

# --- Color Codes for beautiful output ---
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Configuration ---
TOOL_FILENAME="kivotos_tool.py"
CONTAINER_NAME="debian"
PYTHON_TOOL_DEPS="python3 python3-pip"
PYTHON_PIP_DEPS="unity-bundle-tool pillow unitypy"

# --- Helper function for printing headers ---
print_header() {
    echo -e "\n${CYAN}==============================================${NC}"
    echo -e "${CYAN} $1 ${NC}"
    echo -e "${CYAN}==============================================${NC}"
}

# --- Start of the script ---
clear
echo -e "${GREEN}せんせい、ようこそ！(Welcome, Sensei!)${NC}"
echo "This script will automatically set up the Kivotos Hybrid Tool environment."
read -p "Press [Enter] to begin the installation..."

#================================================
# STEP 1: CREATE THE MAIN TOOL SCRIPT
#================================================
print_header "Step 1: Creating the Main Tool Script (with Deploy)"

# Using a 'heredoc' to write the Python script to a file.
cat <<'EOF' > "$TOOL_FILENAME"
#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import glob

# --- Configuration ---
BLUE_ARCHIVE_BUNDLE_SRC_PATH = "/sdcard/Android/data/com.nexon.bluearchive/files/PUB/Resource/GameData/Android/"
DEFAULT_WORKSPACE_BASE = "/sdcard/BA_Workspace/"
RISH_PATH = "/data/data/com.termux/files/usr/bin/rish"
PROOT_CONTAINER_NAME = "debian" 

# --- ANSI Color Codes ---
class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

# --- Helper Functions ---
def run_privileged_command(cmd_prefix, command_str):
    full_command = cmd_prefix + [command_str]
    env = None
    if 'rish' in cmd_prefix[0]:
        env = os.environ.copy()
        env['RISH_APPLICATION_ID'] = 'com.termux'
    
    try:
        result = subprocess.run(
            full_command, 
            capture_output=True, 
            text=True, 
            check=False,
            env=env
        )
        if result.returncode == 0:
            return result
        else:
            print(f"\n{Colors.RED}--- PRIVILEGED COMMAND FAILED ---{Colors.RESET}")
            print(f"  Command: {' '.join(full_command)}")
            print(f"  Return Code: {result.returncode}")
            if result.stderr:
                print(f"  {Colors.YELLOW}Error (stderr):\n{result.stderr.strip()}{Colors.RESET}")
            raise subprocess.CalledProcessError(result.returncode, full_command)
    except Exception as e:
        print(f"{Colors.RED}An unexpected Python error occurred: {e}{Colors.RESET}")
        raise

def get_access_method():
    print("Probing for high-privilege access method...")
    try:
        subprocess.run(['su', '-c', 'id -u'], check=True, capture_output=True)
        print(f"  {Colors.GREEN}Root (su) access detected.{Colors.RESET}")
        return ['su', '-c'], 'su'
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  {Colors.YELLOW}Root (su) not available.{Colors.RESET} Checking for Shizuku...")

    if os.path.exists(RISH_PATH):
        print(f"  {Colors.GREEN}Shizuku (rish) access detected.{Colors.RESET}")
        return [RISH_PATH, '-c'], 'rish'

    return None, 'manual_setup_required'

# --- Main Logic ---
def main():
    parser = argparse.ArgumentParser(
        description="Kivotos Hybrid Operations Tool - The Orchestrator",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_copy = subparsers.add_parser("copy", help="Copy bundles from protected storage to your workspace.")
    parser_copy.add_argument("search_term", help="Name to search for in bundle filenames (e.g., 'yuuka').")
    parser_copy.add_argument("workspace_folder", help="Name for the new folder in your workspace (e.g., 'yuuka_mod').")

    parser_process = subparsers.add_parser("process", help="Tell the proot-distro to process bundles with 'ubt'.")
    process_subparsers = parser_process.add_subparsers(dest="action", required=True)
    
    parser_extract = process_subparsers.add_parser("extract", help="Extract all bundles in a workspace folder.")
    parser_extract.add_argument("workspace_folder", help="Name of the folder in your workspace to process.")

    parser_repack = process_subparsers.add_parser("repack", help="Repack an extracted folder.")
    parser_repack.add_argument("workspace_folder", help="Name of the folder in your workspace to repack.")
    parser_repack.add_argument("output_name", help="Filename for the new repacked bundle (e.g., 'modded_yuuka.bundle').")

    # --- NEW 'deploy' COMMAND ---
    parser_deploy = subparsers.add_parser("deploy", help="Copy a modded bundle back into the game directory.")
    parser_deploy.add_argument("modded_bundle_path", help="Path to your repacked bundle file.")
    parser_deploy.add_argument("original_bundle_name", help="The EXACT filename of the original bundle you are replacing.")

    args = parser.parse_args()

    # Shared access method logic
    cmd_prefix, method = None, None
    if args.command in ["copy", "deploy"]:
        cmd_prefix, method = get_access_method()
        if method == 'manual_setup_required':
            print(f"\n{Colors.RED}--- ACTION REQUIRED ---{Colors.RESET}")
            print("This operation requires root or Shizuku. Please set it up.")
            print("Open Shizuku app -> Use in terminal apps -> Export files -> Select Termux -> USE THIS FOLDER.")
            sys.exit(1)

    # ================= COMMAND LOGIC =================

    if args.command == "copy":
        print(f"\n{Colors.CYAN}--- Operation: COPY ---{Colors.RESET}")
        dest_dir = os.path.join(DEFAULT_WORKSPACE_BASE, args.workspace_folder)
        try:
            print(f"Searching for '{args.search_term}' and copying to '{dest_dir}'...")
            os.makedirs(DEFAULT_WORKSPACE_BASE, exist_ok=True)
            subprocess.run(['chmod', '777', DEFAULT_WORKSPACE_BASE], check=True)
            os.makedirs(dest_dir, exist_ok=True)
            subprocess.run(['chmod', '777', dest_dir], check=True)
            
            print("Listing remote files...")
            result = run_privileged_command(cmd_prefix, f"ls '{BLUE_ARCHIVE_BUNDLE_SRC_PATH}'")
            files_to_copy = [f for f in result.stdout.strip().split('\n') if args.search_term.lower() in f.lower() and f.lower().endswith('.bundle')]
            
            if not files_to_copy:
                print(f"{Colors.YELLOW}No bundles found containing '{args.search_term}'.{Colors.RESET}")
                return

            print(f"Found {len(files_to_copy)} bundles. Copying...")
            for filename in files_to_copy:
                print(f"  - {Colors.CYAN}{filename}{Colors.RESET}")
                src = os.path.join(BLUE_ARCHIVE_BUNDLE_SRC_PATH, filename)
                dest = os.path.join(dest_dir, filename)
                run_privileged_command(cmd_prefix, f"cp '{src}' '{dest}'")
            print(f"\n{Colors.GREEN}Copy complete, Sensei!{Colors.RESET}")

        except Exception:
            print(f"\n{Colors.RED}An error occurred during the copy operation. Aborting.{Colors.RESET}")
            sys.exit(1)

    elif args.command == "process":
        print(f"\n{Colors.CYAN}--- Operation: PROCESS (Remote Control) ---{Colors.RESET}")
        workspace_dir = os.path.join(DEFAULT_WORKSPACE_BASE, args.workspace_folder)

        if args.action == "extract":
            print(f"Telling Debian to extract all bundles in '{workspace_dir}'...")
            for bundle_path in glob.glob(os.path.join(workspace_dir, "*.bundle")):
                output_folder = os.path.splitext(bundle_path)[0]
                print(f"  - Extracting {os.path.basename(bundle_path)}...")
                proot_cmd = f"proot-distro login {PROOT_CONTAINER_NAME} -- ubt extract '{bundle_path}' '{output_folder}'"
                subprocess.run(proot_cmd, shell=True, check=True)
            print(f"\n{Colors.GREEN}Extraction complete, Sensei!{Colors.RESET}")

        elif args.action == "repack":
            repack_source_dir = os.path.join(DEFAULT_WORKSPACE_BASE, args.workspace_folder)
            output_path = os.path.join(DEFAULT_WORKSPACE_BASE, args.output_name)
            print(f"Telling Debian to repack '{repack_source_dir}' into '{output_path}'...")
            proot_cmd = f"proot-distro login {PROOT_CONTAINER_NAME} -- ubt repack '{repack_source_dir}' '{output_path}'"
            subprocess.run(proot_cmd, shell=True, check=True)
            print(f"\n{Colors.GREEN}Repacking complete, Sensei!{Colors.RESET}")

    elif args.command == "deploy":
        print(f"\n{Colors.CYAN}--- Operation: DEPLOY ---{Colors.RESET}")
        modded_bundle_path = os.path.abspath(args.modded_bundle_path)
        if not os.path.exists(modded_bundle_path):
            print(f"{Colors.RED}Error: Modded bundle '{modded_bundle_path}' not found.{Colors.RESET}")
            sys.exit(1)
        
        target_path_in_game = os.path.join(BLUE_ARCHIVE_BUNDLE_SRC_PATH, args.original_bundle_name)
        
        print(f"Deploying '{os.path.basename(modded_bundle_path)}'")
        print(f"       to '{target_path_in_game}'")
        
        # SAFETY CHECK
        user_confirm = input(f"{Colors.YELLOW}This will overwrite the original game file. Are you sure? (y/n): {Colors.RESET}").lower()
        if user_confirm != 'y':
            print("Deploy cancelled by user.")
            sys.exit(0)
            
        try:
            print("Attempting to deploy file to protected storage...")
            # We use `dd` for a more robust, direct overwrite.
            deploy_command = f"dd if='{modded_bundle_path}' of='{target_path_in_game}'"
            run_privileged_command(cmd_prefix, deploy_command)
            print(f"\n{Colors.GREEN}Deploy successful! Your mod is now in the game.{Colors.RESET}")
            print(f"{Colors.YELLOW}Note: You may need to clear the game's cache or restart the game for changes to apply.{Colors.RESET}")
        except Exception:
            print(f"\n{Colors.RED}An error occurred during the deploy operation. Aborting.{Colors.RESET}")
            sys.exit(1)

if __name__ == "__main__":
    main()
EOF

# Make the newly created python script executable
chmod +x "$TOOL_FILENAME"
echo -e "${GREEN}Successfully created the main tool: '$TOOL_FILENAME'${NC}"

#================================================
# STEP 2: SETUP TERMUX HOST ENVIRONMENT
#================================================
print_header "Step 2: Setting up Termux Environment"
echo "Updating and upgrading Termux packages..."
pkg update -y && pkg upgrade -y
echo "Installing proot-distro..."
pkg install proot-distro -y
if [ -f "/data/data/com.termux/files/usr/bin/rish" ]; then
    echo -e "${GREEN}Shizuku (rish) is already installed correctly. Skipping.${NC}"
else
    if [ -f "$HOME/rish" ] && [ -f "$HOME/rish_shizuku.dex" ]; then
        echo -e "${YELLOW}Found local 'rish' files. Installing...${NC}"
        mv "$HOME/rish" "$HOME/rish_shizuku.dex" "/data/data/com.termux/files/usr/bin/"
        chmod +x "/data/data/com.termux/files/usr/bin/rish"
        echo -e "${GREEN}Successfully installed 'rish'.${NC}"
    else
        echo -e "${YELLOW}Warning: 'rish' not found. If you don't have root, you must set it up manually later.${NC}"
    fi
fi

#================================================
# STEP 3: SETUP DEBIAN PROOT CONTAINER
#================================================
print_header "Step 3: Setting up Debian Proot Container"
if proot-distro list | grep -q "$CONTAINER_NAME"; then
    echo -e "${GREEN}Debian container is already installed. Skipping installation.${NC}"
else
    echo "Debian container not found. Installing now... (This may take a while)"
    proot-distro install "$CONTAINER_NAME"
fi
echo "Updating package lists inside Debian..."
proot-distro login "$CONTAINER_NAME" -- apt-get update -y > /dev/null 2>&1
echo "Installing Python and Pip inside Debian..."
proot-distro login "$CONTAINER_NAME" -- apt-get install -y $PYTHON_TOOL_DEPS
echo "Installing 'ubt' and other Python dependencies inside Debian..."
proot-distro login "$CONTAINER_NAME" -- bash -c "
    echo 'Attempting to install Python packages with pip...'
    pip3 install --upgrade pip > /dev/null 2>&1
    pip3 install --break-system-packages $PYTHON_PIP_DEPS
    if [ \$? -eq 0 ]; then
        echo -e '${GREEN}Python dependencies installed successfully.${NC}'
    else
        echo -e '${RED}Failed to install Python dependencies.${NC}'
        exit 1
    fi
"
if [ $? -ne 0 ]; then
    echo -e "${RED}A critical error occurred while setting up the Debian container. Aborting.${NC}"
    exit 1
fi

#================================================
# STEP 4: FINALIZATION
#================================================
print_header "Step 4: Installation Complete!"
echo -e "${GREEN}任務完了、せんせい！ (Mission complete, Sensei!)${NC}"
echo ""
echo -e "The main tool has been created as ${GREEN}'$TOOL_FILENAME'${NC} in this directory."
echo ""
echo -e "A full modding workflow would be:"
echo -e "1. ${CYAN}./${TOOL_FILENAME} copy <name> <folder>${NC}"
echo -e "2. ${CYAN}./${TOOL_FILENAME} process extract <folder>${NC}"
echo -e "3. ${YELLOW}(Edit your files in /sdcard/BA_Workspace/<folder>/...)${NC}"
echo -e "4. ${CYAN}./${TOOL_FILENAME} process repack <subfolder_to_repack> <mod_name.bundle>${NC}"
echo -e "5. ${CYAN}./${TOOL_FILENAME} deploy /sdcard/BA_Workspace/<mod_name.bundle> <original_name.bundle>${NC}"
echo ""
echo -e "Thank you for using the Kivotos Hybrid Tool Installer!"
