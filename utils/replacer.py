

symbols = {'e': "е",
           'y': "у",
           'i': "і",
           'o': "о",
           'p': "р",
           'a': "а",
           'k': "к",
           'x': "х",
           'c': "с",
           'E': "Е",
           'T': "Т",
           'Y': "У",
           'I': "І",
           'O': "О",
           'P': "Р",
           'A': "А",
           'H': "Н",
           'K': "К",
           'X': "Х",
           'C': "С",
           'B': "В",
           'M': "М",
           }


def replace_symbols(string: str) -> str:
    result = ""
    for num, sym in enumerate(string):
        if sym in symbols:
            result += symbols[sym]
        else:
            result += sym

    return result
