#!/usr/bin/env python3
"""
compress_z.py

Упаковує у поточній директорії файли:
  - en.csv
  - en_conversations.csv
Формати:
  * gzip (.gz)
  * classic Unix compress (LZW .Z)
  * власна обгортка: додає 4-байтовий header + raw deflate (zlib)
Не потребує зовнішніх залежностей.
"""
import os
import gzip
import zlib


def lzw_compress(data, maxbits=16):
    dict_size = 256
    dictionary = {bytes([i]): i for i in range(dict_size)}
    string = b""
    result_codes = []

    for symbol in data:
        s = string + bytes([symbol])
        if s in dictionary:
            string = s
        else:
            result_codes.append(dictionary[string])
            dictionary[s] = dict_size
            dict_size += 1
            string = bytes([symbol])
    if string:
        result_codes.append(dictionary[string])

    CLEAR, EOI = 256, 257
    bitbuf, bits_in_buf = 0, 0
    code_size = 9
    output = bytearray()

    def write_code(code):
        nonlocal bitbuf, bits_in_buf, code_size
        bitbuf |= code << bits_in_buf
        bits_in_buf += code_size
        while bits_in_buf >= 8:
            yield bitbuf & 0xFF
            bitbuf >>= 8
            bits_in_buf -= 8

    codes = [CLEAR] + result_codes + [EOI]
    for code in codes:
        for b in write_code(code):
            output.append(b)
        if dict_size >= (1 << code_size) and code_size < maxbits:
            code_size += 1
    if bits_in_buf:
        output.append(bitbuf & 0xFF)

    header = b"\x1f\x9d" + bytes([maxbits])
    return header + bytes(output)


def compress_file(input_path):
    base, ext = os.path.splitext(input_path)
    # Read data
    with open(input_path, 'rb') as f:
        data = f.read()

    # 1. gzip
    gz_path = base + ext + '.gz'  # en.csv -> en.csv.gz
    with gzip.open(gz_path, 'wb') as gz:
        gz.write(data)
    print(f"[OK] GZIP -> {gz_path}")

    # 2. LZW classic
    z_path = base + ext + '.z'  # en.csv -> en.csv.z
    lzw_data = lzw_compress(data)
    with open(z_path, 'wb') as f_z:
        f_z.write(lzw_data)
    print(f"[OK] LZW -> {z_path}")

    # 3. raw deflate wrapper
    dz_path = base + ext + '.z'  # en.csv -> en.csv.z
    comp = zlib.compress(data)
    header = len(data).to_bytes(4, 'little')
    with open(dz_path, 'wb') as f_dz:
        f_dz.write(header + comp)
    print(f"[OK] DEFWRAP -> {dz_path}")


def main():
    files = ['en.csv', 'en_conversations.csv']
    print(f"Working directory: {os.getcwd()}")
    print("Found files:", os.listdir(os.getcwd()))
    for fname in files:
        if os.path.isfile(fname):
            compress_file(fname)
        else:
            print(f"[WARN] Not found: {fname}")
    print("Done.")


if __name__ == '__main__':
    main()
