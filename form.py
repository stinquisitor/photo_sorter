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
from tkinter import LEFT
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

        self.top_frame = ttk.Frame(self.root)
        self.bottom_frame = ttk.Frame(self.root)
        self.top_frame.pack()
        self.bottom_frame.pack()

        self.left_frame = ttk.Frame(self.top_frame)
        self.right_frame = ttk.Frame(self.top_frame)
        self.left_frame.pack(side=LEFT)
        self.right_frame.pack(side=LEFT)

        self.printing_logger = Logger(self.bottom_frame)

        self.printing_table_path_fd = FileDialog(self.left_frame, 'Путь до excel-таблицы')
        self.printing_unsorted_path_fd = FileDialog(self.left_frame, 'Путь до папки с фото', ask_dir=True)
        self.printing_ext_checker = ExtChecker(self.right_frame)

        self.is_retush = BooleanVar(value=False)
        self.retush_check = ttk.Checkbutton(master=self.right_frame, variable=self.is_retush, text='В одну папку')
        self.retush_check.pack()

        self.sub_dir_include = BooleanVar(value=False)
        self.subdir_check = ttk.Checkbutton(master=self.right_frame, variable=self.sub_dir_include, text='Просматривать подпапки?')
        self.subdir_check.pack()

        self.printing_sort_button = Button(master=self.left_frame, text='Сортировать', command=self._sort_printing)
        self.printing_sort_button.pack()

        self._loop = asyncio.get_event_loop()

    def __del__(self):
        self._loop.close()

    # Сейчас переделали под универсальный формат
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
                                    self.printing_ext_checker.get(), self.is_retush.get(), self.sub_dir_include.get())
            sorter.sort()
        except Exception as exc:
            self.printing_logger.error(str(exc))
            raise

    def run(self):
        self.root.mainloop()
