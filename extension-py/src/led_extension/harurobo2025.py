"""
RoLIMOAExtensionのかんたんなサンプルコードです

- 同じdispatchに対して複数のコールバック関数を登録することができます
- `task/setTaskUpdate` などはRoLIMOAのReduxのactionに対応しています
- 時間経過を待ちたい場合 `time.sleep()` でなく `asyncio.sleep()` を使います
"""
import threading
from logging import getLogger, StreamHandler, DEBUG
import asyncio
from rolimoa_extension import RoLIMOAExtension
from led_controller import ledController

class harurobo2025_ledController(ledController):
    def __init__(self,scoreCounter:dict):
        super().__init__()
    def default_func(self, client_socket, client_ip):
        try:
            # redのスコアの更新
            if client_ip == "192.168.11.100":
                fieldSide = "red"
            # blueのスコアの更新
            elif client_ip == "192.168.11.101":
                fieldSide = "blue"

            self.set_barrel_led(client_socket, fieldSide, scoreCounter[fieldSide].score_list["beehive_barrel"],scoreCounter[fieldSide].score_list["honney_barrel"])
            self.set_kuma_led(client_socket, fieldSide, scoreCounter[fieldSide].score_list["beehive_kuma"],scoreCounter[fieldSide].score_list["honney_kuma"])

        except Exception as e:
            # print(f"Send error to {client_ip}: {e}")
            with self.lock:
                client_socket.close()
                del self.clients[client_ip]
        
    def set_barrel_led(self, client_socket, fieldSide, beehive_barrel_num, honney_barrel_num):
        with self.lock:
            # kuma_numが0の場合は消灯
            if beehive_barrel_num > 0 or honney_barrel_num > 0:
                if fieldSide == "blue":
                    client_socket.send(self.generate_msg(100, [0x00,  125 * beehive_barrel_num, 125 * honney_barrel_num], 0))
                else:
                    client_socket.send(self.generate_msg(100, [125 * honney_barrel_num, 125 * beehive_barrel_num, 0x00], 0))
            else:
                client_socket.send(self.generate_msg(100, [0x00, 0x00, 0x00], 0))

    def set_kuma_led(self, client_socket, fieldSide, beehive_kuma_num, honney_kuma_num):
        with self.lock:
            # kuma_numが0の場合は消灯
            if beehive_kuma_num > 0 or honney_kuma_num > 0:
                if fieldSide == "blue":
                    client_socket.send(self.generate_msg(200, [0x00,  125 * beehive_kuma_num, 125 * honney_kuma_num], 100))
                else:
                    client_socket.send(self.generate_msg(200, [125 * honney_kuma_num, 125 * beehive_kuma_num, 0x00], 100))
            else:
                client_socket.send(self.generate_msg(200, [0x00, 0x00, 0x00], 100))


async def main(scoreCounterList):
    led_controller = harurobo2025_ledController(scoreCounterList)
    asyncio.create_task(RolimoaThread(scoreCounterList))
    asyncio.create_task(ledControllerThread(led_controller))
    while True:
        await asyncio.sleep(1)

async def RolimoaThread(scoreCounterList):
    print("RolimoaThread")
    # ext = RoLIMOAExtension("ws://localhost:8000/ws")
    ext = RoLIMOAExtension("http://192.168.11.40:8000/")

    try:
        asyncio.create_task(ext.connect())
    except Exception as e:
        print(f"RoLIMOA接続エラー: {e}")

    @ext.on_dispatch("task/setState")
    async def on_set_update(payload: dict):
        scoreCounter["red"].all_clear()
        scoreCounter["blue"].all_clear()
        print("タスクの状態が更新されました")

    @ext.on_dispatch("task/setTaskUpdate")
    async def on_task_update(payload: dict):
        fieldSide = payload["fieldSide"]
        taskObject = payload["taskObjectId"]
        afterValue = payload["afterValue"]
        
        scoreCounter[fieldSide].add_score(taskObject, afterValue)
        print(f"{fieldSide}の合計スコアは{scoreCounter[fieldSide].get_total_score()}です")

        # タスクオブジェクトが変更されたときの処理
        print(f"{fieldSide}の{taskObject}が{afterValue}に更新されました")
    
    await ext.connect()

async def ledControllerThread(led_controller: ledController):
    await asyncio.sleep(1)
    threading.Thread(target=led_controller.start, daemon=True).start()

class scoreCounter:
    def __init__(self,color):
        self.color = color
        # ボタンの入力を記録する　(点数ではない)
        self.score_list = {
            "A" : 0,
            "violation" : 0, 
            "beehive_kuma" : 0, 
            "honney_kuma" : 0, 
            "beehive_barrel" : 0, 
            "honney_barrel" : 0
        }
        self.total_score = 0
        self.kuma_bonus = 0
        self.barrel_bonus = 0
        self.vgoalFlag = False

    def add_score(self, topic , score):
        self.score_list[topic] = score
        
        if self.score_list["beehive_kuma"] > 0 and self.score_list["honney_kuma"] > 0:
            self.kuma_bonus = 60
        else:
            self.kuma_bonus = 0

        if self.score_list["beehive_barrel"] > 0 and self.score_list["honney_barrel"] > 0:
            self.barrel_bonus = 200
        else:
            self.barrel_bonus = 0
            
        self.total_score = self.score_list["A"] * 1 \
                            + self.score_list["beehive_kuma"]  * 40 \
                            + self.score_list["honney_kuma"]  * 40 \
                            + self.score_list["beehive_barrel"]  * 100 \
                            + self.score_list["honney_barrel"]  * 100 \
                            + self.kuma_bonus \
                            + self.barrel_bonus
        
        self.vgoalFlag = True if self.score_list["beehive_barrel"] >= 2 and self.score_list["honney_barrel"] >= 2 else False

    def get_total_score(self):
        return self.total_score
    
    def get_vgoalFlag(self):
        return self.vgoalFlag
    
    def all_clear(self):
        self.score_list = {
            "A" : 0,
            "violation" : 0, 
            "beehive_kuma" : 0, 
            "honney_kuma" : 0, 
            "beehive_barrel" : 0, 
            "honney_barrel" : 0
        }
        self.total_score = 0
        self.kuma_bonus = 0
        self.barrel_bonus = 0
        self.vgoalFlag = False

if __name__ == '__main__':
    scoreCounter = {"red" : scoreCounter("red"), "blue" : scoreCounter("blue")}
    asyncio.run(main(scoreCounter))