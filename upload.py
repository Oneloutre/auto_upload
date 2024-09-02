import os
import json
import re
import paramiko
from scp import SCPClient

TGREEN = '\033[32m'
TRED = '\033[31m'
TRESET = '\033[0m'
TYELLOW = '\033[33m'

sourceforge_remote_path = "/home/frs/p/evolution-x"
sourceforge_host = "frs.sourceforge.net"
config_folder = "upload_config"
config_creds = "upload_config/credentials.json"
config_devices = "upload_config/devices/"
out = "../out/target/product/"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def create_creds():
    print(TYELLOW + "Config file not found. Creating a new one...")
    pseudo = input(TRESET + "Enter your SourceForge username: ")
    password = input(TRESET + "Enter your SourceForge password: ")
    android_version = input(TRESET + "Enter the Android version you are uploading (Ex: 11): ")
    os.environ["SOURCEFORGE_USERNAME"] = pseudo

    with open(config_creds, "w") as f:
        f.write(f'{{"username": "{pseudo}", "password": "{password}", "android_version": "{android_version}"}}')
    print(TGREEN + "Config file created successfully. User : " + pseudo)
    return pseudo


def check_creds():
    if not os.path.exists(config_creds):
        print(TRED + "Config file not found. Please run the script with '-i' or 'init' to create a new one.")
        return False
    else:
        return True


def init():
    if not os.path.exists(config_folder):
        print(TYELLOW + "Config folder not found. Creating a new one...")
        os.mkdir(config_folder)
        os.mkdir(config_devices)
        create_creds()
    else:
        if not os.path.exists(config_creds):
            create_creds()
        else:
            username = os.environ.get("SOURCEFORGE_USERNAME")
            if username is None:
                with open(config_creds, "r") as f:
                    data = json.load(f)
                    username = data["username"]
            print(TGREEN + "Config file read successfully. Welcome, " + username)


def upload_rom_file(device):
    rom_file = "../out/target/product/" + device + "/EvolutionX*.zip"
    if not os.path.exists(rom_file):
        print("ROM file not found. Exiting...")
        return
    else:
        print("ROM file found. Uploading...")
        os.system(f"rsync -avz --progress --partial --inplace --rsh=ssh {rom_file} {sourceforge_remote_path}")
        print("ROM file uploaded successfully.")


def generate_device_file(device, file_list):
    data = {
        "device": device,
        "files": file_list
    }

    with open(config_devices + device + ".json", 'w') as outfile:
        json.dump(data, outfile, indent=4)

    print(TGREEN + f"File '{device}.json' has been generated successfully.")


def add_device():
    if not check_creds():
        return
    device = input(TYELLOW + "Please input device's codename : ")
    if device == "":
        print(TRED + "You must input a device codename.")
        return
    elif os.path.exists(config_devices + device + ".json"):
        response = input(TRED + "Be careful, this device already exists ! override ? (y/N) : ")
        if response.lower() != "y":
            print(TRED + "Aborting...")
            return
        else:
            os.remove(config_devices + device + ".json")
    i = input(TYELLOW + "How many files are mandatory ? (without the ROM file) : ")
    if i.strip == "":
        print(TRED + "You must input a number.")
    elif not i.isdigit():
        print(TRED + "You must input a number.")
    else:
        i = int(i)
        file_list = []
        for j in range(i):
            file = input("Please input file name (Ex: boot.img) : ")
            file_list.append(file)

        generate_device_file(device, file_list)


def delete_device():
    if not check_creds():
        return
    device = input(TYELLOW + "Please input device's codename : ")
    if os.path.exists(config_devices + device + ".json"):
        print(TGREEN + "Device found. Deleting...")
        os.remove(config_devices + device + ".json")
    else:
        print(TRED + "Device not found. Aborting...")
        return


def upload_file(device, filename):
    pattern_rom = r'^Evolution.*\.zip$'
    with open(config_creds, "r") as f:
        data = json.load(f)
        username = data["username"]
        password = data["password"]
        android_version = data["android_version"]
    file_path = out + device + "/" + filename
    if re.match(pattern_rom, filename):
        try:
            if not os.path.exists(file_path):
                print(TRED + f"File {file_path} not found. Aborting...")
            else:
                remote_path = f"{sourceforge_remote_path}/{device}/{android_version}/"
                ssh.connect(hostname=sourceforge_host, username=username, password=password)
                scp = SCPClient(ssh.get_transport())
                print(TYELLOW + f"Sending {file_path} to {remote_path}... Please wait...")
                scp.put(file_path, f"{remote_path}")
                scp.close()
                print(TGREEN + f"Upload successful ! file available at https://sourceforge.net/projects/evolution-x/files/{device}/{android_version}/")

        except Exception as e:
            print(TRED + f"Failed to upload {file_path}: {str(e)}")
    else:
        filename_without_ext = os.path.splitext(filename)[0]
        try:
            if not os.path.exists(file_path):
                print(TRED + f"File {file_path} not found. Aborting...")
            else:
                remote_path = f"{sourceforge_remote_path}/{device}/{android_version}/{filename_without_ext}/"
                ssh.connect(hostname=sourceforge_host, username=username, password=password)
                scp = SCPClient(ssh.get_transport())
                print(TYELLOW + f"Sending {file_path} to {remote_path}... Please wait...")
                scp.put(file_path, f"{remote_path}")
                scp.close()
                print(TGREEN + f"Upload successful ! file available at https://sourceforge.net/projects/evolution-x/files/{device}/{android_version}/{filename_without_ext}/")

        except Exception as e:
            print(TRED + f"Failed to upload {file_path}: {str(e)}")


def retrieve_rom_name(device):
    pattern_rom = r'^Evolution.*\.zip$'
    if not os.path.exists(f"../out/target/product/{device}"):
        print(TRED + f"Device {device} not found. Aborting...")
    else:
        for dir in os.listdir(f"../out/target/product/{device}"):
            if re.match(pattern_rom, dir):
                return dir
    return None

def upload(devices):
    for devices in devices:
        device_without_ext = os.path.splitext(devices)[0]
        rom = retrieve_rom_name(device_without_ext)
        if rom is None:
            print(TRED + f"ROM file for device {device_without_ext} not found. Aborting...")
        else:
            upload_file(device_without_ext, rom)
        with open(config_devices + devices) as f:
            data = json.load(f)
            files = data["files"]
            for file in files:
                upload_file(device_without_ext, file)



def upload_menu():
    if not check_creds():
        return
    else:
        devices_list = input("What devices do you want to upload (please separate with a comma. Ex: polaris,sargo,bonito). Type a for all. : ")
        if devices_list == "a":
            devices = (os.listdir(config_devices))
            upload(devices)
        else:
            devices = devices_list.split(",")
            for device in devices:
                if os.path.exists(config_devices + device + ".json"):
                    with open(config_devices + device + ".json") as f:
                        data = json.load(f)
                        files = data["files"]
                        device_without_ext = os.path.splitext(device)[0]
                        rom = retrieve_rom_name(device_without_ext)
                        if rom is None:
                            print(TRED + f"ROM file for device {device_without_ext} not found. Aborting...")
                        else:
                            upload_file(device_without_ext, rom)
                        for file in files:
                            upload_file(device_without_ext, file)
                else:
                    print(TRED + f"Device {device} not found. Aborting...")


def help():
    print("Available commands :")
    print("---------------------")
    print("  • i/init : Initialize the config folder and create a new config file.")
    print("  • a/add : Add a new device to the upload list.")
    print("  • u/upload : Upload the files for a device.")
    print("  • d/delete : Delete a device from the upload list.")
    print("  • h/help : Display this help message. ")
    print("  • q/quit : Exit the script.")


def main():
    arg = input(TRESET + "Please input a command (h for help) : ")
    if arg == "i" or arg == "init":
        init()
        main()
    if arg == "add" or arg == "a":
        add_device()
        main()
    if arg == "upload" or arg == "u":
        upload_menu()
        main()
    elif arg == "delete" or arg == "d":
        delete_device()
        main()
    elif arg == "h" or arg == "help":
        help()
        main()
    elif arg == "q" or arg == "quit":
        print(TGREEN + "Exiting...")
    else:
        print(TRED + "Unknown command. Please type h for help.")
        main()

main()
