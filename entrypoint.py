import argparse
import os
import socket
import subprocess
import time

host = os.environ.get('HOST')
port = os.environ.get('PORT')
port = int(port)
python_server_port = os.environ.get('PYTHON_SERVER_PORT') or 8000

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--migrate', action='store_const', const=True, default=False,
                        help='start migrate')
    parser.add_argument('-f', '--fixture', default=False, help='Load fixture. \
                        List the fixtures you need.\nExample: --fixture="groups users \
                        licenses files offices floors room_types rooms tables"')
    parser.add_argument('-r', '--runserver', action='store_const', const=True, default=True,
                        help='Run server for Django froject')
    script_arg = parser.parse_args()
    return script_arg

def check_database(host, port):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(1)
        result = client.connect_ex((host, port))
        client.close()
        if result == 0: return True
        else: return False
    except socket.gaierror:
        print(f'Name or service {host}:{port} not known')
    except Exception as e:
        print(e)

def call_command(command):
    subprocess.call(f'{command}', shell=True)

if __name__ == '__main__':
    while True:
        print('\033[31m Check database ... ')
        if check_database(host, port): break
        else: time.sleep(1)

    script_arg = create_parser()

    if script_arg.migrate:
        print('\033[36m \033[4m Start migrate ...')
        call_command("python manage.py makemigrations")
        call_command("python manage.py migrate")

    if script_arg.fixture:
        print('\033[36m \033[4m Start loaddata fixture ...')
        call_command(f"python manage.py loaddata {script_arg.fixture}")

    if script_arg.runserver:
        print('\033[32m \033[4m Run server')
        call_command(f"python manage.py runserver\
                    0.0.0.0:{python_server_port}")
