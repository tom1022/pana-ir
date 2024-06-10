#!/usr/bin/env python3

from irrp import IRRP
import json
import io
import argparse


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

def ir_send(decoded_code: str, led_pin: int = 17):
    ir_code_json = io.StringIO(json.dumps({"ir_code": decoded_code}))
    ir_code_json = json.dumps({"ir_code": decoded_code})
    ir = IRRP(file="/dev/null", no_confirm=True)
    ir.Playback(GPIO=led_pin, ID="ir_code", file_object=ir_code_json)
    ir.stop()

def control_aircon(
    power: str,
    mode: str,
    temp: int,
    led_pin: int = 17,
    strength: str = "auto",
    direction: str = "auto",
    powerful: str = "off",
    unit_time: int = 425,
    repeat: int = 1
):
    encoded_hex = encode_panasonic_aircon(power, mode, temp, strength, direction, powerful)
    ir_signal = encode_ir_signal("Panasonic", encoded_hex, unit_time, repeat)
    ir_send(ir_signal, led_pin=led_pin)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and send Panasonic aircon IR signal.")
    parser.add_argument("--power", type=str, required=True, help="Power state: on/off")
    parser.add_argument("--mode", type=str, required=True, help="Mode: auto/fan/dry/cool/heat")
    parser.add_argument("--temp", type=int, required=True, help="Temperature (16-30)")
    parser.add_argument("--led_pin", type=int, default=17, help="GPIO pin for IR LED")
    parser.add_argument("--strength", type=str, default="auto", help="Fan strength: 1(min)/2/3/4(max)/auto/quiet")
    parser.add_argument("--direction", type=str, default="auto", help="Fan direction: 1(horizontal)/2/3/4/5(vertical)/auto")
    parser.add_argument("--powerful", type=str, default="off", help="Powerful mode: on/off")
    parser.add_argument("--unit_time", type=int, default=425, help="Unit time for IR signal")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to repeat the signal")
    parser.add_argument("--send", action="store_true", help="Send the generated IR signal")

    args = parser.parse_args()

    encoded_hex = encode_panasonic_aircon(
        args.power,
        args.mode,
        args.temp,
        args.strength,
        args.direction,
        args.powerful
    )

    ir_signal = encode_ir_signal("Panasonic", encoded_hex, args.unit_time, args.repeat)

    if args.send:
        ir_send(ir_signal, led_pin=args.led_pin)
    else:
        print("Generated IR Signal:", ir_signal)