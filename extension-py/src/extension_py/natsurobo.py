from rolimoa_extension import RoLIMOAExtension
from led_controller import LedController

class LedStatus:
    def __init__(self):
        self.color = [0, 0, 0]

    def set_color(self, color):
        self.color = color

    def get_color(self):
        return self.color

if __name__ == '__main__':
    led_controller = LedController()

    extension = RoLIMOAExtension(
        url="ws://localhost:8000/ws"
    )

    @extension.on_dispatch("task/setTaskUpdate")
    def on_task_update(payload: dict):
        fieldSide = payload["fieldSide"]
        taskObject = payload["taskObjectId"]
        afterValue = payload["afterValue"]

        print(f"{fieldSide}チームの{taskObject}が{afterValue}に更新されました")
        
        if fieldSide == "red":
            led_controller.send_msg(led_controller.generate_msg(200, [0xFF, 0x00, 0x00]))
        elif fieldSide == "blue":
            led_controller.send_msg(led_controller.generate_msg(200, [0x00, 0x00, 0xFF]))

    @extension.on_dispatch("task/setGlobalUpdate")
    def on_global_update(payload: dict):
        taskObject = payload["taskObjectId"]
        afterValue = payload["afterValue"]

        print(f"{taskObject}が{afterValue}に更新されました")

    try:
        led_controller.start()
        extension.connect()
    except KeyboardInterrupt:
        print("Server shutting down...")
        led_controller.stop()
