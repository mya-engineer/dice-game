import socket
from json import load


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    @staticmethod
    def parse_message(message: bytes) -> str:
        return message.decode('utf-8').rstrip()

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            while True:
                data = s.recv(1024)
                message = self.parse_message(data)
                if message.startswith('!'):
                    if message == '!CLOSE':
                        break
                    s.sendall(input().encode())
                else:
                    print(message)


if __name__ == '__main__':
    with open('settings.json') as file:
        settings = load(file)
    Client(settings['HOST'], settings['PORT']).run()
