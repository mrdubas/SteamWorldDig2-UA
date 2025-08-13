#!/usr/bin/env python3
"""
decompress_z.py

Розпаковує у поточній директорії файли:
  - en.csv.z
  - en_conversations.csv.z
Формати:
  * gzip
  * classic Unix compress (LZW, pure Python)
  * власна обгортка: перші 4 байти + raw deflate (zlib)
Залежностей позбувся: використання лише стандартних модулів.
"""
import os
import gzip
import zlib


def lzw_decompress(compressed):
    # classic Unix compress (.Z) format:
    # header: 1F 9D  (third byte: flags = maxbits + blockmode)
    # data starts from byte 3
    maxbits = compressed[2] & 0x1F
    data = compressed[3:]
    bitstr = ''.join(f'{byte:08b}' for byte in data)
    pos = 0
    dict_size = 256
    dictionary = {i: bytes([i]) for i in range(dict_size)}
    code_size = 9

    def read_code():
        nonlocal pos, code_size
        code = int(bitstr[pos:pos+code_size], 2)
        pos += code_size
        return code

    # first code
    prev_code = read_code()
    result = bytearray(dictionary[prev_code])

    while pos + code_size <= len(bitstr):
        code = read_code()
        if code == 256:  # CLEAR code
            dictionary = {i: bytes([i]) for i in range(256)}
            dict_size = 256
            code_size = 9
            prev_code = read_code()
            result += dictionary[prev_code]
            continue
        if code in dictionary:
            entry = dictionary[code]
        elif code == dict_size:
            entry = dictionary[prev_code] + dictionary[prev_code][:1]
        else:
            break
        result += entry
        # add new sequence
        dictionary[dict_size] = dictionary[prev_code] + entry[:1]
        dict_size += 1
        # increase bitsize
        if dict_size >= (1 << code_size) and code_size < maxbits:
            code_size += 1
        prev_code = code
    return bytes(result)


def decompress(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = f.read()
    header = data[:2]

    # gzip
    if header == b"\x1f\x8b":
        with gzip.open(input_path, 'rb') as src, open(output_path, 'wb') as dst:
            dst.write(src.read())
        print(f"[OK] GZIP -> {output_path}")
        return

    # classic compress LZW
    if header == b"\x1f\x9d":
        try:
            decompressed = lzw_decompress(data)
            with open(output_path, 'wb') as dst:
                dst.write(decompressed)
            print(f"[OK] LZW -> {output_path}")
        except Exception as err:
            print(f"[ERROR] LZW ({input_path}): {err}")
        return

    # raw deflate (skip 4-byte wrapper)
    try:
        payload = data[4:]
        decompressed = zlib.decompress(payload)
        with open(output_path, 'wb') as dst:
            dst.write(decompressed)
        print(f"[OK] DEFLATE -> {output_path}")
    except Exception as err:
        print(f"[ERROR] Unknown format ({input_path}): {err}")


def main():
    targets = ['en.csv.z', 'en_conversations.csv.z']
    for fname in targets:
        if os.path.isfile(fname):
            out_name = fname.rsplit('.', 1)[0]
            decompress(fname, out_name)
        else:
            print(f"[WARN] Not found: {fname}")


if __name__ == '__main__':
    main()
