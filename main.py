import os
import socket
import sys

from PyQt5 import QtWidgets, QtCore


class GetBySocket:
    def __init__(self, port, folder_path, ip=None):
        if ip is None:
            self.ip = self.get_ip()
        else:
            self.ip = ip
        self.port = port
        self.folder_path = folder_path
        sock = socket.socket()
        sock.bind((self.ip, self.port))
        sock.listen(1)
        self.conn, self.addr = sock.accept()
        self.filename = self.get_file_name()
        self.filename = os.path.split(os.path.normpath(self.filename))[1]
        self.conn.close()
        self.conn, self.addr = sock.accept()
        self.get_file()
        self.conn.close()

    @staticmethod
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            IP = s.getsockname()[0]
        except:
            IP = "127.0.0.1"
        finally:
            s.close()
        return IP

    def get_file_name(self):
        full_data = b""
        while True:
            data = self.conn.recv(1024)
            if not data:
                break
            full_data += data
        return full_data.decode("utf-8")

    def get_file(self):
        with open(self.folder_path + '/' + self.filename, 'wb') as fd:
            while True:
                data = self.conn.recv(1024)
                if not data:
                    break
                fd.write(data)


class TransferBySocket:
    def __init__(self, ip, port, filename):
        sock = socket.socket()
        sock.connect((ip, port))
        sock.send(filename.encode("utf-8"))
        sock.close()
        sock = socket.socket()
        sock.connect((ip, port))
        with open(filename, 'rb') as fd:
            while True:
                data = fd.read(1024)
                if not data:
                    break
                sock.send(data)
        sock.close()


class MyWindow():
    def __init__(self):
        self.window = QtWidgets.QWidget()
        self.settings = QtCore.QSettings("dmprod", application="file_server")
        self.init_layouts()
        self.window.show()

    def init_layouts(self):
        layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        self.file_path = QtWidgets.QLineEdit(self.settings.value("file_path"))
        self.folder_path = QtWidgets.QLineEdit(self.settings.value("folder_path"))
        self.ip_text = QtWidgets.QLineEdit()
        label = QtWidgets.QLabel("Your IP: {}".format(GetBySocket.get_ip()))
        button_down = QtWidgets.QPushButton("Download", self.window)
        button_down.clicked.connect(self.on_download)
        button_up = QtWidgets.QPushButton("Upload", self.window)
        button_up.clicked.connect(self.on_upload)
        layout.addLayout(form_layout)
        form_layout.addRow("IP to connect:", self.ip_text)
        form_layout.addRow("File path:", self.file_path)
        form_layout.addRow("Folder path:", self.folder_path)
        layout.addWidget(label)
        layout.addWidget(button_down)
        layout.addWidget(button_up)
        self.window.setLayout(layout)

    def on_download(self):
        GetBySocket(9090, self.folder_path.text(), ip=GetBySocket.get_ip())
        self.settings.setValue('folder_path', self.folder_path.text())

    def on_upload(self):
        TransferBySocket(self.ip_text.text(), 9090, self.file_path.text())
        self.settings.setValue("file_path", self.file_path.text())


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MyWindow()
    sys.exit(app.exec())
