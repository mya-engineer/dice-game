import socket
from random import choice
from time import sleep
from src.player import Player
from signal import SIGINT, signal
from sys import exit
from json import load
from threading import Event


class Server:
    def __init__(self, host: str, port: int) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        self.game_run = Event()
        self.game_run.set()

        signal(SIGINT, self.terminate)

    def terminate(self, *args) -> None:
        self.send_to_clients('Server closed the connection')
        self.send_to_clients('!CLOSE')
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()
        exit()

    def send_to_clients(self, message: str) -> None:
        for _, client_socket in self.client_sockets.items():
            client_socket.sendall(f'{message}\n'.encode())
        sleep(2)

    def set_order(self) -> None:
        choice(self.players).order = 1
        next(player for player in self.players if not player.order).order = 2

    def reset_players(self) -> None:
        for player in self.players:
            player.reset()

    @staticmethod
    def parse_message(message: bytes) -> str:
        return message.decode('utf-8').rstrip()

    def is_full(self):
        return True if len(self.client_sockets) == 2 else False

    def run(self) -> None:
        self.client_sockets = {}
        while True:
            if not self.is_full():
                client_socket, _ = self.server_socket.accept()
            client_socket.sendall(b'Choose username: ')
            sleep(1)
            client_socket.sendall(b'!USERNAME')
            username = client_socket.recv(1024)

            self.client_sockets[Player(username)] = client_socket
            if self.is_full():
                self.players = list(self.client_sockets.keys())
                # Game starts
                while self.game_run.is_set():
                    # phase 1
                    self.send_to_clients(f'Players {" and ".join(map(str, self.client_sockets.keys()))} are ready!')
                    self.send_to_clients('Whose turn is first? Get ready...')
                    self.set_order()
                    # phase 2
                    players = list(self.client_sockets.keys())
                    first = next(player for player in players if player.order == 1)
                    second = next(player for player in players if player.order == 2)
                    self.send_to_clients(f'{first} is first! Roll the dice!')
                    self.client_sockets[first].sendall(b'!ROLL')
                    self.client_sockets[first].recv(1024)
                    self.send_to_clients('Rolling...')
                    first.roll()
                    self.send_to_clients(f'You scored {first.score}! Well done!')
                    self.send_to_clients(f'{second} your turn. Roll the dice!')
                    self.client_sockets[second].sendall(b'!ROLL')
                    self.client_sockets[second].recv(1024)
                    self.send_to_clients('Rolling...')
                    second.roll()
                    self.send_to_clients(f'You scored {second.score}! Nice one!')
                    # phase 3
                    self.send_to_clients('Let\'s check the result! :)')
                    winner = first.username if first.score > second.score else second.username if first.score < second.score else 0 if first.score == second.score else None
                    self.send_to_clients(f'{winner} is winner! Congratulations!' if winner else 'A draw! But you are still well done!')
                    # retry ?
                    self.send_to_clients('One more round? (y/n)')
                    self.send_to_clients('!RETRY')
                    first_response = self.parse_message(self.client_sockets[first].recv(1024))
                    second_response = self.parse_message(self.client_sockets[second].recv(1024))
                    if first_response != 'y' or second_response != 'y':
                        self.game_run.clear()
                        self.terminate()
                        break
                    self.reset_players()
            else:
                self.send_to_clients('Waiting for other players...')


if __name__ == '__main__':
    with open('settings.json') as file:
        settings = load(file)
    Server(settings['HOST'], settings['PORT']).run()
