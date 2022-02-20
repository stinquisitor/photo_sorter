import asyncio
import os

from tkinter import Button
from tkinter import END
from tkinter import Frame
from tkinter import INSERT
from tkinter import Label
from tkinter import OptionMenu
from tkinter import Misc
from tkinter import StringVar
from tkinter import Text
from tkinter import Tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import BooleanVar
from pathlib import Path
import constants
from tkinter.scrolledtext import ScrolledText

from sorters import *


class Logger:
    def __init__(self, root: Misc):
        self.text = ScrolledText(master=root, width=80, height=20)
        self.text.pack()
        self._root = root

    def info(self, message: str):
        self._print(message, 'INFO')

    def warning(self, message: str):
        self._print(message, 'WARN')

    def error(self, message: str):
        self._print(message, 'ERR')

    def _print(self, text, prefix: str):
        self.text.insert(INSERT, f'[{prefix}]: {text}\n')
        self._root.update_idletasks()

    def clear(self):
        self.text.delete('1.0', END)


class Summary:
    def __init__(self, logger: Logger):
        self._summary = {}  # dir_name: photo_num
        self._unique_photos = set()
        self._miss_files = set()
        self._logger = logger

    def add(self, dir_name: (str, Path), photo_count: int, photo_name=""):
        if dir_name not in self._summary.keys():
            self._summary[dir_name] = photo_count
        else:
            self._summary[dir_name] += photo_count
        self._unique_photos.add(photo_name)

    # кажись костыль не нужен больше.
    def add_miss_file(self, num, dir, metadata):
        # TODO: это костыль
        if len(str(num)) == 4:
            self._miss_files.add((num, dir, metadata))

    def get(self, dir_name: (str, Path)):
        if isinstance(dir_name, str):
            return self._get_by_name(dir_name)
        if dir_name in self._summary.keys():
            return dir_name, self._summary[dir_name]
        else:
            return None

    @property
    def unique_files(self):
        return self._unique_photos

    @property
    def miss_files(self):
        return self._miss_files

    def _get_by_name(self, name: str):
        for dir_name in self._summary.keys():
            if dir_name.name == name:
                return dir_name, self._summary[dir_name]
        return None

    def show(self):
        for dir in sorted(self._summary.keys()):
            self._logger.info(f'В "{dir.name}" - {self._summary[dir]} фото')


class FileDialog:
    def __init__(self, root: (Tk, Frame, Misc), label: str, ask_dir=False):
        self.ask_dir = ask_dir
        self.label = Label(root, text=label)
        self.label.pack()
        self.text = Text(master=root, width=50, height=1)
        self.text.pack()
        self.open_button = Button(master=root, text='Открыть', command=self._open)
        self.open_button.pack()

    def _open(self):
        self.text.delete(1.0, END)
        if self.ask_dir:
            file_name = fd.askdirectory()
        else:
            file_name = fd.askopenfilename()
        self.text.insert(1.0, file_name)

    def get_file_name(self):
        return self.text.get("1.0", "end-1c")


class ExtChecker:
    def __init__(self, root: (Tk, Frame, Misc)):
        extensions = ['ВСЕ', 'ФОТО'] + constants.extensions.copy()
        self._variable = StringVar(root)
        self._variable.set(extensions[0])
        menu = OptionMenu(root, self._variable, *extensions)

        label = Label(root, text='Расширение сортируемых файлов')
        label.pack()
        menu.pack()

    def get(self):
        return self._variable.get()


class Window:
    def __init__(self):
        self.root = Tk()
        self.root.title('Сортировка фото ' + constants.version)
        self.root.resizable(False, False)
        self.tab_control = ttk.Notebook(self.root)
        printing_tab = ttk.Frame(self.tab_control)
        album_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(printing_tab, text='Печать')
        self.tab_control.add(album_tab, text='Альбом')

        self.printing_table_path_fd = FileDialog(printing_tab, 'Путь до excel-таблицы')
        self.printing_unsorted_path_fd = FileDialog(printing_tab, 'Путь до папки с фото', ask_dir=True)
        self.printing_ext_checker = ExtChecker(printing_tab)

        self.is_retush = BooleanVar(value=False)
        self.retush_check = ttk.Checkbutton(master=printing_tab, variable=self.is_retush, text='В одну папку')
        self.retush_check.pack()

        self.printing_logger = Logger(printing_tab)
        self.printing_sort_button = Button(master=printing_tab, text='Сортировать', command=self._sort_printing)
        self.printing_sort_button.pack()

        self.album_table_path_fd = FileDialog(album_tab, 'Путь до excel-таблицы')
        self.album_unsorted_path_fd = FileDialog(album_tab, 'Путь до папки с фото', ask_dir=True)
        self.album_ext_checker = ExtChecker(album_tab)

        # потом всё в одно интегрируем
        self.is_retush_album = BooleanVar(value=False)
        self.retush_check_album = ttk.Checkbutton(master=album_tab, variable=self.is_retush_album, text='В одну папку')
        self.retush_check_album.pack()

        self.album_logger = Logger(album_tab)
        self.album_sort_button = Button(master=album_tab, text='Сортировать', command=self._sort_album)
        self.album_sort_button.pack()

        self.tab_control.pack(expand=1, fill='both')

        self._loop = asyncio.get_event_loop()

    def __del__(self):
        self._loop.close()

    def _sort_printing(self):
        try:
            unsorted = self.printing_unsorted_path_fd.get_file_name()
            outdir = os.path.join(unsorted, 'Сортировка')
            table = self.printing_table_path_fd.get_file_name()
            self.printing_logger.info(f'Таблица: {table}')
            self.printing_logger.info(f'Несортированные фото: {unsorted}')
            self.printing_logger.info(f'Сортированные фото: {outdir}')
            summary = Summary(self.printing_logger)
            sorter = PrintingSorter(table, unsorted, outdir,
                                    self.printing_logger,
                                    self._loop, summary,
                                    self.printing_ext_checker.get(), self.is_retush.get())
            sorter.sort()
        except Exception as exc:
            self.printing_logger.error(str(exc))
            raise

    def _sort_album(self):
        try:
            unsorted = self.album_unsorted_path_fd.get_file_name()
            outdir = os.path.join(unsorted, 'Сортировка')
            table = self.album_table_path_fd.get_file_name()
            self.album_logger.info(f'Таблица: {table}')
            self.album_logger.info(f'Несортированные фото: {unsorted}')
            self.album_logger.info(f'Сортированные фото: {outdir}')
            summary = Summary(self.printing_logger)
            sorter = AlbumSorter(table, unsorted, outdir,
                                 self.album_logger,
                                 self._loop,
                                 summary,
                                 self.album_ext_checker.get(), self.is_retush_album.get())
            sorter.sort()
        except Exception as exc:
            self.printing_logger.error(str(exc))
            raise

    def run(self):
        self.root.mainloop()
