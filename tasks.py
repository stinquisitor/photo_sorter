import glob
from pathlib import Path

import aiofiles

import constants


class TaskCreator:
    def __init__(self, summary, extension, unsorted_dir: Path):
        self._tasks = {}
        self._summary = summary
        self._extension = extension
        self._file_list = {}
        self.fill_file_list(unsorted_dir)

    def strip_file_name(self, name: str):
        import re
        reg = r'\D*(\d*)[.](\w*)'
        num, ext = re.findall(reg, name)[0]
        if ext is not None:
            ext = ext.lower()
        return num, str('.'+ext)

    # создадим список файлов, чтобы не заниматься потом фигнёй с поиском файла в цикле.
    # поскольку вариантов может быть по факту много с расширениями.
    def fill_file_list(self, unsorted_dir: Path):
        # сначала получаем список файлов с заданным расширением.
        # если установлено "ВСЕ" - не смотрим на расширения
        if self._extension == 'ВСЕ':
            for item in Path.iterdir(unsorted_dir):
                if Path.is_file(item):
                    num, ext = self.strip_file_name(item.name)
                    if ext is not None and ext in constants.extensions:
                        self._file_list[str(num)] = item.name

        # если установлено "ФОТО" - смотрим только фото-расширения
        elif self._extension == 'ФОТО':
            for item in Path.iterdir(unsorted_dir):
                if Path.is_file(item):
                    num, ext = self.strip_file_name(item.name)
                    if ext is not None and ext in constants.extensions:
                        self._file_list[str(num)] = item.name
        else:
            for item in Path.iterdir(unsorted_dir):
                if Path.is_file(item):
                    num, ext = self.strip_file_name(item.name)
                    if ext is not None and ext == self._extension:
                        self._file_list[str(num)] = item.name

    def add_task(self, unsorted_dir: Path, num: str, out_dir: Path, logger, copies: int = 1,
                 summary=True, metadata=None):
        key = (num, out_dir)
        summary = self._summary if summary else None
        # !!! файла с таким расширением не нашлось
        if str(num) not in self._file_list.keys():
            if self._summary:
                self._summary.add_miss_file(num, out_dir, '')
                return
        if key not in self._tasks.keys():
            self._tasks[key] = Task(unsorted_dir, num, out_dir, logger, summary, metadata, self._extension,
                                    filename=self._file_list[str(num)])
        self._tasks[key].increase(copies)

    @property
    def tasks(self):
        return list(self._tasks.values())


class Task:
    def __init__(self, unsorted_dir: Path, num: str, out_dir: Path, logger, summary, metadata, extension, filename):
        self._unsorted_dir = unsorted_dir
        self._out_dir = out_dir
        self._logger = logger
        self._num = num
        self._cnt = 0
        self._summary = summary
        self._metadata = metadata
        self._extension = extension
        self._filename = filename

    async def copy_file(self):
        missed = True

        cur_file = Path(f'{str(self._unsorted_dir)}/{self._filename}')
        missed = False
        async with aiofiles.open(cur_file, mode='rb') as input_file:
            self._out_dir.mkdir(exist_ok=True)
            out_file_name = cur_file.name if self._cnt <= 1 else f'+{self._cnt}_{cur_file.name}'
            async with aiofiles.open(str(self._out_dir / out_file_name), mode='wb') as out_file:
                data = await input_file.read()
                await out_file.write(data)

                self._logger.info(f'Скопирован файл {cur_file.name} в директорию {self._out_dir}')
                if self._summary:
                    self._summary.add(self._out_dir, self._cnt, photo_name=self._num)

        if missed:
            if self._summary:
                self._summary.add_miss_file(self._num, self._out_dir, self._metadata)


    async def copy_file_old(self):
        missed = True
        cur_file_names = [f'{str(self._unsorted_dir)}/IMG_{self._num}{self._extension}',
                          f'{str(self._unsorted_dir)}/{self._num}{self._extension}',
                          f'{str(self._unsorted_dir)}/IMG_{self._num}{self._extension.upper()}',
                          f'{str(self._unsorted_dir)}/{self._num}{self._extension.upper()}']
        for cur_file in cur_file_names:
            cur_file = Path(cur_file)
            if not cur_file.exists():
                continue
            missed = False
            async with aiofiles.open(cur_file, mode='rb') as input_file:
                self._out_dir.mkdir(exist_ok=True)
                out_file_name = cur_file.name if self._cnt <= 1 else f'+{self._cnt}_{cur_file.name}'
                async with aiofiles.open(str(self._out_dir / out_file_name), mode='wb') as out_file:
                    data = await input_file.read()
                    await out_file.write(data)

                    self._logger.info(f'Скопирован файл {cur_file.name} в директорию {self._out_dir}')
                    if self._summary:
                        self._summary.add(self._out_dir, self._cnt, photo_name=self._num)

        if missed:
            if self._summary:
                self._summary.add_miss_file(self._num, self._out_dir, self._metadata)

    def increase(self, copies: int=1):
        self._cnt += copies

    def __repr__(self):
        return f'<{self.__class__}> Copy "{self._num}" to "{self._out_dir}"'

    def __str__(self):
        return self.__repr__()
