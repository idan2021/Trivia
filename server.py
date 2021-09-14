##############################################################################
# server.py
##############################################################################
import random
import select
import socket
import chatlib

# GLOBALS
import client

users = {}
questions = {}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later
client_users = []
messages_to_send = []
username = ""

ERROR_MSG = "Error! "
SERVER_PORT = 5682
SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
    global messages_to_send
    full_msg = chatlib.build_message(code, msg)
    messages_to_send.append((conn, full_msg))
    print("[SERVER] ", full_msg)  # Debug print


def recv_message_and_parse(conn):
    global messages_to_send
    try:
        full_msg = conn.recv(1024).decode()
    except OSError as o:
        return None, None
    cmd, data = chatlib.parse_message(full_msg)
    print("[CLIENT] ", full_msg)  # Debug print
    return cmd, data


def print_client_sockets(client_sockets):
    global messages_to_send
    global logged_users
    for c in client_sockets:
        print(c.getpeername())


# Data Loaders #

def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    questions = {
        2313: {"question": "How much is 2+2", "answers": ["3", "4", "2", "1"], "correct": 2},
        4122: {"question": "What is the capital of France?", "answers": ["Lion", "Marseille", "Paris", "Montpellier"],
               "correct": 3}
    }

    return questions


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    users = {
        "test": {"password": "test", "score": 0, "questions_asked": []},
        "yossi": {"password": "123", "score": 50, "questions_asked": []},
        "master": {"password": "master", "score": 200, "questions_asked": []}
    }
    return users


# SOCKET CREATOR

def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
    global messages_to_send
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    sock.listen(5)
    sock.setblocking(0)
    print("The server is up and listening...")
    return sock


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: None
    """
    global messages_to_send
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER.get("login_failed_msg"), error_msg)


##### MESSAGE HANDLING

def create_random_question():
    global messages_to_send
    question_list = list(questions.items())
    question = random.choice(question_list)
    question_string = [str(question[0]), question[1]["question"], chatlib.join_data(question[1]["answers"])]
    return chatlib.join_data(question_string)


def handle_question_message(conn):
    global messages_to_send
    build_and_send_message(conn, "QUESTION", create_random_question())


def handle_answer_message(conn, answer_username, data):
    global messages_to_send
    answer = chatlib.split_data(data, 3)
    if int(answer[1]) == questions[int(answer[0])]["correct"]:  # ERROR
        build_and_send_message(conn, "CORRECT_ANSWER", "")
        users[answer_username]["score"] += 5
    else:
        build_and_send_message(conn, "WRONG_ANSWER", str(questions[int(answer[0])]["correct"]))


def handle_logged_message(conn):
    global messages_to_send
    build_and_send_message(conn, "LOGGED", str(logged_users))


def handle_highscore_message(conn):
    global messages_to_send
    global users
    list_scores = {}
    for i in users:
        list_scores[i] = users[i]["score"]
    var = {k: v for k, v in sorted(list_scores.items(), reverse=True, key=lambda item: item[1])}
    build_and_send_message(conn, "HIGHSCORE", str(var))


def handle_getscore_message(conn, username):
    global messages_to_send
    global users
    build_and_send_message(conn, "SCORE", str(users[username]["score"]))


def handle_logout_message(conn):
    """
    Closes the given socket (in later chapters, also remove user from logged_users dictioary)
    Recieves: socket
    Returns: None
    """
    global messages_to_send
    global logged_users
    user = conn.getpeername()
    print("[SERVER] ", "Thank you", logged_users.pop(user), "for playing, GOODBYE")
    conn.close()


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Recieves: socket, message code and data
    Returns: None (sends answer to client)
    """
    global messages_to_send
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users  # To be used later
    global username
    (username, password) = chatlib.split_data(data, 2)
    for i in users:
        if username == i:
            if password == users[username]['password']:
                build_and_send_message(conn, chatlib.PROTOCOL_SERVER.get("login_ok_msg"), "")
                logged_users[conn.getpeername()] = username
                print("Hi there ", username, " WELCOME")
                return "SUCCESS"
            else:
                send_error(conn, ERROR_MSG + "Wrong password")
                return "ERROR"
        if users is None:
            send_error(conn, ERROR_MSG + "There's no users in the system")
            return "ERROR"
    send_error(conn, ERROR_MSG + "The username doesnt exist")
    return "ERROR"


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global messages_to_send
    global logged_users  # To be used later
    try:
        low = cmd.lower()
    except AttributeError as a:
        print("[SERVER] Theres been an error, reconnect the server...")
        exit()
    if low == "login":
        while True:
            string = handle_login_message(conn, data)
            if string == "SUCCESS":
                break
            if string == "ERROR":
                cmd, data = recv_message_and_parse(conn)
    elif low == "logout":
        handle_logout_message(conn)
    elif low == "score":
        handle_getscore_message(conn, logged_users[conn.getpeername()])
    elif low == "highscore":
        handle_highscore_message(conn)
    elif low == "logged":
        handle_logged_message(conn)
    elif low == "question":
        handle_question_message(conn)
    elif low == "answer":
        handle_answer_message(conn, logged_users[conn.getpeername()], data)
    else:
        send_error(conn, "Theres no such option")


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users, client_users
    global questions
    global messages_to_send
    users = load_user_database()
    questions = load_questions()
    print("Welcome to Trivia Server!")
    sock = setup_socket()
    try:
        while True:
            ready_to_read, ready_to_write, in_error = select.select([sock] + client_users, client_users, [])
            for current_socket in ready_to_read:
                if current_socket is sock:
                    (client_socket, client_address) = current_socket.accept()
                    print("New client joined!", client_address)
                    client_users.append(client_socket)
                    print_client_sockets(client_users)
                else:
                    cmd, data = recv_message_and_parse(current_socket)
                    handle_client_message(current_socket, cmd, data)
                    if cmd == "LOGOUT":
                        client_users.remove(current_socket)
                        current_socket.close()
            for message in messages_to_send:
                client_socket, data = message
                if client_socket in ready_to_write:
                    print("[SERVER] ", client_socket.getpeername(), data)
                    client_socket.send(data.encode())
                    messages_to_send.remove(message)
    except Exception as e:
        del logged_users[username]
        del client_users[:]
        print("[SERVER] Theres been an error, reconnect the server...")


if __name__ == '__main__':
    main()
