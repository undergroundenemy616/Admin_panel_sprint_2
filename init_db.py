import subprocess

command_list = [
                "python manage.py migrate",
                "python manage.py\
                loaddata groups users \
                licenses files offices \
                floors room_types rooms tables",
                ]

def call_command(command):
    subprocess.call(F'{command}', shell=True)

if __name__ == '__main__':
    for command in command_list:
        try:
            call_command(command)
        except FileNotFoundError as e:
            print(e)