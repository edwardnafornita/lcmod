import os
import ctypes
import requests
import shutil
import zipfile
import subprocess
import time
import psutil
import sys
import tkinter as tk
from tkinter import filedialog

class UpdateApp:
    def __init__(self, master):
        self.master = master
        master.title("Lethal Company Modpack Updater")

        self.display_ascii_art()

        self.text_area = tk.Text(master, height=20, width=60)
        self.text_area.pack()

        self.run_as_admin()
        button_frame = tk.Frame(master)
        button_frame.pack(pady=10)

        self.run_button = tk.Button(button_frame, text="Run Program", command=self.run_update)
        self.run_button.pack(side=tk.RIGHT, padx=5)

        self.close_button = tk.Button(button_frame, text="Close", command=self.close_app)
        self.close_button.pack(side=tk.RIGHT, padx=5)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            return False

    def run_as_admin(self):
        if self.is_admin():
            return True

        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

    def download_latest_release(self, destination_path, headers=None):
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

                self.update_text("Download and extraction successful.")
            else:
                self.update_text("No valid assets found in the release.")

        except requests.RequestException as e:
            self.update_text(f"Error downloading latest release from GitHub: {e}")

    def get_user_steam_path(self):
        steam_path = filedialog.askdirectory(title="Select Steam Installation Directory")
        if os.path.exists(steam_path):
            return steam_path
        else:
            self.update_text("Invalid path. Please make sure the path exists.")
            return None

    def move_folder_contents(self, src_folder, dest_folder):
        for item in os.listdir(src_folder):
            s = os.path.join(src_folder, item)
            d = os.path.join(dest_folder, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
                shutil.rmtree(s)
            else:
                shutil.copy2(s, d)
                os.remove(s)

    def launch_and_wait(self, executable_path, wait_time_seconds=30):
        try:
            process = subprocess.Popen([executable_path], shell=True)
            time.sleep(wait_time_seconds)
            process.terminate()
        except Exception as e:
            self.update_text(f"Error launching {executable_path}: {e}")

    def terminate_process(self, process_name):
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == process_name:
                psutil.Process(process.info['pid']).terminate()

    def replace_line_in_file(self, file_path, search_str, replace_str):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        with open(file_path, 'w') as file:
            for line in lines:
                if search_str in line:
                    file.write(replace_str + '\n')
                else:
                    file.write(line)

    def update_text(self, message):
        current_text = self.text_area.get("1.0", tk.END)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, current_text + message + "\n")

    def close_app(self):
        self.master.destroy()

    def display_ascii_art(self):
        ascii_art = """
    __         __  __          __   ______                                       
   / /   ___  / /_/ /_  ____ _/ /  / ____/___  ____ ___  ____  ____ _____  __  __
  / /   / _ \/ __/ __ \/ __ `/ /  / /   / __ \/ __ `__ \/ __ \/ __ `/ __ \/ / / /
 / /___/  __/ /_/ / / / /_/ / /  / /___/ /_/ / / / / / / /_/ / /_/ / / / / /_/ / 
/_____/\___/\__/_/ /_/\__,_/_/   \____/\____/_/ /_/ /_/ .___/\__,_/_/ /_/\__, /  
                                                     /_/                /____/   

        Modpack by
            Edward Nafornita
        """
        ascii_label = tk.Label(self.master, text=ascii_art, font=("Courier", 10))
        ascii_label.pack()

    def run_update(self):
        try:
            steam_path = self.get_user_steam_path()

            if steam_path:
                self.download_latest_release(steam_path)

                self.update_text("Checking for existing BepInEx files.")
                backbone_api_src = os.path.join(steam_path, 'assets', 'backbone_api')
                backbone_api_dest = os.path.join(steam_path, 'BepInEx')

                if os.path.exists(backbone_api_dest):
                    self.update_text("Existing BepInEx files found. Skipping extraction.")
                else:
                    self.update_text("Moving BepInEx files to root directory.")
                    self.move_folder_contents(backbone_api_src, steam_path)

                    lethal_company_exe_path = os.path.join(steam_path, 'Lethal Company.exe')
                    self.launch_and_wait(lethal_company_exe_path)
                    self.terminate_process("Lethal Company.exe")

                    bepinex_cfg_path = os.path.join(steam_path, 'BepInEx', 'config', 'BepInEx.cfg')
                    self.replace_line_in_file(bepinex_cfg_path, 'HideManagerGameObject = false', 'HideManagerGameObject = true')

                self.update_text("Moving plugin files to plugin directory located in the BepInEx directory.")
                mods_src = os.path.join(steam_path, 'assets', 'mods')
                plugins_dest = os.path.join(steam_path, 'BepInEx', 'plugins')
                self.move_folder_contents(mods_src, plugins_dest)

                self.update_text("Removing temporary files.")
                asset_dir = os.path.join(steam_path, 'assets')
                shutil.rmtree(asset_dir)

                self.update_text("Update completed successfully.")
            else:
                self.update_text("Steam not found. Update aborted.")

        except Exception as e:
            self.update_text(f"An error occurred: {e}")

# Create the main window
if __name__ == "__main__":
    root = tk.Tk()
    app = UpdateApp(root)
    root.mainloop()
