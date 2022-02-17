import os
from random import random, randrange

from form import Window

# связка столбца и имени каталога
name_to_col = {
    'Фото в эл.виде    БЕЗ ПЕЧАТИ': 0,
    '1 фото в эл. виде без ретуши': 1,
    '1 фото в эл. виде с ретушью': 2,
    'А6 за 2 шт. одинаковые': 3,
    'А5': 4,
    'А4': 5,
    'А3': 6,
    "Магнит 5 на 7 см": 7,
    "Магнит-рамка горизонтальный  8 на 11 см": 8,
    "Календарь-плакат 30 на 45 см": 9
}


def col_to_name(col_ch):
    for name, col in name_to_col.items():
        if col == col_ch:
            return name
    print('ОШИБКА! нет такого столбца')
    return None


# сделаем для теста набор файлов
def make_test_samples():
    if not os.path.isdir('res'):
        os.mkdir('res')
    # формат названия - RSKN.jpg - N - число копий, S - размер, R - строка, K - порядковый номер в ячейке
    # пройдемся по 4 строкам, больше не надо
    for r in range(4):
        # на данный момент по шаблону 10 столбцов
        for s in range(10):
            # в ячейке rs генерим сколько будет разных файлов
            k = randrange(3)
            # если выпало 0 - нисколько
            if k == 0:
                continue
            for k_n in range(k):
                n = randrange(1, 3)
                # готово создаем файл, картинку не будем(зачем), просто текст
                file_name = './res/'+str(r)+str(s)+str(k_n)+str(n)+'.jpg'
                with open(file_name, 'w+') as f:
                    f.write('a')


# теперь проверим на соответствие. Для этого подсчитаем для каждой суб-директории результата
# какие файлы в ней (и приписку по количеству)
def check_results(res_path):
    # цикл по директориям
    err_num = 0
    for sub_dir in os.listdir(res_path):
        sub_dir_full = os.path.join(res_path, sub_dir)
        if os.path.isdir(sub_dir_full):
            err_num += check_dir(sub_dir_full)
        else:
            print('ОШИБКА: в основной директории обнаружен файл:\n'+str(sub_dir))
            err_num += 1


# проверим директорию и вернём число ошибок
def check_dir(dir_path):
    errors = 0
    for file_n in os.listdir(dir_path):
        if os.path.isdir(os.path.join(dir_path, file_n)):
            errors += 1
            print('ошибочно попала директория в каталог '+str(dir_path)+'\nИмя директории - ' + str(file_n))
        else:
            # 1. расширение не смотрим, т.е. берём [:-4]
            # в тесте не берём больше 9 копий - усложнит тест, но не улучшит тестирование
            # если начинается с + то несколько копий.
            if file_n.startswith('+'):
                n_copies = int(file_n[1])
                parse_name = file_n[2:-4]
            else:
                n_copies = 1
                parse_name = file_n[:-4]
            # N - число копий
            # S - размер (номер столбца, связка с каталогом)
            # остальные не проверяются, служат для уникальности
            R = parse_name[0]
            S = parse_name[1]
            K = parse_name[2]
            N = parse_name[3]
            if N != n_copies:
                errors += 1
                print('неправильное число копий в файле ' + str(os.path.join(dir_path, file_n)))
            if os.path.basename(dir_path) != col_to_name(S):
                errors += 1
                print('неправильная директория файла ' + str(os.path.join(dir_path, file_n)))
    return errors


if __name__ == '__main__':
    # make_test_samples()
    # exit(0)
    wnd = Window()
    wnd.run()
