import argparse
import os
import re
import sys

from tqdm import tqdm
from colorama import Fore

BUFFER_SIZE = 16 * 1024


def error(msg: any):
    print(f"{Fore.LIGHTRED_EX}[ERROR] {msg}{Fore.RESET}", file=sys.stderr)


def confirm(message: str = "Confirm action?", yes: str = "y", no: str = "n") -> bool:
    while True:
        answer = input(f"{message} ({yes}/{no}): ").lower()
        if answer in {yes, no}:
            break

    return answer == yes


def get_files(inputs: list[str]) -> list[str]:
    input_files = []
    for arg in inputs:
        if os.path.isdir(arg):
            input_files.extend(
                os.path.join(arg, name)
                for name in os.listdir(arg)
                if os.path.isfile(os.path.join(arg, name))
            )
        else:
            input_files.append(arg)

    files = []
    for file in input_files:
        base_name = os.path.basename(file)
        if "*" in base_name:
            dir_name = os.path.dirname(file)
            pattern = re.escape(base_name).replace("*", r"d+")
            for name in os.listdir(os.path.abspath(dir_name)):
                file = os.path.join(dir_name, name)
                if re.match(pattern, name) and os.path.isfile(file):
                    files.append(file)
        else:
            files.append(file)

    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="+")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-y", "--yes", action="store_true")
    args = parser.parse_args()

    files = get_files(args.input)

    if not args.yes and os.path.exists(args.output):
        if not confirm(
            f'File "{args.output}" already exists. Add data to the end of it?'
        ):
            return

    if len(files) > 1:
        iterator = tqdm(files, desc="Join", unit="file")
        leave = False
    else:
        iterator = files
        leave = True

    with open(args.output, "ab") as fw:
        for file in iterator:
            with (
                open(file, "rb") as fr,
                tqdm(
                    total=os.path.getsize(file),
                    unit="iB",
                    unit_scale=True,
                    desc=os.path.basename(file),
                    leave=leave,
                ) as pbar,
            ):
                buf = "\0"
                while len(buf):
                    buf = fr.read(BUFFER_SIZE)
                    fw.write(buf)
                    pbar.update(len(buf))


if __name__ == "__main__":
    try:
        main()
    except Exception as _e:
        error(_e)
