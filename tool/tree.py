import os


def walk(d, fn):
    with os.scandir(d) as it:
        for ent in it:
            p = os.path.join(ent)
            # print(p)
            if ent.is_dir():
                walk(p, fn)
                fn(p, True)
            else:
                fn(p, False)


def walk(d, fn):
    for ent in os.listdir(d):
        p = os.path.join(d, ent)
        # print(p)
        if os.path.isdir(p):
            walk(p, fn)
            fn(p, True)
        else:
            fn(p, False)


def walk(d, fn):
    try:
        for ent in os.listdir(d):
            p = d + '/' + ent
            # print(p)
            walk(p, fn)
            fn(p, xxx)
    except OSError:
        pass


def walk(d, fn):
    try:
        for name, typ, ino, sz in os.ilistdir(d):
            p = d + '/' + name
            # print(p)
            isdir = None
            if typ & 0x4000 != 0:
                isdir = True
            if typ & 0x8000 != 0:
                isdir = False
            walk(p, fn)
            fn(p, isdir)
    except OSError:
        pass


def fn_ls(p, isdir):
    st = os.stat(p)
    st_size = st[6]
    print(f"{p}{'/' if isdir else ''} {st_size if not isdir else ''}")


def fn_rm(p, isdir):
    if isdir:
        os.rmdir(p)
    else:
        os.remove(p)


def lsR(p):
    walk(p, fn_ls)


def rmR(p):
    walk(p, fn_rm)
