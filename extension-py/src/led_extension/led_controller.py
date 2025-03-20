import socket
import threading
import time

class ledController:
    def __init__(self):
        self.led_status = False
        self.stop_event = threading.Event()
        self.send_interval = 0.05
        self.clients = {}
        self.lock = threading.Lock()
        self.toggle_count = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('192.168.11.200', 5000))
        self.server_socket.listen(10)
        self.server_socket.settimeout(1)

    def handle_client(self, client_socket, client_address):
        print(f"Connection established with {client_address}")
        with self.lock:
            self.clients[client_address[0]] = client_socket
            self.toggle_count[client_address[0]] = 0
        
        # クライアントごとにスレッドを起動
        threading.Thread(target=self.client_thread_func, args=(client_address[0],), daemon=True).start()

    def client_thread_func(self, client_ip):
        try:
            while not self.stop_event.is_set():
                with self.lock:
                    client_socket = self.clients.get(client_ip)
                    if not client_socket:
                        break

                self.default_func(client_socket, client_ip)
                time.sleep(self.send_interval)
        except Exception as e:
            print(f"Error with {client_ip}: {e}")
        finally:
            with self.lock:
                if client_ip in self.clients:
                    del self.clients[client_ip]
                    del self.toggle_count[client_ip]
            print(f"Connection closed with {client_ip}")

    def send_to_ip(self, ip_address, msg):
        with self.lock:
            if ip_address in self.clients:
                try:
                    client_socket = self.clients[ip_address]
                    client_socket.send(msg)
                    print(f"Message sent to {ip_address}")
                except Exception as e:
                    print(f"Failed to send message to {ip_address}: {e}")
            else:
                print(f"No connection found for {ip_address}")

    def default_func(self, client_socket, client_ip):
        try:
            # print(f"Sending message to {client_ip}")
            self.test_blink(client_socket, client_ip)
        except Exception as e:
            print(f"Send error to {client_ip}: {e}")
            with self.lock:
                client_socket.close()
                del self.clients[client_ip]

    def test_blink(self, client_socket, client_ip):
        with self.lock:
            if self.toggle_count[client_ip] % 2 == 0:
                client_socket.send(self.generate_msg(300, [0x00, 0x00, 0xFF], 0))
            else:
                client_socket.send(self.generate_msg(300, [0xFF, 0x00, 0x00], 0))
            self.toggle_count[client_ip] += 1

    def start(self):
        print("Server is listening on 192.168.11.200:5000")
        while not self.stop_event.is_set():
            try:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
            except socket.timeout:
                continue

    def generate_msg(self, led_num=0, colors=[0, 0, 0], first_indx=0):
        led_num_index = (led_num.bit_length() // 8) + 1
        led_num_bytes = led_num.to_bytes(led_num_index, 'big')
        first_indx_bytes = first_indx.to_bytes(led_num_index, 'big')

        msg = [0x55, led_num_index] + list(led_num_bytes) + list(first_indx_bytes) + colors + [0xAA]
        return bytes(msg)

    def stop(self):
        self.stop_event.set()
        with self.lock:
            for client in self.clients.values():
                client.close()
        self.server_socket.close()
        print("Server shut down.")

if __name__ == '__main__':
    led_controller = ledController()
    try:
        led_controller.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
        led_controller.stop()
