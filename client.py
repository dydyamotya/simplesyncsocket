"""
Add these features:
    > Debug mode
"""

import argparse
import io
import json
import os
import socket
import zipfile

SIGTTERM = b"\x00\x00\x00\x00"
BROADCAST_PORT = 44444


class Client:
    def __init__(self, ip: str, folder_to_path: str, port: int = 9090, debug=False):
        if ip == "search":
            self.ip = self.broadcast_retrieve()
        else:
            self.ip = ip
        self.folder_to_path = folder_to_path
        self.port = port
        self.debug = debug

    @staticmethod
    def concat_ff(folder: str, file: str) -> str:
        """Concatenate folder and file paths"""
        if folder.endswith("/") or folder.endswith("\\"):
            return folder + file
        else:
            return folder + '/' + file

    @staticmethod
    def broadcast_retrieve():
        s_broad = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_broad.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s_broad.sendto("search".encode("utf-8"), ("<broadcast>", BROADCAST_PORT))
        data, addr = s_broad.recvfrom(1024)
        if data.decode("utf-8") == "search_request":
            return addr[0]

    def start_download_thread(self):
        sock = socket.socket()
        sock.connect((self.ip, self.port))
        data_to_send_io = io.BytesIO(json.dumps(os.listdir(self.folder_to_path)).encode("utf-8"))
        while True:
            to_send = data_to_send_io.read(1024)
            if not to_send:
                sock.send(SIGTTERM)
                break
            else:
                sock.send(to_send)

        archive_path = self.concat_ff(self.folder_to_path, 'downloaded.zip')
        with open(archive_path, 'wb') as fd:
            while True:
                to_read: bytes = sock.recv(1024)
                if not to_read:
                    break
                fd.write(to_read)

        archive = zipfile.ZipFile(archive_path, 'r')
        archive.extractall(self.folder_to_path)
        archive.close()

        os.remove(archive_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", type=str, help="ip to connect")
    parser.add_argument("path", type=str, help="folder to sync")
    parser.add_argument("-d", "--debug", help="debug mode", action="store_true")
    parser.add_argument("--port", type=int, help='port of connection', default=9090)
    args = parser.parse_args()
    client = Client(args.ip, args.path, port=args.port, debug=args.debug)
    client.start_download_thread()
