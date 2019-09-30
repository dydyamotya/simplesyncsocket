"""
All file must be rewriten in async manner
Cause i heard threading is bad for this works

Also some ideas:
    > Caching zip-files by they hashes
    > Taking different commands
    > Deleting files with very small size or little difference in time
    > Sync with database file
"""

import argparse
import datetime
import json
import logging
import os
import socket
import threading
import zipfile

SIGTTERM = b"\x00\x00\x00\x00"


class Server:
    def __init__(self, folder_to_sync: str, ip: str = "", port: int = 9090, debug=False):
        """Accepts path of folder, which should be synced"""
        self.CLIENTS = {}
        if ip:
            self.ip = ip
        else:
            self.ip = self.get_ip()
            print("Your ip: ", self.ip)
        self.port = port
        self.folder_to_sync = folder_to_sync
        if debug:
            self._init_logger(level=logging.DEBUG)
        else:
            self._init_logger()

    def _init_logger(self, level: int = logging.INFO):
        timestamp = datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
        name = timestamp + ".log"
        log_folder = "./logs/"
        if not os.path.exists(log_folder):
            os.mkdir(log_folder)
        logging.basicConfig(filename=log_folder + name, level=level)

    @staticmethod
    def get_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP

    @staticmethod
    def concat_ff(folder: str, file: str) -> str:
        """Concatenate folder and file paths"""
        if folder.endswith("/") or folder.endswith("\\"):
            return folder + file
        else:
            return folder + '/' + file

    def start_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip, self.port))
        s.listen(10)
        while True:
            try:
                client_sock, addr = s.accept()
            except KeyboardInterrupt:
                break
            else:
                logging.info("Connected to client with addr: {}".format(addr))
                self.CLIENTS[addr] = client_sock
                threading.Thread(target=self._process_client,
                                 args=(client_sock, len(self.CLIENTS),)).start()
        s.close()

    def _process_client(self, client_sock: socket.socket, client_num: int):
        """client_sock: socket accepted from the client"""
        """Program must recieve the list of files from the client,
        decide which filed to send, pack them to archive and send it.
        """
        client_sock.settimeout(5)
        data: bytes = b""
        while True:
            received = client_sock.recv(1024)
            logging.debug("Data got: {}".format(received))
            if not received:
                break
            else:
                data += received
            if data[-4:] == SIGTTERM:
                data = data[:-4]
                break
        existed_files_list = json.loads(data.decode("utf-8"))

        to_send_list = []

        for file in self._get_files_in_folder():
            if file not in existed_files_list:
                to_send_list.append(file)

        zip_name = "send_client{}.zip".format(client_num)
        with zipfile.ZipFile(zip_name, 'w') as zfd:
            for file in to_send_list:
                zfd.write(self.concat_ff(self.folder_to_sync, file), arcname=file)

        with open(zip_name, "rb") as fd:
            while True:
                data = fd.read(1024)
                if not data:
                    break
                client_sock.send(data)
        client_sock.close()

        os.remove(zip_name)

    def _get_files_in_folder(self):
        """Returns iterator(generator)
        Be careful!!
        """
        for file in os.listdir(self.folder_to_sync):
            if not (file.startswith("send") or file.startswith("logs")):
                yield file


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to sync folder", type=str, action="store")
    parser.add_argument("--ip", help="special ip to setup server", type=str, default="", action="store")
    parser.add_argument("-d", "--debug", help="start with debug mode", action='store_true')
    args = parser.parse_args()
    server = Server(args.path, args.ip, debug=args.debug)
    server.start_server()
