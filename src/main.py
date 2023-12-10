import os
import ctypes
import requests
import shutil
import zipfile
import subprocess
import time
import psutil
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        return False

def run_as_admin():
    if is_admin():
        return True

    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

def download_latest_release(destination_path, headers=None):
    github_api_url = "https://api.github.com/repos/edwardnafornita/lcmod/releases/133309022"

    try:
        response = requests.get(github_api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        assets = data.get('assets', [])
        if isinstance(assets, list) and assets:
            download_url = assets[0].get('browser_download_url')

            response = requests.get(download_url)
            with open('latest_files.zip', 'wb') as f:
                f.write(response.content)

            with zipfile.ZipFile('latest_files.zip', 'r') as zip_ref:
                zip_ref.extractall(destination_path)

            os.remove('latest_files.zip')

            print("Download and extraction successful.")
        else:
            print("No valid assets found in the release.")

    except requests.RequestException as e:
        print(f"Error downloading latest release from GitHub: {e}")

def get_user_steam_path():
    steam_path = input("Enter the path to your Lethal Company installation (e.g., C:\\Program Files (x86)\\Steam\\...): \n")
    if os.path.exists(steam_path):
        return steam_path
    else:
        print("Invalid path. Please make sure the path exists.")
        return None

def move_folder_contents(src_folder, dest_folder):
    for item in os.listdir(src_folder):
        s = os.path.join(src_folder, item)
        d = os.path.join(dest_folder, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
            shutil.rmtree(s)
        else:
            shutil.copy2(s, d)
            os.remove(s)

def launch_and_wait(executable_path, wait_time_seconds=30):
    try:
        # Launch the subprocess in the background
        process = subprocess.Popen([executable_path], shell=True)

        time.sleep(wait_time_seconds)

        process.terminate()

    except Exception as e:
        print(f"Error launching {executable_path}: {e}")

def terminate_process(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            psutil.Process(process.info['pid']).terminate()

def replace_line_in_file(file_path, search_str, replace_str):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            if search_str in line:
                file.write(replace_str + '\n')
            else:
                file.write(line)

def run_update():
    try:
        run_as_admin()
        steam_path = get_user_steam_path()

        if steam_path:
            print("Downloading latest version of the Lethal Company Modpack.")
            download_latest_release(steam_path)
            
            print("Checking for existing BepInEx files.")
            backbone_api_src = os.path.join(steam_path, 'assets', 'backbone_api')
            backbone_api_dest = os.path.join(steam_path, 'BepInEx')

            # Check if backbone_api files already exist in the root directory
            if os.path.exists(backbone_api_dest):
                print("Existing BepInEx files found. Skipping extraction.")
            else:
                print("Moving BepInEx files to root directory.")
                move_folder_contents(backbone_api_src, steam_path)

                print("Launching Lethal Company to generate core files.\n")
                lethal_company_exe_path = os.path.join(steam_path, 'Lethal Company.exe')
                launch_and_wait(lethal_company_exe_path)

                # print("Terminating Lethal Company process after 30 seconds.")
                # terminate_process("Lethal Company.exe")
                print("Modifying BepInEx configuration file to set the HideManagerGameObject variable to true.")
                bepinex_cfg_path = os.path.join(steam_path, 'BepInEx', 'config', 'BepInEx.cfg')
                replace_line_in_file(bepinex_cfg_path, 'HideManagerGameObject = false', 'HideManagerGameObject = true')

            print("Moving plugin files to plugin directory located in the BepInEx directory.")
            mods_src = os.path.join(steam_path, 'assets', 'mods')
            plugins_dest = os.path.join(steam_path, 'BepInEx', 'plugins')
            move_folder_contents(mods_src, plugins_dest)

            print("Removing temporary files.")
            asset_dir = os.path.join(steam_path, 'assets')
            shutil.rmtree(asset_dir)

            print("Update completed successfully.")
        else:
            print("Steam not found. Update aborted.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_update()
    input("Press Enter to close the command prompt.")
