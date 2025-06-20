import os
import json
import requests
import subprocess
import zipfile
import sys
import platform
import locale
import shutil
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QComboBox, QProgressBar, QLineEdit, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- Глобальные пути ---
BASE_DIR = os.path.abspath(".")
MC_DIR = os.path.join(BASE_DIR, ".minecraft")
VERSIONS_DIR = os.path.join(MC_DIR, "versions")
LIBRARIES_DIR = os.path.join(MC_DIR, "libraries")
NATIVES_DIR = os.path.join(MC_DIR, "natives")
ASSETS_DIR = os.path.join(MC_DIR, "assets")

# Создаем необходимые директории, если они не существуют
os.makedirs(VERSIONS_DIR, exist_ok=True)
os.makedirs(LIBRARIES_DIR, exist_ok=True)
os.makedirs(NATIVES_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)


# --- Данные локализации ---
translation_data = {
    "en": {
        "window_title": "Minecraft Launcher",
        "nickname_label": "Nickname:",
        "version_label": "Version:",
        "search_label": "Search Version:",
        "status_select_version": "Select Minecraft version",
        "button_download_and_launch": "Download and Launch",
        "status_loading_versions": "Loading versions list...",
        "status_versions_loaded": "Versions list loaded. Select a version.",
        "error_network_title": "Network Error",
        "error_network_msg": "Failed to load Minecraft versions list.\nPlease check your internet connection.\nError: {e}",
        "error_data_title": "Data Error",
        "error_data_msg": "Failed to parse version manifest.\nError: {e}",
        "warning_enter_nickname_title": "Attention",
        "warning_enter_nickname_msg": "Please enter a nickname.",
        "warning_select_version_title": "Attention",
        "warning_select_version_msg": "Please select a Minecraft version.",
        "status_loading_version_data": "Loading version data: {version}...",
        "status_downloading_client_jar": "Downloading client JAR: {filename}",
        "status_downloading_libraries": "Downloading libraries...",
        "status_extracting_natives": "Extracting native libraries...",
        "status_downloading_assets": "Downloading assets...",
        "status_launching_game": "Launching game...",
        "status_done_launched": "Done! Game launched (or error occurred, check console).",
        "error_download_title": "Download Error",
        "error_download_msg": "An error occurred during file download:\n{e}",
        "error_json_parse_title": "JSON Parse Error",
        "error_json_parse_msg": "An error occurred while processing version data:\n{e}",
        "error_unknown_title": "Unknown Error",
        "error_unknown_msg": "An unexpected error occurred:\n{e}",
        "warn_skip_asset_index_url": "Warning: Asset index URL not found. Perhaps a very old version or an error.",
        "status_downloading_asset_index": "Downloading asset index file: {filename}",
        "warn_asset_error": "Error downloading asset: {name}. Continuing...",
        "error_java_not_found_title": "Java Not Found",
        "error_java_not_found_msg": "Java not found. Please ensure Java Development Kit (JDK) is installed and added to your system's PATH.",
        "error_launch_title": "Launch Error",
        "error_launch_msg": "Failed to launch Minecraft:\n{e}",
        "warn_client_jar_missing": "Warning: Client JAR not found for classpath: {path}. Game might not launch.",
        "warn_invalid_zip": "Warning: {filename} is not a valid ZIP file. Skipping.",
        "error_extract_natives": "Error extracting natives: {filename}",
        "error_download_lib": "Error downloading library: {filename}. Continuing...",
        "error_download_native_lib": "Error downloading native library: {filename}. Continuing...",
        "language_label": "Language:",
        "current_language_status": "Current Language: {lang}",
        "status_nickname_empty": "Enter nickname!",
        "status_using_installed_version": "Using installed version: {version}",
        "status_scanning_local_versions": "Scanning for local versions...",
        "status_local_versions_found": "Found {count} installed versions.",
        "local_version_suffix": " (Installed)",
        "status_jar_skip": " (skip)",
        "status_file_missing": " (file missing)",
        "status_working_in_background": "Working in background...",
        "error_thread_failed_title": "Operation Failed",
        "error_thread_failed_msg": "The background operation failed: {error_message}"
    },
    "ru": {
        "window_title": "Лаунчер Minecraft",
        "nickname_label": "Ник:",
        "version_label": "Версия:",
        "search_label": "Поиск версий:",
        "status_select_version": "Выберите версию Minecraft",
        "button_download_and_launch": "Скачать и запустить",
        "status_loading_versions": "Загрузка списка версий...",
        "status_versions_loaded": "Список версий загружен. Выберите версию.",
        "error_network_title": "Ошибка сети",
        "error_network_msg": "Не удалось загрузить список версий Minecraft.\nПроверьте ваше интернет-соединение.\nОшибка: {e}",
        "error_data_title": "Ошибка данных",
        "error_data_msg": "Не удалось распарсить манифест версии.\nОшибка: {e}",
        "warning_enter_nickname_title": "Внимание",
        "warning_enter_nickname_msg": "Пожалуйста, введите никнейм.",
        "warning_select_version_title": "Внимание",
        "warning_select_version_msg": "Пожалуйста, выберите версию Minecraft.",
        "status_loading_version_data": "Загрузка данных версии: {version}...",
        "status_downloading_client_jar": "Загрузка JAR клиента: {filename}",
        "status_downloading_libraries": "Загрузка библиотек...",
        "status_extracting_natives": "Распаковка нативных библиотек...",
        "status_downloading_assets": "Загрузка ресурсов...",
        "status_launching_game": "Запуск игры...",
        "status_done_launched": "Готово! Игра запущена (или произошла ошибка, проверьте консоль).",
        "error_download_title": "Ошибка загрузки",
        "error_download_msg": "Произошла ошибка при загрузке файлов:\n{e}",
        "error_json_parse_title": "Ошибка парсинга JSON",
        "error_json_parse_msg": "Произошла ошибка при обработке данных версии:\n{e}",
        "error_unknown_title": "Неизвестная ошибка",
        "error_unknown_msg": "Произошла непредвиденная ошибка:\n{e}",
        "warn_skip_asset_index_url": "Предупреждение: Не найден URL индекса ресурсов. Возможно, очень старая версия или ошибка.",
        "status_downloading_asset_index": "Загрузка файла индекса ресурсов: {filename}",
        "warn_asset_error": "Ошибка загрузки ресурса: {name}. Продолжаем...",
        "error_java_not_found_title": "Java не найдена",
        "error_java_not_found_msg": "Java не найдена. Убедитесь, что Java Development Kit (JDK) установлена и добавлена в PATH.",
        "error_launch_title": "Ошибка запуска",
        "error_launch_msg": "Не удалось запустить Minecraft:\n{e}",
        "warn_client_jar_missing": "Предупреждение: JAR клиента не найден для classpath: {path}. Игра может не запуститься.",
        "warn_invalid_zip": "Предупреждение: {filename} не является действительным ZIP-файлом. Пропускаем его.",
        "error_extract_natives": "Ошибка при распаковке нативов: {filename}",
        "error_download_lib": "Ошибка загрузки библиотеки: {filename}. Продолжаем...",
        "error_download_native_lib": "Ошибка загрузки нативной библиотеки: {filename}. Продолжаем...",
        "language_label": "Язык:",
        "current_language_status": "Текущий язык: {lang}",
        "status_nickname_empty": "Введите ник!",
        "status_using_installed_version": "Используется установленная версия: {version}",
        "status_scanning_local_versions": "Поиск локальных версий...",
        "status_local_versions_found": "Найдено {count} установленных версий.",
        "local_version_suffix": " (Установлено)",
        "status_jar_skip": " (пропуск)",
        "status_file_missing": " (файл отсутствует)",
        "status_working_in_background": "Работа в фоновом режиме...",
        "error_thread_failed_title": "Операция не удалась",
        "error_thread_failed_msg": "Фоновая операция не удалась: {error_message}"
    }
}

# Determine default language based on system locale
def get_system_language():
    try:
        lang_code, _ = locale.getdefaultlocale()
        if lang_code:
            return lang_code[:2]
    except Exception:
        pass
    return "en" # Fallback to English

current_language = get_system_language()
if current_language not in translation_data:
    current_language = "en" # Ensure it's a supported language


def _(key, **kwargs):
    """
    Translation lookup function.
    Retrieves the translated string for a given key in the current language.
    Allows for string formatting with keyword arguments.
    """
    text = translation_data.get(current_language, {}).get(key, key) # Fallback to key if translation not found
    return text.format(**kwargs)


# --- Helper functions for OS detection and Minecraft rules ---
def get_current_os_name():
    """
    Maps sys.platform to Minecraft's OS names found in version manifests.
    e.g., 'win32' -> 'windows', 'linux'/'linux2' -> 'linux', 'darwin' -> 'osx'.
    """
    os_name = sys.platform
    if os_name.startswith('linux'):
        return 'linux'
    elif os_name == 'win32':
        return 'windows'
    elif os_name == 'darwin':
        return 'osx'
    return os_name


def get_current_os_arch():
    """
    Maps platform.machine() to Minecraft's architecture names.
    e.g., 'x86_64' -> 'x64', 'arm64' -> 'arm64'.
    """
    arch = platform.machine().lower()
    if arch == 'x86_64':
        return 'x64'
    elif arch == 'amd64':
        return 'x64'
    elif arch == 'i386':
        return 'i386'
    elif arch == 'arm64':
        return 'arm64'
    return arch


def check_library_rules(rules):
    """
    Checks if a library is applicable based on Minecraft's rule set.
    Minecraft's rule logic:
    1. If no rules are defined, the library is always applicable.
    2. If 'allow' rules exist:
       At least one 'allow' rule must match the current OS/architecture for the library to be potentially included.
       If 'allow' rules exist but none match, the library is excluded.
    3. If 'disallow' rules exist:
       If any 'disallow' rule matches the current OS/architecture, the library is excluded, regardless of 'allow' rules.
    """
    if not rules:
        return True

    current_os_name = get_current_os_name()
    current_os_arch = get_current_os_arch()

    found_matching_allow_rule = False
    has_allow_rules = False
    for rule in rules:
        if rule.get("action") == "allow":
            has_allow_rules = True
            rule_os = rule.get("os")
            os_matches = True
            if rule_os:
                if "name" in rule_os and rule_os["name"] != current_os_name:
                    os_matches = False
                if "arch" in rule_os and rule_os["arch"] != current_os_arch:
                    os_matches = False
            if os_matches:
                found_matching_allow_rule = True
                break

    if has_allow_rules and not found_matching_allow_rule:
        return False

    for rule in rules:
        if rule.get("action") == "disallow":
            rule_os = rule.get("os")
            os_matches = True
            if rule_os:
                if "name" in rule_os and rule_os["name"] != current_os_name:
                    os_matches = False
                if "arch" in rule_os and rule_os["arch"] != current_os_arch:
                    os_matches = False
            if os_matches:
                return False

    return True


# --- Worker Thread for Background Operations ---
class WorkerThread(QThread):
    # Signals to communicate with the main UI thread
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    operation_finished = pyqtSignal(bool) # True for success, False for failure
    error_occurred = pyqtSignal(str)

    def __init__(self, version_id, nickname, remote_versions, local_versions):
        super().__init__()
        self.version_id = version_id
        self.nickname = nickname
        self.remote_versions = remote_versions
        self.local_versions = local_versions

    def run(self):
        """
        This method is executed when the thread starts.
        It contains all the long-running operations.
        """
        try:
            version_data = None

            # Try to load from local first, if not found, then download
            if self.version_id in self.local_versions:
                version_data = self.local_versions[self.version_id]
                self.status_updated.emit(_("status_using_installed_version", version=self.version_id))
            else:
                version_url = self.remote_versions.get(self.version_id)
                if not version_url:
                    raise Exception(f"Manifest URL for version {self.version_id} not found.")
                
                self.status_updated.emit(_("status_loading_version_data", version=self.version_id))
                response = requests.get(version_url, timeout=10)
                response.raise_for_status()
                version_data = response.json()

                # Save the full version JSON manifest if it was downloaded
                json_path = os.path.join(VERSIONS_DIR, self.version_id, f"{self.version_id}.json")
                os.makedirs(os.path.dirname(json_path), exist_ok=True)
                with open(json_path, "w", encoding='utf-8') as f:
                    json.dump(version_data, f, indent=4)

            # --- Step 1: Download client JAR (approx 10% of overall progress) ---
            client_jar_path = os.path.join(VERSIONS_DIR, self.version_id, f"{self.version_id}.jar")
            if not os.path.exists(client_jar_path):
                self.progress_updated.emit(10)
                self._download_client_jar(version_data)
            else:
                self.status_updated.emit(_("status_downloading_client_jar", filename=f"{self.version_id}.jar") + _("status_jar_skip"))
            self.progress_updated.emit(20)

            # --- Step 2: Download libraries (approx 30% of overall progress) ---
            self.status_updated.emit(_("status_downloading_libraries"))
            self._download_libraries(version_data)
            self.progress_updated.emit(50)

            # --- Step 3: Extract natives (approx 10% of overall progress) ---
            self.status_updated.emit(_("status_extracting_natives"))
            self._extract_natives(version_data)
            self.progress_updated.emit(60)

            # --- Step 4: Download assets (approx 20% of overall progress) ---
            self.status_updated.emit(_("status_downloading_assets"))
            self._download_assets(version_data)
            self.progress_updated.emit(80)

            # --- Step 5: Launch game (approx 20% of overall progress) ---
            self.status_updated.emit(_("status_launching_game"))
            self._launch_game(version_data, self.nickname)
            self.progress_updated.emit(100)
            self.status_updated.emit(_("status_done_launched"))
            self.operation_finished.emit(True)

        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(_("error_download_msg", e=e))
            self.operation_finished.emit(False)
        except json.JSONDecodeError as e:
            self.error_occurred.emit(_("error_json_parse_msg", e=e))
            self.operation_finished.emit(False)
        except Exception as e:
            self.error_occurred.emit(_("error_unknown_msg", e=e))
            self.operation_finished.emit(False)

    def _download_client_jar(self, version_data):
        """Downloads the main Minecraft client JAR file for the selected version."""
        version = version_data["id"]
        version_path = os.path.join(VERSIONS_DIR, version)
        os.makedirs(version_path, exist_ok=True)

        client_jar_url = version_data["downloads"]["client"]["url"]
        jar_filename = f"{version}.jar"
        jar_path = os.path.join(version_path, jar_filename)
        
        self.status_updated.emit(_("status_downloading_client_jar", filename=jar_filename))
        try:
            r = requests.get(client_jar_url, stream=True, timeout=60)
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(jar_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        current_progress = 10 + int(10 * (downloaded / total_length)) # From 10% to 20%
                        self.progress_updated.emit(min(current_progress, 20))
        except requests.exceptions.RequestException as e:
            print(f"Error downloading client JAR {client_jar_url}: {e}")
            self.status_updated.emit(_("error_download_lib", filename=jar_filename))
            raise # Re-raise to be caught by run() method


    def _download_libraries(self, version_data):
        """
        Downloads all required libraries, including regular JARs and native ZIPs,
        based on the version manifest and OS rules.
        """
        libraries = version_data.get("libraries", [])
        total_libs = 0
        for lib in libraries:
            if check_library_rules(lib.get("rules")) and "downloads" in lib:
                if "artifact" in lib["downloads"] or ("classifiers" in lib["downloads"] and lib.get("natives")):
                    total_libs += 1

        downloaded_libs_count = 0
        
        for lib in libraries:
            if not check_library_rules(lib.get("rules")):
                continue

            # Handle regular artifact libraries (JARs)
            if "downloads" in lib and "artifact" in lib["downloads"]:
                artifact = lib["downloads"]["artifact"]
                url = artifact["url"]
                path = os.path.join(LIBRARIES_DIR, artifact["path"])
                filename = os.path.basename(path)
                
                if not os.path.exists(path):
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    self.status_updated.emit(_("status_downloading_libraries") + f": {filename}")
                    try:
                        r = requests.get(url, stream=True, timeout=30)
                        r.raise_for_status()
                        with open(path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading library {url}: {e}")
                        self.status_updated.emit(_("error_download_lib", filename=filename))
                        # Not raising here to attempt to download other libraries
                else:
                    self.status_updated.emit(_("status_downloading_libraries") + f": {filename}" + _("status_jar_skip"))

            # Handle native libraries (these are typically ZIP files that need extraction later)
            elif "natives" in lib:
                native_key_template = lib["natives"].get(get_current_os_name())
                if not native_key_template:
                    continue

                native_key = native_key_template.replace("${arch}", get_current_os_arch())

                if "downloads" in lib and "classifiers" in lib["downloads"]:
                    if native_key in lib["downloads"]["classifiers"]:
                        native_info = lib["downloads"]["classifiers"][native_key]
                        url = native_info["url"]
                        path = os.path.join(LIBRARIES_DIR, native_info["path"])
                        filename = os.path.basename(path)

                        if not os.path.exists(path):
                            os.makedirs(os.path.dirname(path), exist_ok=True)
                            self.status_updated.emit(_("status_downloading_libraries") + f": {filename}")
                            try:
                                r = requests.get(url, stream=True, timeout=30)
                                r.raise_for_status()
                                with open(path, "wb") as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                            except requests.exceptions.RequestException as e:
                                print(f"Error downloading native library {url}: {e}")
                                self.status_updated.emit(_("error_download_native_lib", filename=filename))
                                # Not raising here to attempt to download other natives
                        else:
                            self.status_updated.emit(_("status_downloading_libraries") + f": {filename}" + _("status_jar_skip"))
            
            downloaded_libs_count += 1
            if total_libs > 0:
                current_progress = 20 + int(30 * (downloaded_libs_count / total_libs)) # From 20% to 50%
                self.progress_updated.emit(min(current_progress, 50))


    def _extract_natives(self, version_data):
        """
        Extracts native library ZIP files into the designated NATIVES_DIR.
        """
        self.status_updated.emit(_("status_extracting_natives"))
        
        # Clear the natives directory before extraction to avoid conflicts
        if os.path.exists(NATIVES_DIR):
            for item in os.listdir(NATIVES_DIR):
                item_path = os.path.join(NATIVES_DIR, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

        extracted_files_count = 0
        total_natives_to_process = 0
        
        for lib in version_data.get("libraries", []):
            if not check_library_rules(lib.get("rules")):
                continue
            if "natives" in lib:
                native_key_template = lib["natives"].get(get_current_os_name())
                if native_key_template:
                    native_key = native_key_template.replace("${arch}", get_current_os_arch())
                    if "downloads" in lib and "classifiers" in lib["downloads"] and native_key in lib["downloads"]["classifiers"]:
                        total_natives_to_process += 1

        for lib in version_data.get("libraries", []):
            if not check_library_rules(lib.get("rules")):
                continue

            if "natives" in lib:
                native_key_template = lib["natives"].get(get_current_os_name())
                if not native_key_template:
                    continue
                    
                native_key = native_key_template.replace("${arch}", get_current_os_arch())

                if "downloads" in lib and "classifiers" in lib["downloads"]:
                    if native_key in lib["downloads"]["classifiers"]:
                        native_info = lib["downloads"]["classifiers"][native_key]
                        native_path = os.path.join(LIBRARIES_DIR, native_info["path"])
                        native_filename = os.path.basename(native_path)
                        
                        if os.path.exists(native_path):
                            try:
                                with zipfile.ZipFile(native_path, 'r') as zip_ref:
                                    for member in zip_ref.namelist():
                                        if not member.startswith('META-INF/') and not member.endswith('/'):
                                            zip_ref.extract(member, NATIVES_DIR)
                                self.status_updated.emit(_("status_extracting_natives") + f": {native_filename}")
                            except zipfile.BadZipFile:
                                print(_("warn_invalid_zip", filename=native_filename))
                                self.status_updated.emit(_("warn_invalid_zip", filename=native_filename))
                            except Exception as e:
                                print(f"Error extracting natives {native_path}: {e}")
                                self.status_updated.emit(_("error_extract_natives", filename=native_filename))
                        else:
                            self.status_updated.emit(_("status_extracting_natives") + f": {native_filename}" + _("status_file_missing"))
                        
                        extracted_files_count += 1
                        if total_natives_to_process > 0:
                            current_progress = 50 + int(10 * (extracted_files_count / total_natives_to_process)) # From 50% to 60%
                            self.progress_updated.emit(min(current_progress, 60))


    def _download_assets(self, version_data):
        """
        Downloads the asset index JSON and then all individual assets (textures, sounds, etc.)
        that are referenced in the index.
        """
        self.status_updated.emit(_("status_downloading_assets"))
        
        asset_index_id = version_data.get("assetIndex", {}).get("id")
        if not asset_index_id:
            asset_index_id = version_data["id"]

        asset_index_info = version_data.get("assetIndex", {})
        asset_index_url = asset_index_info.get("url")
        
        if not asset_index_url:
            self.status_updated.emit(_("warn_skip_asset_index_url"))
            self.progress_updated.emit(60)
            return

        index_path = os.path.join(ASSETS_DIR, "indexes", f"{asset_index_id}.json")
        os.makedirs(os.path.dirname(index_path), exist_ok=True)

        try:
            if not os.path.exists(index_path):
                self.status_updated.emit(_("status_downloading_asset_index", filename=f"{asset_index_id}.json"))
                r = requests.get(asset_index_url, stream=True, timeout=30)
                r.raise_for_status()
                with open(index_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            with open(index_path, "r", encoding='utf-8') as f:
                asset_index = json.load(f)

            objects = asset_index.get("objects", {})
            total_assets = len(objects)
            downloaded_assets_count = 0

            for name, obj_info in objects.items():
                hash_val = obj_info["hash"]
                object_dir = os.path.join(ASSETS_DIR, "objects", hash_val[:2])
                object_path = os.path.join(object_dir, hash_val)
                
                os.makedirs(object_dir, exist_ok=True)

                if not os.path.exists(object_path):
                    asset_url = f"https://resources.download.minecraft.net/{hash_val[:2]}/{hash_val}"
                    try:
                        r = requests.get(asset_url, stream=True, timeout=30)
                        r.raise_for_status()
                        with open(object_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading asset {asset_url}: {e}")
                        self.status_updated.emit(_("warn_asset_error", name=name))
                
                downloaded_assets_count += 1
                if total_assets > 0:
                    current_progress = 60 + int(20 * (downloaded_assets_count / total_assets)) # From 60% to 80%
                    self.progress_updated.emit(min(current_progress, 80))

        except requests.exceptions.RequestException as e:
            self.status_updated.emit(_("error_download_msg", e=e))
            raise # Re-raise to be caught by run() method
        except json.JSONDecodeError as e:
            self.status_updated.emit(_("error_json_parse_msg", e=e))
            raise # Re-raise to be caught by run() method


    def _launch_game(self, version_data, nickname):
        """
        Constructs and executes the Java command to launch the Minecraft game.
        Handles both older (minecraftArguments) and newer (arguments with jvm/game sections)
        argument formats.
        """
        version = version_data["id"]
        
        if version.startswith(("a", "b", "c", "inf")) or version in ["rd-132211", "0.0.19a", "0.0.14a_08", "c0.30_01"]:
            self._launch_old_version(version_data, nickname)
            return

        main_class = version_data["mainClass"]
        classpath = self._build_classpath(version_data)
        classpath_str = os.pathsep.join(classpath)

        cmd = [
            "java",
            "-Xmx2G",
            "-Xms1G",
            f"-Djava.library.path={NATIVES_DIR}",
            "-cp", classpath_str,
            main_class,
        ]

        if "minecraftArguments" in version_data:
            args_template = version_data["minecraftArguments"]
            replacements = {
                "${auth_player_name}": nickname,
                "${version_name}": version,
                "${game_directory}": MC_DIR,
                "${assets_root}": ASSETS_DIR,
                "${assets_index}": version_data.get("assetIndex", {}).get("id", version),
                "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
                "${auth_access_token}": "0",
                "${user_properties}": "{}",
                "${user_type}": "mojang",
            }
            parsed_args = args_template.split()
            final_args = []
            for arg_part in parsed_args:
                replaced_arg = arg_part
                for placeholder, value in replacements.items():
                    replaced_arg = replaced_arg.replace(placeholder, value)
                final_args.append(replaced_arg)
            cmd.extend(final_args)

        elif "arguments" in version_data:
            jvm_args_data = version_data["arguments"].get("jvm", [])
            game_args_data = version_data["arguments"].get("game", [])

            arg_replacements = {
                "player_name": nickname,
                "version_name": version,
                "game_directory": MC_DIR,
                "assets_root": ASSETS_DIR,
                "assets_index": version_data.get("assetIndex", {}).get("id", version),
                "auth_uuid": "00000000-0000-0000-0000-000000000000",
                "auth_access_token": "0",
                "user_properties": "{}",
                "user_type": "mojang",
                "version_type": version_data.get("type", "release"),
                "resolution_width": "854",
                "resolution_height": "480",
                "natives_directory": NATIVES_DIR,
                "classpath": classpath_str,
            }
            
            def process_arg_entries(args_list_data):
                processed_args = []
                for arg_entry in args_list_data:
                    if isinstance(arg_entry, str):
                        final_val = arg_entry
                        for k, v in arg_replacements.items():
                            final_val = final_val.replace(f"${{{k}}}", str(v))
                        processed_args.append(final_val)
                    elif isinstance(arg_entry, dict) and "value" in arg_entry:
                        if check_library_rules(arg_entry.get("rules")):
                            values = arg_entry["value"]
                            if not isinstance(values, list):
                                values = [values]
                            
                            for val_str in values:
                                final_val = val_str
                                for k, v in arg_replacements.items():
                                    final_val = final_val.replace(f"${{{k}}}", str(v))
                                processed_args.append(final_val)
                return processed_args

            cmd.extend(process_arg_entries(jvm_args_data))
            cmd.extend(process_arg_entries(game_args_data))

        else:
            self.status_updated.emit("Предупреждение: Неизвестный формат аргументов версии. Используются базовые аргументы.")
            cmd.extend([
                "--username", nickname,
                "--version", version,
                "--gameDir", MC_DIR,
                "--assetsDir", ASSETS_DIR,
                "--assetIndex", version_data.get("assetIndex", {}).get("id", version),
                "--accessToken", "0",
                "--userProperties", "{}",
                "--uuid", "00000000-0000-0000-0000-000000000000",
                "--userType", "mojang"
            ])

        self.status_updated.emit(_("status_launching_game") + ":\n" + " ".join(cmd))
        print(" ".join(cmd))

        try:
            subprocess.Popen(cmd, cwd=MC_DIR)
        except FileNotFoundError:
            raise Exception(_("error_java_not_found_msg"))
        except Exception as e:
            raise Exception(_("error_launch_msg", e=e))


    def _launch_old_version(self, version_data, nickname):
        """
        Specialized launch logic for very old Minecraft versions (e.g., pre-1.6 Beta/Alpha).
        """
        version = version_data["id"]
        jar_path = os.path.join(VERSIONS_DIR, version, f"{version}.jar")
        
        if version.startswith("c0.0."):
            main_class = "com.mojang.minecraft.Minecraft"
        elif version.startswith(("a", "b", "inf")) or version in ["rd-132211"]:
            main_class = "net.minecraft.client.MinecraftApplet"
        else:
            main_class = "net.minecraft.client.Minecraft"
        
        classpath = [jar_path]
        
        common_old_libs_paths = [
            os.path.join(LIBRARIES_DIR, "org/lwjgl/lwjgl/lwjgl/2.9.0/lwjgl-2.9.0.jar"),
            os.path.join(LIBRARIES_DIR, "org/lwjgl/lwjgl/lwjgl_util/2.9.0/lwjgl_util-2.9.0.jar"),
            os.path.join(LIBRARIES_DIR, "net/java/jinput/jinput/2.0.5/jinput-2.0.5.jar"),
        ]
        
        for lib_path in common_old_libs_paths:
            if os.path.exists(lib_path):
                classpath.append(lib_path)

        classpath_str = os.pathsep.join(classpath)
        
        cmd = [
            "java",
            "-Xmx1G",
            "-Xms512M",
            f"-Djava.library.path={NATIVES_DIR}",
            "-cp", classpath_str,
            main_class,
            nickname
        ]
        
        if version.startswith(("a", "b", "c", "inf")) or version in ["rd-132211"]:
            cmd.append("12345")
            
        self.status_updated.emit(_("status_launching_game") + f" (old version):\n" + " ".join(cmd))
        print(" ".join(cmd))

        try:
            subprocess.Popen(cmd, cwd=MC_DIR)
        except FileNotFoundError:
            raise Exception(_("error_java_not_found_msg"))
        except Exception as e:
            raise Exception(_("error_launch_msg", e=e))


    def _build_classpath(self, version_data):
        """
        Constructs the Java classpath by collecting paths to all required library JARs
        and the main client JAR.
        """
        classpath = []
        for lib in version_data["libraries"]:
            if not check_library_rules(lib.get("rules")):
                continue
            
            if "downloads" in lib and "artifact" in lib["downloads"]:
                artifact = lib["downloads"]["artifact"]
                path = os.path.join(LIBRARIES_DIR, artifact["path"])
                if os.path.exists(path):
                    classpath.append(path)

        version = version_data["id"]
        client_jar_path = os.path.join(VERSIONS_DIR, version, f"{version}.jar")
        if os.path.exists(client_jar_path):
            classpath.append(client_jar_path)
        else:
            print(_("warn_client_jar_missing", path=client_jar_path))

        return classpath


# --- Main Launcher Class ---
class MinecraftLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 400) # Increased height to accommodate search bar

        self.layout = QVBoxLayout()
        
        # Language selection section
        self.language_layout = QHBoxLayout()
        self.language_label = QLabel(_("language_label"))
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        
        initial_lang_index = self.language_combo.findData(current_language)
        if initial_lang_index != -1:
            self.language_combo.setCurrentIndex(initial_lang_index)
        
        self.language_combo.currentIndexChanged.connect(self.change_language)
        self.language_layout.addWidget(self.language_label)
        self.language_layout.addWidget(self.language_combo)
        self.layout.addLayout(self.language_layout)

        # Nickname input section (horizontal layout for label and input)
        self.nickname_layout = QHBoxLayout()
        self.nickname_label = QLabel(_("nickname_label"))
        self.nickname_input = QLineEdit("Player")
        self.nickname_layout.addWidget(self.nickname_label)
        self.nickname_layout.addWidget(self.nickname_input)
        self.layout.addLayout(self.nickname_layout)

        # Search input section
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel(_("search_label"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_("search_label"))
        self.search_input.textChanged.connect(self.filter_versions)
        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input)
        self.layout.addLayout(self.search_layout)
        
        # Version selection dropdown
        self.version_combo = QComboBox()
        self.version_label = QLabel(_("version_label"))
        self.layout.addWidget(self.version_label)
        self.layout.addWidget(self.version_combo)

        # Status label and progress bar
        self.status_label = QLabel(_("status_select_version"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)

        # Launch button
        self.launch_button = QPushButton(_("button_download_and_launch"))
        self.launch_button.clicked.connect(self.start_download_and_launch_thread) # Connect to new thread starter method
        self.layout.addWidget(self.launch_button)

        self.setLayout(self.layout)

        self.remote_versions = {}
        self.local_versions = {}
        self.all_versions = {}
        self.worker_thread = None # To hold the reference to the worker thread

        self.update_ui_texts()
        self.load_all_versions()

    def update_ui_texts(self):
        global current_language
        self.setWindowTitle(_("window_title"))
        self.nickname_label.setText(_("nickname_label"))
        self.version_label.setText(_("version_label"))
        self.search_label.setText(_("search_label"))
        self.search_input.setPlaceholderText(_("search_label"))
        self.launch_button.setText(_("button_download_and_launch"))
        self.language_label.setText(_("language_label"))

        if self.status_label.text() == "Выберите версию Minecraft" or \
           self.status_label.text() == "Select Minecraft version":
             self.status_label.setText(_("status_select_version"))


    def change_language(self, index):
        global current_language
        selected_lang_code = self.language_combo.itemData(index)
        if selected_lang_code in translation_data:
            current_language = selected_lang_code
            self.update_ui_texts()
            self.update_status(_("current_language_status", lang=selected_lang_code.upper()))
            self.load_all_versions()
            self.filter_versions(self.search_input.text())
        else:
            print(f"Unsupported language selected: {selected_lang_code}")


    def update_status(self, message):
        self.status_label.setText(message)
        print(f"[STATUS] {message}")


    def update_progress(self, value):
        self.progress_bar.setValue(value)


    def show_message_box(self, title_key, message_key, icon=QMessageBox.Icon.Information, **kwargs):
        msg_box = QMessageBox()
        msg_box.setIcon(icon)
        msg_box.setText(_(message_key, **kwargs))
        msg_box.setWindowTitle(_(title_key))
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()


    def load_all_versions(self):
        self.update_status(_("status_loading_versions"))
        self.scan_local_versions()
        self.fetch_remote_versions()

        self.all_versions = {}
        combined_version_ids = sorted(list(set(self.local_versions.keys()) | set(self.remote_versions.keys())), reverse=True)

        for version_id in combined_version_ids:
            display_name = version_id
            if version_id in self.local_versions:
                display_name += _("local_version_suffix")
            self.all_versions[version_id] = display_name
        
        self.populate_version_combo(list(self.all_versions.keys()))
        self.update_status(_("status_versions_loaded"))


    def populate_version_combo(self, version_ids_to_display):
        self.version_combo.clear()
        for version_id in version_ids_to_display:
            display_name = self.all_versions.get(version_id, version_id)
            self.version_combo.addItem(display_name, version_id)


    def filter_versions(self, search_text):
        search_text = search_text.lower()
        filtered_ids = []
        for version_id, display_name in self.all_versions.items():
            if search_text in version_id.lower() or search_text in display_name.lower():
                filtered_ids.append(version_id)
        
        filtered_ids.sort(key=lambda x: self.all_versions[x], reverse=True)

        self.populate_version_combo(filtered_ids)


    def scan_local_versions(self):
        self.update_status(_("status_scanning_local_versions"))
        self.local_versions = {}
        found_count = 0
        for version_id in os.listdir(VERSIONS_DIR):
            version_path = os.path.join(VERSIONS_DIR, version_id)
            jar_path = os.path.join(version_path, f"{version_id}.jar")
            json_path = os.path.join(version_path, f"{version_id}.json")

            if os.path.isdir(version_path) and os.path.exists(jar_path) and os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        version_data = json.load(f)
                    self.local_versions[version_id] = version_data
                    found_count += 1
                except Exception as e:
                    print(f"Error reading local JSON for version {version_id}: {e}")
        self.update_status(_("status_local_versions_found", count=found_count))


    def fetch_remote_versions(self):
        manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        try:
            response = requests.get(manifest_url, timeout=10)
            response.raise_for_status()
            manifest = response.json()
            self.remote_versions = {v["id"]: v["url"] for v in manifest["versions"]}
        except requests.exceptions.RequestException as e:
            self.update_status(_("error_network_msg", e=e))
            self.show_message_box("error_network_title", "error_network_msg", QMessageBox.Icon.Critical, e=e)
        except json.JSONDecodeError as e:
            self.update_status(_("error_data_msg", e=e))
            self.show_message_box("error_data_title", "error_data_msg", QMessageBox.Icon.Critical, e=e)


    # --- New Threading Logic ---
    def start_download_and_launch_thread(self):
        version_id = self.version_combo.currentData()
        nickname = self.nickname_input.text().strip()

        if not nickname:
            self.update_status(_("status_nickname_empty"))
            self.show_message_box("warning_enter_nickname_title", "warning_enter_nickname_msg", QMessageBox.Icon.Warning)
            return
            
        if not version_id:
            self.update_status(_("status_select_version"))
            self.show_message_box("warning_select_version_title", "warning_select_version_msg", QMessageBox.Icon.Warning)
            return

        # Disable UI elements to prevent user interaction during the process
        self.launch_button.setEnabled(False)
        self.version_combo.setEnabled(False)
        self.nickname_input.setEnabled(False)
        self.search_input.setEnabled(False)
        self.language_combo.setEnabled(False)
        self.progress_bar.setValue(0)
        self.update_status(_("status_working_in_background"))

        # Create and start the worker thread
        self.worker_thread = WorkerThread(version_id, nickname, self.remote_versions, self.local_versions)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.status_updated.connect(self.update_status)
        self.worker_thread.operation_finished.connect(self.on_operation_finished)
        self.worker_thread.error_occurred.connect(self.on_error_occurred)
        self.worker_thread.start()


    def on_operation_finished(self, success):
        # Re-enable UI elements
        self.launch_button.setEnabled(True)
        self.version_combo.setEnabled(True)
        self.nickname_input.setEnabled(True)
        self.search_input.setEnabled(True)
        self.language_combo.setEnabled(True)
        self.progress_bar.setValue(100 if success else self.progress_bar.value()) # Keep current progress if failed
        self.update_status(_("status_done_launched") if success else self.status_label.text()) # Keep error status if failed

        # Clean up the thread
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait() # Wait for the thread to actually finish
            self.worker_thread = None


    def on_error_occurred(self, error_message):
        self.show_message_box("error_thread_failed_title", "error_thread_failed_msg", QMessageBox.Icon.Critical, error_message=error_message)
        self.on_operation_finished(False) # Call finished handler to re-enable UI


# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = MinecraftLauncher()
    launcher.show()
    sys.exit(app.exec())
