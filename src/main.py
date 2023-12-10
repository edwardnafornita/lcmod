import os
import sys
import ctypes
import requests
import shutil
import winreg

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        return False
    
def run_as_admin():
    if is_admin():
        return True
    
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def check_for_updates():
    GITHUB_API_URL = "https://github.com/repos/edwardnafornita/lcmod/releases/latest"
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        data = response.json()
        download_url = data['assets'][0]['browser_download_url']
        response = requests.get(download_url)

        with open('latest_files.zip', 'wb') as file:
            file.write(response.contet)
    except requests.RequestException as e:
        print(f"Error checking for updates on GitHub: {e}")
        sys.exit(1)

def copy_files(destination_path):
    with shutil.ZipFile('latest_files.zip', 'r') as zip_ref:
        zip_ref.extractall('temp_folder')

    BACKBONE_API_SRC = os.path.join('temp_folder', 'backbone_api')
    BACKBONE_API_DST = os.path.join(destination_path, 'backbone_api')
    if not os.path.exists(BACKBONE_API_DST):
        shutil.move(BACKBONE_API_SRC, BACKBONE_API_DST)
    else: 
        print("backbone_api folder already exists. Skipping.")

    mods_src = os.path.join('temp_folder', 'mods')
    mods_dst = os.path.join(destination_path, 'mods')
    shutil.move(mods_src, mods_dst)

    shutil.rmtree('temp_folder')

def find_steam_installation():
    try:
        key = r"SOFTWARE\\Valve\\Steam\\steamapps\\common\\Lethal Company"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as reg_key:
            steam_path, _ = winreg.QueryValueEx(reg_key, "InstallPath")
            return steam_path
    except Exception as e:
        print(f"Error finding Steam installtion path: {e}")
        return None
    
if __name__ == "__main__":
    run_as_admin()

    check_for_updates()

    steam_path = find_steam_installation()
    
    if steam_path:
        copy_files(steam_path)
        print("Update successful.")
    else:
        print("Steam not found. Update aborted.")