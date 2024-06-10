import json
import argparse

p = argparse.ArgumentParser()
p.add_argument("-f", "--file", help="Filename", required=True)
args = p.parse_args()

def normalize(code, T=425):
    normalized_code = []
    frame = []
    for i in range(len(code)):
        period = round(code[i] / T)
        if period > 8:
            normalized_code.append(frame)
            frame = []
        else:
            frame.append(period)
    normalized_code.append(frame)
    return normalized_code

def decode_to_binary(normalized_code):
    block = []
    data_frame = ""
    for frame_index, frame in enumerate(normalized_code):
        # フレーム#1を無視し、フレーム#2のみを処理
        if frame_index == 0:
            continue
        for i in range(0, len(frame) - 1, 2):
            if frame[i] == 8 and frame[i + 1] == 4:
                continue
            elif frame[i] == 1 and frame[i + 1] == 1:
                data_frame += "0"
            elif frame[i] == 1 and frame[i + 1] == 3:
                data_frame += "1"
            else:
                raise ValueError(f"Unable to decode at frame {frame_index}, position {i}. Values: {frame[i]}, {frame[i + 1]}")
        block.append(data_frame)
        data_frame = ""

    return block[0], len(block)

def parse_binary_code_as_hex(binary_code):
    hex_code = ""
    while len(binary_code) > 0:
        hex_code += "{:02x}".format(int(binary_code[7::-1], 2))
        binary_code = binary_code[8:]
    return hex_code

with open(args.file, "r") as f:
    records = json.load(f)

for key, values in records.items():
    normalized_code = normalize(values)
    try:
        binary_code, n_frame = decode_to_binary(normalized_code)
        hex_code = parse_binary_code_as_hex(binary_code)
        formatted_hex_code = ' '.join([str(hex_code)[i:i+2] for i in range(0, len(hex_code), 2)])
        print(f"{key}: {formatted_hex_code}")
    except ValueError as e:
        print(f"Error decoding {key}: {e}")
