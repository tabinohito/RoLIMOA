import socket
import threading
import time  # timeモジュールのインポート
from rolimoa_extension import RoLIMOAExtension
from led_controller import LedController
from datetime import datetime  # datetimeモジュールを使う
import asyncio

class LedStatus:
    def __init__(self):
        self.colors = {}  # IPアドレスごとに色を管理する辞書

    def set_color(self, ip, color, length=None):
        """特定のIPアドレスに対して色を設定"""
        self.colors[ip] = color

    def get_color(self, ip):
        """特定のIPアドレスに対応する色を取得。存在しない場合は黒を返す。"""
        return self.colors.get(ip, [0, 0, 0])

class LedControllerWithThreads(LedController):
    def __init__(self):
        super().__init__()
        self.led_status = LedStatus()  # 全体で共有するLEDの色
        self.lock = threading.Lock()  # スレッド間でのデータ競合を防ぐためのロック
        self.stop_event = threading.Event()  # サーバ停止用のイベント
        self.threads = []  # クライアントごとのスレッド管理
        self.loop = asyncio.new_event_loop()  # asyncioイベントループを作成
        threading.Thread(target=self.loop.run_forever).start()  # 非同期タスク用のスレッドを開始

    def start(self):
        """サーバーを開始する"""
        self.server_socket.listen(10)
        print(f"Server is listening on {self.local_ip}:{self.port}")

        while not self.stop_event.is_set():
            try:
                self.server_socket.settimeout(1.0)  # サーバソケットにタイムアウトを設定してstop_eventを定期的にチェック
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.start()
                self.threads.append(client_thread)  # スレッドを管理リストに追加
            except socket.timeout:
                continue  # タイムアウト発生時はstop_eventを確認するために再ループ
            except OSError:
                # ソケットが閉じられた場合の処理
                break

    def handle_client(self, client_socket, client_address):
        ip = client_address[0]
        print(f"Connection established with {client_address}")
        try:
            while not self.stop_event.is_set():
                with self.lock:
                    color = self.led_status.get_color(ip)  # 現在のLEDの色を取得
                client_socket.send(self.generate_msg(200, 0, color))  # クライアントにメッセージを送信
                time.sleep(0.1)
        except Exception as e:
            print(f"Error with {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed with {client_address}")

    def set_color_for_ip(self, ip, color):
        """LEDの色を設定"""
        with self.lock:
            print(f"Setting color for {ip} to {color}")
            self.led_status.set_color(ip, color)

    async def turn_off_after_delay(self, ip, delay=10):
        """指定したIPのLEDを一定時間後に消灯"""
        for i in range(delay):
            await asyncio.sleep(1)  # 指定時間だけ待機
            print(f"Turning off LED for {ip} in {delay - i} seconds")
        with self.lock:
            self.led_status.set_color(ip, [0, 0, 0])  # 消灯
        print(f"Turned off LED for {ip}")

    def stop(self):
        """サーバーを停止するための関数"""
        self.stop_event.set()  # 停止イベントを設定
        try:
            self.server_socket.close()  # サーバソケットを閉じる
        except OSError:
            pass  # サーバソケットが既に閉じられている場合を考慮

        for thread in self.threads:
            thread.join(timeout=2.0)  # 各スレッドが確実に終了するのを待つ（タイムアウト付き）

        self.loop.call_soon_threadsafe(self.loop.stop)  # イベントループを停止

def start_extension_connection(extension):
    """RoLIMOAExtensionの接続を別スレッドで実行"""
    extension.connect()

if __name__ == '__main__':
    led_controller = LedControllerWithThreads()

    extension = RoLIMOAExtension(
        url="ws://localhost:8000/ws"
        # url="ws://192.168.11.40:8000/ws"
    )

    @extension.on_dispatch("task/setTaskUpdate")
    def on_task_update(payload: dict):
        fieldSide = payload["fieldSide"]
        taskObject = payload["taskObjectId"]
        afterValue = payload["afterValue"]

        print(f"{fieldSide}チームの{taskObject}が{afterValue}に更新されました")

        # IPアドレスに応じて色を設定（例として適当なIPアドレスを使用）
        ip_address = None
        if fieldSide == "red":
            ip_address = "192.168.1.100"  # 実際のクライアントのIPアドレスを指定

        elif fieldSide == "blue":
            ip_address = "192.168.1.101"  # 実際のクライアントのIPアドレスを指定
            print(fieldSide)

        # 加熱の場合
        if taskObject == "heating":
            if afterValue == 1:
                # LEDを赤色に点灯
                led_controller.set_color_for_ip(ip_address, [255, 75, 0x00])

                # 10秒後に非同期で消灯
                asyncio.run_coroutine_threadsafe(
                    led_controller.turn_off_after_delay(ip_address, delay=10),
                    led_controller.loop
                )
            else:
                # LEDをすぐに消灯
                led_controller.set_color_for_ip(ip_address, [0x00, 0x00, 0x00])

    @extension.on_dispatch("task/setGlobalUpdate")
    def on_global_update(payload: dict):
        taskObject = payload["taskObjectId"]
        afterValue = payload["afterValue"]

        print(f"{taskObject}が{afterValue}に更新されました")

    try:
        # LED Controllerのサーバーを開始
        print("Server is starting...")

        # RoLIMOAExtensionの接続を別スレッドで実行
        extension_thread = threading.Thread(target=start_extension_connection, args=(extension,))
        extension_thread.start()

        # LED controllerの処理を開始
        led_controller.start()

    except KeyboardInterrupt:
        print("Server shutting down...")

        # サーバ停止とクライアントスレッドの終了
        led_controller.stop()

        # RoLIMOAExtensionスレッドの終了を待機
        extension_thread.join(timeout=5.0)

        print("Shutdown complete.")
