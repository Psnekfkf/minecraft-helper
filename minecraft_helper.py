# minecraft_helper.py
# Простой GUI для копирования модов (.jar) и шейдеров (.zip / папки) в папку Minecraft на Windows.
# Не выполняет сторонних инсталляторов — просто копирует/упаковывает в %appdata%\.minecraft

import os
import shutil
import time
from pathlib import Path
import PySimpleGUI as sg

APP_NAME = "Minecraft Mod/Shader Helper"
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")

def get_minecraft_path():
    appdata = os.getenv("APPDATA")
    if not appdata:
        return None
    mc = Path(appdata) / ".minecraft"
    return mc if mc.exists() else None

def ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def backup_folder(folder: Path, backup_root: Path):
    if not folder.exists():
        return None
    ensure_dir(backup_root)
    archive_name = backup_root / f"{folder.name}_backup_{TIMESTAMP}"
    archive_path = shutil.make_archive(str(archive_name), 'zip', root_dir=str(folder))
    return archive_path

def copy_mod(file_path: Path, mods_folder: Path):
    ensure_dir(mods_folder)
    dest = mods_folder / file_path.name
    shutil.copy2(str(file_path), str(dest))
    return dest

def add_shader_file(file_path: Path, shaderpacks_folder: Path):
    ensure_dir(shaderpacks_folder)
    dest = shaderpacks_folder / file_path.name
    shutil.copy2(str(file_path), str(dest))
    return dest

def add_shader_folder(folder_path: Path, shaderpacks_folder: Path):
    ensure_dir(shaderpacks_folder)
    base_name = f"{folder_path.name}_{TIMESTAMP}"
    temp_zip_base = Path(os.path.abspath(os.path.join(os.getcwd(), base_name)))
    # make_archive will append .zip
    archive_created = shutil.make_archive(str(temp_zip_base), 'zip', root_dir=str(folder_path))
    temp_zip = Path(archive_created)
    dest = shaderpacks_folder / temp_zip.name
    shutil.move(str(temp_zip), str(dest))
    return dest

def log(message: str, log_file: Path, window=None):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    if window:
        try:
            # append to multiline element
            window["-LOG-"].update(line, append=True)
        except Exception:
            pass

def main():
    sg.theme("LightBlue")
    mc_path = get_minecraft_path()
    layout_top = [
        [sg.Text("Папка Minecraft:"), sg.Input(mc_path.as_posix() if mc_path else "", key="-MC_PATH-", size=(50,1)), sg.FolderBrowse(target="-MC_PATH-")],
        [sg.Button("Добавить мод (.jar)"), sg.Button("Добавить шейдер (файл / папка)"), sg.Button("Открыть логи"), sg.Button("Выход")]
    ]
    layout_log = [[sg.Multiline("", size=(80, 15), key="-LOG-", autoscroll=True, disabled=False)]]
    layout = layout_top + layout_log

    window = sg.Window(APP_NAME, layout, finalize=True)

    log_file = (mc_path / "mod_shader_helper.log") if mc_path else Path.cwd() / "mod_shader_helper.log"

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "Выход":
            break

        mc_input = values.get("-MC_PATH-")
        mc_dir = Path(mc_input) if mc_input else None
        if not mc_dir or not mc_dir.exists():
            sg.popup_error("Не найдена папка Minecraft. Укажите вручную в поле или выберите её.")
            continue

        mods_folder = mc_dir / "mods"
        shaderpacks_folder = mc_dir / "shaderpacks"
        backups_root = mc_dir / "mod_shader_backups"

        if event == "Добавить мод (.jar)":
            file = sg.popup_get_file("Выберите .jar файл мода (OptiFine тоже .jar):", file_types=(("JAR Files", "*.jar"),), no_window=True)
            if not file:
                continue
            file_path = Path(file)
            if file_path.suffix.lower() != ".jar":
                sg.popup_error("Выбран не .jar файл. Повторите.")
                continue
            try:
                log("Начинаю резервную копию папки mods...", log_file, window)
                backup = backup_folder(mods_folder, backups_root)
                if backup:
                    log(f"Резервная копия mods создана: {backup}", log_file, window)
                else:
                    log("Папка mods не найдена или пуста — резервная копия пропущена.", log_file, window)
                dest = copy_mod(file_path, mods_folder)
                log(f"Мод скопирован: {dest}", log_file, window)
                sg.popup("Всё выполнено", title="Готово")
            except Exception as e:
                sg.popup_error("Ошибка при добавлении мода:", str(e))
                log(f"Ошибка при добавлении мода: {e}", log_file, window)

        if event == "Добавить шейдер (файл / папка)":
            choice = sg.popup_yes_no("Вы хотите выбрать файл или папку?\nYes — файл (.zip), No — папка", title="Файл или папка")
            if choice == "Yes":
                file = sg.popup_get_file("Выберите файл шейдера (.zip):", file_types=(("ZIP Files", "*.zip"), ("All files", "*.*")), no_window=True)
                if not file:
                    continue
                file_path = Path(file)
                try:
                    log("Резервная копия shaderpacks...", log_file, window)
                    backup = backup_folder(shaderpacks_folder, backups_root)
                    if backup:
                        log(f"Резервная копия shaderpacks создана: {backup}", log_file, window)
                    else:
                        log("Папка shaderpacks не найдена или пуста — резервная копия пропущена.", log_file, window)
                    dest = add_shader_file(file_path, shaderpacks_folder)
                    log(f"Шейдер добавлен: {dest}", log_file, window)
                    sg.popup("Всё выполнено", title="Готово")
                except Exception as e:
                    sg.popup_error("Ошибка при добавлении шейдера:", str(e))
                    log(f"Ошибка при добавлении шейдера (файл): {e}", log_file, window)
            elif choice == "No":
                folder = sg.popup_get_folder("Выберите папку со шейдером:", no_window=True)
                if not folder:
                    continue
                folder_path = Path(folder)
                if not folder_path.is_dir():
                    sg.popup_error("Выбранный путь не является папкой.")
                    continue
                try:
                    log("Резервная копия shaderpacks...", log_file, window)
                    backup = backup_folder(shaderpacks_folder, backups_root)
                    if backup:
                        log(f"Резервная копия shaderpacks создана: {backup}", log_file, window)
                    else:
                        log("Папка shaderpacks не найдена или пуста — резервная копия пропущена.", log_file, window)
                    dest = add_shader_folder(folder_path, shaderpacks_folder)
                    log(f"Шейдер-папка упакована и добавлена: {dest}", log_file, window)
                    sg.popup("Всё выполнено", title="Готово")
                except Exception as e:
                    sg.popup_error("Ошибка при добавлении шейдера (папка):", str(e))
                    log(f"Ошибка при добавлении шейдера (папка): {e}", log_file, window)
            else:
                continue

        if event == "Открыть логи":
            try:
                if not log_file.exists():
                    sg.popup("Лог пустой.")
                else:
                    with open(log_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    sg.popup_scrolled(content, title="Лог операций", size=(80,30))
            except Exception as e:
                sg.popup_error("Не удалось открыть лог:", str(e))

    window.close()

if __name__ == "__main__":
    main()
