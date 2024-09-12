import socket
import threading
import time

class LedController:
    def __init__(self):
        self.led_status = False
        self.stop_event = threading.Event()  # 停止用のフラグを追加

        # config server
        self.local_ip = '192.168.1.200'
        self.port = 5000

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.local_ip, self.port))
        self.server_socket.listen(10)  # 最大10接続を待機
        self.server_socket.settimeout(1)  # accept()に1秒のタイムアウトを設定
        self.clients = []  # クライアントリスト
        self.name2ip = {"192.168.1.100": "red" , "192.168.1.101": "blue"}
        self.name2id = {}

    def handle_client(self, client_socket, client_address):
        print(f"Connection established with {client_address}")
        try:
            while not self.stop_event.is_set():  # stop_eventがセットされていない限りループ
                self.default_func(client_socket)
        except Exception as e:
            print(f"Error with {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection closed with {client_address}")

    def default_func(self, client_socket):
        # LEDメッセージ送信処理
        client_socket.send(self.generate_msg(200, 0, [0x00, 0x00, 0xFF]))
        time.sleep(0.1)

        client_socket.send(self.generate_msg(200, 0, [0x00, 0x00, 0x00]))
        time.sleep(0.1)

    def start(self,function=None):
        print(f"Server is listening on {self.local_ip}:{self.port}")
        while not self.stop_event.is_set():  # stop_eventがセットされていない限りループ
            try:
                # 新しい接続を受け入れる
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                
                # クライアントごとにスレッドを作成
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address), name=self.name2ip[str(client_address[0])])
                name = str(client_address[0]) 
                print(client_thread.name)
                client_thread.start()
            except socket.timeout:
                # タイムアウト時にstop_eventをチェック
                continue

    def generate_msg(self, led_num, index, colors):
        msg = [0x55, led_num, index]
        msg.extend(colors)
        msg.append(0xAA)
        return bytes(msg)  # バイト列に変換

    def stop(self):
        self.stop_event.set()  # stop_eventをセットしてループを停止させる
        for client in self.clients:
            client.close()
        self.server_socket.close()

if __name__ == '__main__':
    led_controller = LedController()

    try:
        led_controller.start()  # サーバーを起動しクライアントを待つ
    except KeyboardInterrupt:
        print("Server shutting down...")
        led_controller.stop()  # サーバーを停止

# Msg format : START Byte + LED Number + (LED Color[R] + LED Color[G] + LED Color[B]) * LED Number + END Byte
# START Byte : 0x55
# END Byte : 0xAA
# LED Number : 0x01 ~ 0x08
# LED Color : 0x00 ~ 0xFF
# Example : 0x55 0x01 0xFF 0x00 0x00 0xAA
# Msg decode C language function
# void decode_msg(uint8_t *msg, uint8_t *led_num, uint8_t *led_colors) {
#     *led_num = msg[1];
#     for (int i = 0; i < *led_num; i++) {
#         led_colors[i * 3] = msg[2 + i * 3];
#         led_colors[i * 3 + 1] = msg[3 + i * 3];
#         led_colors[i * 3 + 2] = msg[4 + i * 3];
#     }
# }
