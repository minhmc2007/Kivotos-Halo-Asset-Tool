# Kivotos Halo Asset Tool

![Preview](exam.png)

A complete, on-device solution for modding **Blue Archive** on Android. This tool provides a powerful command-line interface to copy, extract, repack, and deploy Unity asset bundles directly on your phone.

It features a hybrid architecture, using a Termux-based "Orchestrator" to handle high-privilege file operations and a `proot-distro` Linux container as a clean "Workshop" for processing game assets.

せんせい、今日も頑張ってください！ (Sensei, please do your best today!)

![Preview](header.jpg)

---

## Features

*   **End-to-End Workflow:** Supports the full modding cycle: `copy`, `extract`, `repack`, and `deploy`.
*   **Automated Setup:** A single `install.sh` script prepares the entire complex environment for you.
*   **Smart Permission Handling:** Automatically detects and uses `root (su)` or `Shizuku (rish)` to access protected game files.
*   **Hybrid Architecture:**
    *   **Orchestrator (in Termux):** Manages file operations in protected directories.
    *   **Workshop (in Debian):** A clean environment for running asset processing tools.

## Prerequisites

This tool is designed to run exclusively on **Android**. You will need:
1.  **Termux:** The primary terminal emulator for Android.
2.  **High-Privilege Access:** Your device must have one of the following:
    *   **Root Access:** The `su` binary must be available to Termux.
    *   **Shizuku:** The Shizuku app must be installed and running.

## Installation (Recommended for All Users)

The entire setup process is automated. You only need to run one script.

1.  **Download the Installer:**
    Download the `install.sh` script to your Termux home directory (`~/`).

2.  **Make it Executable:**
    Open Termux and run this command to give the script permission to execute:
    ```bash
    chmod +x install.sh
    ```

3.  **Run the Installer:**
    Execute the script. It will handle everything else.
    ```bash
    ./install.sh
    ```

**What the installer does:**
*   Creates the main `kivotos_tool.py` script for you.
*   Installs and configures `proot-distro` with a Debian container.
*   Installs `ubt`, `UnityPy`, `Pillow`, and other dependencies inside the Debian container.
*   Checks for and correctly installs `rish` if you are using Shizuku.

Once it's finished, you are ready to start modding with the `kivotos_tool.py` script.

## The Standard Modding Workflow (`kivotos_tool.py`)

The `kivotos_tool.py` script, created by the installer, provides a straightforward, step-by-step process. All commands are run from the main Termux shell.

1.  **`copy <search_term> <folder>`:** Copies bundles from the game to your workspace.
2.  **`process extract <folder>`:** Extracts the copied bundles.
3.  **Edit Your Files:** Manually modify the extracted assets in `/sdcard/BA_Workspace/`.
4.  **`process repack <subfolder> <new_name.bundle>`:** Repacks your modified folder into a new bundle.
5.  **`deploy <mod_path> <original_name>`:** Deploys your modded bundle back into the game.

---

## 🧑‍🔬 Advanced Alternative (For Nethunter / Pro Users)

For professional users or those running a full-featured root environment like **Kali Nethunter**, a more powerful, all-in-one script is available: `ba_asset_tool.py`.

This version is not created by the installer and must be downloaded separately. It is designed to be run **entirely within a single, root-privileged Linux environment** (like a Nethunter chroot or a `proot-distro` with `tsu`/`sudo`).

### Why use the Advanced Tool?
*   **Powerful Interactive Search:** Features an advanced menu for finding bundles. It performs a "Smart Scan" on startup to find character sprites, allows live filtering, and supports a "Broad Search" to discover new bundles on the fly.
*   **All-in-One Operation:** Extraction and repacking are handled within a single script, without needing to switch between a Termux orchestrator and a Debian worker.
*   **Direct Control:** Offers more direct control over the extraction and repacking process for users who are comfortable managing their own environment.

### Who Should Use This?
*   Users with a **Kali Nethunter** chroot.
*   Advanced users who run their `proot-distro` session with root privileges (e.g., using `tsu` or `sudo`).
*   Users who prefer an interactive menu over a step-by-step command workflow.

### Setup for the Advanced Tool
1.  **Ensure a Root Environment:** You must be inside a shell with root access (`whoami` should return `root`).
2.  **Install Dependencies:**
    ```bash
    pip install UnityPy Pillow
    ```
3.  **Download and Run:**
    Download the `ba_asset_tool.py` script and run it directly.
    ```bash
    python ba_asset_tool.py extract
    ```

**Note:** The standard `kivotos_tool.py` created by the installer is recommended for most users as it handles the complex permission bridging automatically. The advanced `ba_asset_tool.py` offers more power at the cost of requiring a more complex initial setup.

---

## Disclaimer
This is a third-party tool created for educational and personal use. Modifying game files can be against the game's Terms of Service and may lead to unforeseen consequences, including account suspension. Use this tool responsibly and at your own risk. The developer is not responsible for any issues that may arise from its use.
