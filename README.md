# Panasonic 赤外線リモコン

## 概要

Panasonicのエアコンの赤外線リモコン(A475C3639)を解析してラズベリーパイから操作できるようにしました．

## 使い方

### 必要なソフトウェア

- pigpio

### コマンドラインから使う場合

```bash
python3 pana-ir.py --power on --mode cool --temp 28 --led_pin 17
```

備考

```text
python3 pana-ir.py -h
usage: pana-ir.py [-h] --power POWER --mode MODE --temp TEMP [--led_pin LED_PIN] [--strength STRENGTH]
                  [--direction DIRECTION] [--powerful POWERFUL] [--unit_time UNIT_TIME] [--repeat REPEAT] [--send]

Generate and send Panasonic aircon IR signal.

options:
  -h, --help            show this help message and exit
  --power POWER         Power state: on/off
  --mode MODE           Mode: auto/fan/dry/cool/heat
  --temp TEMP           Temperature (16-30)
  --led_pin LED_PIN     GPIO pin for IR LED
  --strength STRENGTH   Fan strength: 1(min)/2/3/4(max)/auto/quiet
  --direction DIRECTION
                        Fan direction: 1(horizontal)/2/3/4/5(vertical)/auto
  --powerful POWERFUL   Powerful mode: on/off
  --unit_time UNIT_TIME
                        Unit time for IR signal
  --repeat REPEAT       Number of times to repeat the signal
  --send                Send the generated IR signal
```

### プログラムに埋め込む場合

```python
from pana-ir import control_aircon

control_aircon(
    power = "on",
    mode = "cool",
    temp = 28,
    led_pin = 17,
    strength = "auto",
    direction = "auto",
    powerful = "off",
    unit_time = 425,
    repeat = 1
)

```

## 解析結果

### モード切替 #6-1

| mode | hex |
| --- | --- |
| auto | 0 |
| fan? | 1 |
| dry | 2 |
| cool | 3 |
| hot | 4 |

### 電源 #6-2

| power | hex |
| --- | --- |
| on | 1 |
| off | 0 |

### 温度設定 #7

16から30度までで以下の式に従う

```python
format(temp * 2, "02x")
```

### 風量 #9-1

| strength | hex ||
| --- | --- | --- |
| 1(min) | 3 |  |
| 2 | 4 |  |
| 3 | 5 |  |
| 4(max) | 7 |  |
| auto | a | #18-1が0→1 |
| quiet | 3 | #14-1が0→2 |

### 風向 #9-2

| direction | hex |
| --- | --- |
| 1(horizontal) | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| auto | f |

### パワフル #14-2

|  | hex |
| --- | --- |
| on | 1 |
| off | 0 |

## 参考文献

- [格安スマートリモコンの作り方](https://qiita.com/takjg/items/e6b8af53421be54b62c9)
- [赤外線リモコンの通信フォーマット](http://elm-chan.org/docs/ir_format.html)
- [Pythonでエアコンのリモコン信号をデコードしパースする](https://zenn.dev/mikiken/articles/decode-ir-signal)
- [Pythonでエアコンのリモコン信号を解析し自在に操作できるようにする](https://zenn.dev/mikiken/articles/encode-ir-signal)
- [Reverse engineering the Panasonic AC Infrared protocol
](https://www.analysir.com/blog/2014/12/27/reverse-engineering-panasonic-ac-infrared-protocol/)
- [ラズパイ スマートリモコン化でおなじみの irrp.py が扱いにくかったので勝手にモジュール化してみた。](https://qiita.com/Cartelet/items/1a451ec0abf5734aceae)

なお `irrp.py` については少し改変してあります．
