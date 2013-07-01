import argparse
import subprocess
import os
import sys

import hgapi


def make_zip():
    pass


def do_mac_release(args):
    print args
    # dist_dir = "dist_build"
    # bin_dir = os.path.join(dist_dir, 'dist')

    # if os.path.isdir(bin_dir):
    #    print "Removing existing {0}".format(bin_dir)
    #    shutil.rmtree(bin_dir)
    cmd_template = "python {0}  -D  -n LSJuicer -w run_qt.py"
    # cmd_template = "python {0}  -F --clean -n LSJuicer -w run_qt.py"
    cmd = cmd_template.format(args.pyinstaller_cmd)
    print 'Executing: %s' % cmd
    res = subprocess.call(cmd, shell=True)
    print res
    # juicer_dir = os.path.join(dist_dir, 'LSJuicer')
    # if os.path.isdir(juicer_dir):
    #    print "Removing existing {0}".format(juicer_dir)
    #    shutil.rmtree(juicer_dir)
    # shutil.copytree("bftools",os.path.join(bin_dir,'bftools'))
    # shutil.move(bin_dir, juicer_dir)
    # fname = "LSJuicer_{0}_{1}".format(args.tag.replace(" ","_"), "MacOS")
    # archive_name = shutil.make_archive(fname, "zip", root_dir = juicer_dir)
    # print "Created {0}".format(archive_name)


def up_to_tag(tag):
    repo = hgapi.Repo(".")
    all_tags = repo.hg_tags()
    if args.tag == "tip":
        print "If you want to do a release from <tip> then please set an appropriate tag."
        print "Tags already present:"
        print ", ".join([str(el) for el in all_tags])
        return False
    else:
        if tag in all_tags:
            print "Tag <{0}> found. Uping...".format(tag)
            repo.hg_update(tag)
            return True
        else:
            print "Tag {0} not present in repository. Quitting...".format(args.tag)
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pyinstaller_dir", type=str, help="PyInstaller directory")
    parser.add_argument("tag", type=str, help="Tag to make release for")
    args = parser.parse_args()
    if not up_to_tag(args.tag):
        sys.exit(1)
    pyinstaller_cmd = os.path.join(args.pyinstaller_dir, 'pyinstaller.py')
    args.pyinstaller_cmd = pyinstaller_cmd
    do_mac_release(args)
