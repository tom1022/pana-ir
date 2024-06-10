#!/usr/bin/env python3

FRAME0 = "0100000000000100000001110010000000000000000000000000000001100000"

def encode_panasonic_aircon(
    power: str,
    mode: str,
    temp: int,
    strength: str = "auto",
    direction: str = "auto",
    powerful: str = "off",
):
    # byte #1,2,3,4,5 : fixed
    data = "0220e00400"

    # byte #6-1 : mode
    match mode:
        case "auto":
            data += "0"
        case "fan":
            data += "1"
        case "dry":
            data += "2"
        case "cool":
            data += "3"
        case "heat":
            data += "4"

    # byte #6-2 : power
    match power:
        case "off":
            data += "0"
        case "on":
            data += "1"

    # byte #7 : temp
    if 16 <= temp <= 30:
        data += format(temp * 2, "02x")
    else:
        raise ValueError("Temperature must be between 16 and 30")

    # byte #8 : fixed
    data += "80"

    # byte #9-1 : strength
    match strength:
        case "1":
            data += "3"
        case "2":
            data += "4"
        case "3":
            data += "5"
        case "4":
            data += "7"
        case "auto":
            data += "a"
        case "quiet":
            data += "3"

    # byte #9-2 : direction
    match direction:
        case "1":
            data += "1"
        case "2":
            data += "2"
        case "3":
            data += "3"
        case "4":
            data += "4"
        case "5":
            data += "5"
        case "auto":
            data += "f"

    # byte #10,11,12,13 : fixed
    data += "00000660"

    # byte #14 : quiet or pwerful
    if strength == "quiet" and powerful == "off":
        data += "20"
    elif powerful == "on":
        data += "01"
    else:
        data += "00"

    # byte #15,16,17 : fixed
    data += "008000"

    # byte #18 : auto
    if strength == "auto" and mode != "heat":
        data += "16"
    else:
        data += "06"

    # byte #19 : checksum
    data += "{:02x}".format(sum(int(data[i : i + 2], 16) for i in range(0, len(data), 2)) % 256)

    return data

# リモコン信号のhexからAEHAフォーマット準拠のバイナリデータを生成する
def encode_aeha_hex_to_bin(encoded_hex):
    bin_data = ""
    while len(encoded_hex) > 0:
        byte = "{:08b}".format(int(encoded_hex[:2], 16))
        bin_data += byte[::-1]
        encoded_hex = encoded_hex[2:]
    return bin_data

# バイナリデータから赤外線LEDのON/OFFパターンを生成する
def encode_ir_signal(
    format: str,
    encoded_hex: str,
    unit_time: int,
    repeat: int = 1,
):
    if format == "AEHA":
        bin_data = encode_aeha_hex_to_bin(encoded_hex)
        unit_frame = [unit_time * 8, unit_time * 4]
        for b in bin_data:
            if b == "0":
                unit_frame.extend([unit_time, unit_time])
            else:
                unit_frame.extend([unit_time, unit_time * 3])
        frame = []
        for i in range(repeat):
            frame += unit_frame
            frame += [unit_time, unit_time * 30]
        return frame

    if format == "Panasonic":
        unit_frame0 = [unit_time * 8, unit_time * 4]
        for b in FRAME0:
            if b == "0":
                unit_frame0.extend([unit_time, unit_time])
            else:
                unit_frame0.extend([unit_time, unit_time * 3])

        bin_data = encode_aeha_hex_to_bin(encoded_hex)
        unit_frame1 = [unit_time * 8, unit_time * 4]
        for b in bin_data:
            if b == "0":
                unit_frame1.extend([unit_time, unit_time])
            else:
                unit_frame1.extend([unit_time, unit_time * 3])

        frame = []
        for i in range(repeat):
            frame += unit_frame0
            frame += [unit_time, unit_time * 8]
            frame += unit_frame1
            frame += [unit_time, unit_time * 20]
        return frame

from irrp import IRRP
import json
import io

LED_PIN = 17

def ir_send(decoded_code: str):
    ir_code_json = io.StringIO(json.dumps({"ir_code": decoded_code}))
    ir_code_json = json.dumps({"ir_code": decoded_code})
    ir = IRRP(file="/dev/null", no_confirm=True)
    ir.Playback(GPIO=LED_PIN, ID="ir_code", file_object=ir_code_json)
    ir.stop()

def main():
    ir_send(encode_ir_signal("Panasonic", encode_panasonic_aircon("off", "cool", 28, "quiet", "1"), 425, 1))

if __name__ == "__main__":
    main()
