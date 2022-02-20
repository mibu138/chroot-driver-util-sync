import os
import subprocess as sp

CHROOT = "/chroot/ubuntu2004"
OWNED_FILE = 'owned'
FILTERS_OUT = ('/doc/','/man/','/systemd/','/sysusers.d/','/udev/','/modules-load.d/')

def is_lib(path):
    if '/usr/lib' in path:
        return True
    return False

def get_dst_path(path):
    if is_lib(path):
        path = '/usr/lib/x86_64-linux-gnu' + path[len('/usr/lib'):]
    path = CHROOT + path
    return path

def filter_out(path):
    for f in FILTERS_OUT:
        if f in path:
            return True
    return False

def make_args(copy_args):
    cmd_get_nvidia_utils_files = ['pacman','-Ql','nvidia-utils']
    r = sp.run(cmd_get_nvidia_utils_files, capture_output=True)
    paths = [a.split()[1] for a in r.stdout.decode('utf-8').split('\n')[:-1]]
    for path in paths:
        if filter_out(path):
            continue
        dst = get_dst_path(path)
        # don't copy directories unless they don't exist
        copy_args.append((path, dst))

def check_for_detatched_files(dst_paths):
    ok = True
    with open(OWNED_FILE, 'r') as owned_file:
        lines = owned_file.readlines()
        for line in lines:
            line = line[:-1]
            if line not in dst_paths and os.path.exists(line):
                print(f"{line} should be deleted from chroot. it is not in nvidia-utils")
                ok = False
    return ok
def update_owned(dst_paths):
    with open(OWNED_FILE, 'w') as owned_file:
        for path in dst_paths:
            owned_file.write(path + '\n')

def copy_file(src, dst):
    # safety to make sure we did not mix up the args
    assert(CHROOT in dst)
    cmd = ['cp', '-P', src, dst]
    sp.run(cmd)

def copy_files(copy_args, dry_run=True):
    for args in copy_args:
        src, dst = args
        if dry_run:
            continue
        if os.path.isdir(src):
            if not os.path.exists(dst):
                print(f"Making dir {dst}")
                os.mkdir(dst)
        else:
            print(f"Copying {src} to {dst}")
            copy_file(src, dst)

def run(dry_run=True):
    copy_args = []
    make_args(copy_args)
    dst_paths = [a[1] for a in copy_args]
    ok = True
    ok = check_for_detatched_files(dst_paths)
    if not ok:
        print("Need to delete the detached files. Exitting.")
        return
    update_owned(dst_paths)
    copy_files(copy_args, dry_run)

run(dry_run=False)

