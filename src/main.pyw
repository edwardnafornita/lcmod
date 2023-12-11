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
from tkinter import messagebox

class UpdateApp:
    def __init__(self, master):
        self.run_as_admin()
        self.master = master
        self.master.title("Lethal Company Modpack Updater")

        self.display_ascii_art()
        
        self.render_gui_fields()

    def render_gui_fields(self):
        button_width = 20
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        self.close_button = tk.Button(button_frame, text="Close", command=self.close_app, width=button_width)
        self.close_button.pack(side=tk.RIGHT, padx=5)

        self.run_button = tk.Button(button_frame, text="Run Program", command=self.run_update, width=button_width)
        self.run_button.pack(side=tk.RIGHT, padx=5)

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
            else:
                self.show_error("No valid assets found in the release.")

        except requests.RequestException as e:
            self.show_error(f"Error downloading latest release from GitHub: {e}")

    def get_user_steam_path(self):
        steam_path = filedialog.askdirectory(title="Select Lethal Company Installation Directory")
        if os.path.exists(steam_path):
            return steam_path
        else:
            self.show_error("Invalid path. Please make sure the path exists.")
            return None

    def delete_folder_contents(seelf, folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    
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

    def replace_line_in_file(self, file_path, search_str, replace_str):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        with open(file_path, 'w') as file:
            for line in lines:
                if search_str in line:
                    file.write(replace_str + '\n')
                else:
                    file.write(line)

    def show_error(self, message):
        messagebox.showerror("Error", message)

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
                bepinex_dest_folder = os.path.join(steam_path, "BepInEx")

                if not os.path.exists(bepinex_dest_folder):
                    self.update_steps = [
                        (self.move_bepinex_files, [os.path.join(steam_path, 'assets', 'backbone_api'), steam_path]),
                        (self.launch_lethal_company, [os.path.join(steam_path, 'Lethal Company.exe')]),
                        (self.modify_bepinex_config, [os.path.join(steam_path, 'BepInEx', 'config', 'BepInEx.cfg')]),
                        (self.move_mods, [os.path.join(steam_path, 'assets', 'mods'), os.path.join(steam_path, 'BepInEx', 'plugins')]),
                        (self.remove_temp_files, [os.path.join(steam_path, 'assets')])
                    ]
                else:
                    self.update_steps = [
                        (self.delete_plugins_directory, [os.path.join(steam_path, 'BepInEx', 'plugins')]),
                        (self.move_mods, [os.path.join(steam_path, 'assets', 'mods'), os.path.join(steam_path, 'BepInEx', 'plugins')]),
                        (self.remove_temp_files, [os.path.join(steam_path, 'assets')])
                    ]

                self.master.after(100, self.check_update_progress, steam_path)
            else: 
                self.show_error("Steam not found. Update aborted.")
        except Exception as e:
            self.show_error(f"An error occurred: {e}")

    def check_update_progress(self, steam_path):
        if self.update_steps:
            update_step, args = self.update_steps.pop(0)
            update_step(*args)
            self.master.after(100, self.check_update_progress, steam_path)
        else:
            self.show_message("Update completed successfully.")

    def move_bepinex_files(self, src_folder, dest_folder):
        if os.path.exists(os.path.join(dest_folder, 'BepInEx')):
            self.show_message("Existing BepInEx files found. Skipping extraction.")
        else:
            self.move_folder_contents(src_folder, dest_folder)

    def launch_lethal_company(self, executable_path):
        self.show_message("Launching Lethal Company to generate core files.")
        self.launch_and_wait(executable_path)
        self.terminate_process("Lethal Company.exe")

    def launch_and_wait(self, executable_path, wait_time_seconds=20):
        try:
            process = subprocess.Popen([executable_path], shell=True)
            time.sleep(wait_time_seconds)
            process.terminate()
        except Exception as e:
            self.show_error(f"Error launching {executable_path}: {e}")

    def terminate_process(self, process_name):
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == process_name:
                psutil.Process(process.info['pid']).terminate()

    def modify_bepinex_config(self, file_path):
        self.replace_line_in_file(file_path, 'HideManagerGameObject = false', 'HideManagerGameObject = true')

    def delete_plugins_directory(self, folder_path):
        self.delete_folder_contents(folder_path)

    def move_mods(self, src_folder, dest_folder):
        self.move_folder_contents(src_folder, dest_folder)

    def remove_temp_files(self, folder_path):
        shutil.rmtree(folder_path)
    
    def show_message(self, message):
        messagebox.showinfo("Info", message)

# Create the main window
if __name__ == "__main__":
    root = tk.Tk()
    app = UpdateApp(root)
    root.mainloop()
