import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5682
username = ""
password = ""


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    full_msg = chatlib.build_message(code, data)
    send_msg = conn.send(full_msg.encode())
    print(full_msg)


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
    then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    full_msg = conn.recv(1024).decode()
    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data


def build_send_recv_parse(conn, cmd, data):
    full_msg = chatlib.build_message(cmd, data)
    conn.send(full_msg.encode())
    full_msg = conn.recv(1024).decode()
    msg_code, data = chatlib.parse_message(full_msg)
    return msg_code, data


# GAME FUNCTIONS

def get_score(conn):
    msg_code, data = build_send_recv_parse(conn, "SCORE", username + "#" + password)
    if msg_code.lower() != "score":
        print("There's been error with the score, try again\n")
    print("Your score is: " + data)


def get_highscore(conn):
    highscore_string = build_send_recv_parse(conn, "HIGHSCORE", "")[1]
    highscore_string = highscore_string.replace("{", "")
    highscore_string = highscore_string.replace("}", "")
    print(highscore_string.replace(", ", "\n"))


def play_question(conn):
    try:
        send_cmd, send_data = build_send_recv_parse(conn, "QUESTION", "")
        question_list = chatlib.split_data(send_data, 6)
        print("Q: ", question_list[1], ":\n\t1. ", question_list[2], "\n\t2. ", question_list[3], "\n\t3. ",
              question_list[4], "\n\t4. ", question_list[5])
        answer = input("Please choose the correct answer:\n")
        question_answer_code, question_answer_data = build_send_recv_parse(conn, "ANSWER",
                                                                           question_list[0] + "#" + answer)
        if question_answer_code == "CORRECT_ANSWER":
            print("Correct! " + question_answer_data)
        else:
            print("Wrong! the correct answer is: " + question_answer_data)
    except Exception as e:
        print(e)
        return 0


def get_logged_users(conn):
    msg_code, data = build_send_recv_parse(conn, "LOGGED", "")
    print(data)


def connect():
    connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_socket.connect((SERVER_IP, SERVER_PORT))
    return connect_socket


def error_and_exit(error_msg):
    print(error_msg)
    exit()


def login(conn):
    global username, password
    while True:
        username = input("Please enter username: \n")
        password = input("Please enter password: \n")
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], username + "#" + password)
        cmd, data = recv_message_and_parse(conn)
        if cmd is None or data is None or cmd == "ERROR":
            print("The login has failed, please try again!")
        else:
            print("You logged in successfully")
            break


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")


def main():
    conn = connect()
    print(conn)
    login(conn)
    while True:
        user_input = input("Please choose the option you would like to do\n" +
                           "p\tPlay a trivia question\ns\tGet my score\nh\tGet high scores\nl\tGet logged users\n" +
                           "q\tQuit\n")
        if user_input == "q":
            logout(conn)
            break
        elif user_input == "s":
            get_score(conn)
        elif user_input == "h":
            get_highscore(conn)
        elif user_input == "p":
            play_question(conn)
        elif user_input == "l":
            get_logged_users(conn)
        elif user_input=="":
            continue
        else:
            raise TypeError("There seems to have a problem...")
    conn.close()
    exit()


if __name__ == '__main__':
    main()
