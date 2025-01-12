import pygame
import math
import numpy as np
import random
import re
from pygame.locals import *
from PyQt6.QtWidgets import QPushButton, QMainWindow, QLineEdit, QLabel, QVBoxLayout, QWidget, QApplication
from websockets.sync.client import connect
import ast
import time

uri = "ws://192.168.1.43:8765"  # Raspberry pi local
uri = "ws://localhost:8765"  # test local
uri = "ws://assheton-jones.co.uk:8765"

anti_alias = True

def draw_board(board, screen):
    screen.fill((255, 255, 255))
    pygame.draw.line(screen, (0, 0, 0), (100, 5), (100, 295))
    pygame.draw.line(screen, (0, 0, 0), (200, 5), (200, 295))
    pygame.draw.line(screen, (0, 0, 0), (5, 100), (295, 100))
    pygame.draw.line(screen, (0, 0, 0), (5, 200), (295, 200))

    for row in range(3):
        for col in range(3):
            character_index = board[row, col]
            character = board_characters[character_index]
            screen.blit(character, (col*100 + 15, row*100 - 15))

def flash_message(screen, message, colour):
    font = pygame.font.SysFont('Comic Sans MS', 20)
    message_red = font.render(message, anti_alias, colour)
    message_white = font.render(message, anti_alias, (255, 255, 255))
    for i in range(8):
        screen.fill(colour)
        screen.blit(message_white, (0, 0))
        time.sleep(.25)
        pygame.display.update()
        screen.fill((255, 255, 255))
        screen.blit(message_red, (0, 0))
        time.sleep(.25)
        pygame.display.update()

def send_message(websocket, type, message, other_name):
    websocket.send(f'{other_name}:{type}:{str(message)}')
    websocket.recv()

def check_for_messages(websocket, my_name):
    websocket.send(f'{my_name}:Check for messages')
    message_and_type = websocket.recv()
    if message_and_type == 'NO MESSAGE':
        return None, None
    else:
        message_type, message = re.findall('^([^:]+):(.*)$', message_and_type)[0]
        return message_type, message

def three_in_a_row(board):
    threes_in_a_row = [
        [(1, 1), (1, 2), (1, 3)],
        [(2, 1), (2, 2), (2, 3)],
        [(3, 1), (3, 2), (3, 3)],
        [(1, 1), (2, 1), (3, 1)],
        [(1, 2), (2, 2), (3, 2)],
        [(1, 3), (2, 3), (3, 3)],
        [(1, 1), (2, 2), (3, 3)],
        [(1, 3), (2, 2), (3, 1)]
    ]

    for player in (1, 2):
        for chain in threes_in_a_row:
            is_a_chain = True
            for row, col in chain:
                if board[row-1, col-1] != player:
                    is_a_chain = False
            if is_a_chain:
                return player

    return 0

def no_one_wins(board):
    unplayed_rows, unplayed_cols = np.where(board == 0)
    if len(unplayed_rows) == 0 and not three_in_a_row(board):
        return True
    else:
        return False

def choose_who_starts(websocket, screen, my_name, other_name):
    print('Choosing who starts')
    my_num = random.random()
    send_message(websocket, 'who_starts_random', my_num, other_name)

    number_received = False
    while not number_received:
        message_type, message = check_for_messages(websocket, my_name)
        print(f'{message_type}:{message}')
        message_pieces = message.split(":")
        if message is None or message_pieces[0] != 'who_starts_random':
            time.sleep(.25)
        else:
            their_num = float(message_pieces[1])
            number_received = True

    if my_num > their_num:
        my_turn = True
        my_symbol = 1
        their_symbol = 2
        flash_message(screen, 'You win!!!  It is your go!!', (0, 255, 255))
    else:
        my_turn = False
        my_symbol = 2
        their_symbol = 1
        flash_message(screen, 'Ohhhh no they get to go first!!', (0, 0, 255))

    return my_turn, my_symbol, their_symbol

class NameWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.enter_your_name = QLabel("Enter your name")
        self.text_box = QLineEdit()
        self.press_once_done = QPushButton("Press once name is entered")
        self.name_entered = None

        self.press_once_done.clicked.connect(self.button_was_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.enter_your_name)
        layout.addWidget(self.text_box)
        layout.addWidget(self.press_once_done)

        vbox = QWidget()
        vbox.setLayout(layout)

        self.setCentralWidget(vbox)

    def button_was_clicked(self):
        if self.text_box.text() != "":    # make sure to check someone else doesn't have the same name later
            self.name_entered = self.text_box.text()
            self.close()

class ChooseYourOpponent(QMainWindow):
    def __init__(self, my_name, websocket):
        super().__init__()
        self.websocket = websocket
        self.my_name = my_name
        self.refresh_oppoonents()

    def send_to_me(self, message):
        self.websocket.send(f'{self.my_name}:{message}')
        reply = self.websocket.recv()
        return reply

    def check_for_message(self):
        message = self.send_to_me('Check for messages')
        return message

    def refresh_oppoonents(self):
        layout = QVBoxLayout()
        list_of_opponents = self.send_to_me("Who can I play?")
        list_of_opponents = ast.literal_eval(list_of_opponents)
        ####message = self.check_for_message()
        ####print(message)
        print(list_of_opponents)
        for opponent in list_of_opponents:
            button = QPushButton(opponent)
            button.clicked.connect(self.you_chose_your_opponent)
            layout.addWidget(button)
        button = QPushButton("Refresh...")
        button.clicked.connect(self.refresh_oppoonents)
        layout.addWidget(button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def you_chose_your_opponent(self):
        print(self.sender().text())
        reply = self.send_to_me(f'I want to play {self.sender().text()}')
        self.close()





def names_gui(websocket):
    app = QApplication([])

    window = NameWindow()
    window.show()

    app.exec()

    window2 = ChooseYourOpponent(window.name_entered, websocket)
    window2.show()

    app.exec()

    while True:
        message = window2.send_to_me('Check for messages')
        message_pieces = message.split(':')
        if message_pieces[1] == 'Ready to play':
            name_to_play = message_pieces[2]
            break
        time.sleep(0.5)

    my_name = window2.my_name
    other_name = name_to_play

    return my_name, other_name








def play_game(my_name, other_name, websocket):
    screen = pygame.display.set_mode((300, 300))
    my_turn, my_symbol, their_symbol = choose_who_starts(websocket, screen, my_name, other_name)
    board = np.zeros((3, 3), dtype=np.int16)


    while True:
        events = pygame.event.get()

        clicked = False
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                break
            if event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                col = max(math.ceil(pos[0]/100), 1) - 1
                row = max(math.ceil(pos[1]/100), 1) - 1
                clicked = True

        if clicked and my_turn and board[row, col] == 0:
            send_message(websocket, 'player_move', row*10 + col, other_name)
            board[row, col] = my_symbol
            my_turn = False

        if not my_turn:
            message_type, message = check_for_messages(websocket, my_name)
            message_pieces = message.split(":")
            if message_pieces[0] is not None and message_pieces[0] == 'player_move':
                row = int(message_pieces[1]) // 10
                col = int(message_pieces[1]) % 10
                board[row, col] = their_symbol
                my_turn = True

        draw_board(board, screen)

        pygame.display.update()
        pygame.time.Clock().tick(30)

        three_in_a_row_result = three_in_a_row(board)
        game_over = False
        if three_in_a_row_result == my_symbol:
            time.sleep(1)
            flash_message(screen, "YOU WIN!!!", (0, 255, 0))
            board = np.zeros((3, 3), dtype=np.int16)
            game_over = True
        if three_in_a_row_result == their_symbol:
            time.sleep(1)
            flash_message(screen, "YOU LOSE!!!", (255, 0, 0))
            board = np.zeros((3, 3), dtype=np.int16)
            game_over = True
        if no_one_wins(board):
            time.sleep(1)
            flash_message(screen, "GREAT.", (128, 128, 128))
            board = np.zeros((3, 3), dtype=np.int16)
            game_over = True

        if game_over:
            my_turn, my_symbol, their_symbol = choose_who_starts(websocket,
                                                                 screen,
                                                                 my_name,
                                                                 other_name)

        pygame.display.update()
        pygame.time.Clock().tick(30)




def run():
    with connect(uri) as websocket:
        my_name, other_name = names_gui(websocket)
        play_game(my_name, other_name, websocket)

if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    ox_font = pygame.font.SysFont('Comic Sans MS', 90)
    board_characters = [
        ox_font.render(" ", False, (0, 0, 0)),
        ox_font.render("O", False, (0, 0, 0)),
        ox_font.render("X", False, (0, 0, 0))
    ]
    run()
