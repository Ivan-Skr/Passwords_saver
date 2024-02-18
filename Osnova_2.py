import sqlite3
import sys
from PyQt5 import uic, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QCheckBox, QInputDialog, QLineEdit, QLabel, QHBoxLayout
import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES           # pip install pycryptodome
import shutil
import subprocess


def get_chrome_passwords():
    listt = []
    def get_encryption_key():
        local_state_path = os.path.join(os.environ["USERPROFILE"],
                                        "AppData", "Local", "Google", "Chrome",
                                        "User Data", "Local State")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = f.read()
            local_state = json.loads(local_state)

        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        key = key[5:]
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

    def decrypt_password(password, key):
        try:
            iv = password[3:15]
            password = password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt(password)[:-16].decode()
        except:
            try:
                return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
            except:
                return ""



    key = get_encryption_key()
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "default", "Login Data")
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename)
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("select origin_url, action_url, username_value, password_value from logins order by date_created")
    for row in cursor.fetchall():
        action_url = row[1]
        username = row[2]
        password = decrypt_password(row[3], key)
        if username or password:
            listt.append(['Chrome', action_url, username, password])
        else:
            continue
    cursor.close()
    db.close()
    try:
        os.remove(filename)
    except:
        pass
    return listt




def get_wifi_passwords():
    listt = []
    meta_data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'])
    data = meta_data.decode('utf-8', errors ="backslashreplace")
    data = data.split('\n')
    profiles = []
    data = str(data)
    data = data.split('\\')

    for i in data:
        if ":" in i :
            i = i.split(':')
            profiles.append(i[1][1 : :])
        
    profiles = profiles[1 ::]

    itog = []
    for i in profiles:
        results = subprocess.check_output(f'netsh wlan show profile name="{i}" key = clear')
        results = str(results)
        results = results.split('\\')
        passw = []
        for i in results:
            if ':' in i and '            : ' in i and not '"' in i:
                i = i.split(':')
                passw.append(i[1])
        itog.append(passw)
        passw = 0
    for i in range(len(itog)):
        listt.append(['WI-FI', itog[i][0][1::], itog[i][0][1::], itog[i][2][1::]])
    return listt











class Osnova(QMainWindow, QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("uic_2.ui", self)
        self.setWindowTitle("passwords")
        self.setFixedSize(949, 627)

        
        label = QLabel(self)
        pixmap = QPixmap('wifi.png')
        label.setPixmap(pixmap)
        label.move(280, 93)

        label2 = QLabel(self)
        pixmap2 = QPixmap('chrome.png')
        label2.setPixmap(pixmap2)
        label2.resize(35, 35)
        label2.move(305, 52)



        self.bd = sqlite3.connect("passwords.sqlite")
        self.chrome = False
        self.wifi = False
        self.cleann = False
        self.checkBox.toggled.connect(self.chrome_df)
        self.checkBox_2.toggled.connect(self.wifi_df)
        self.pushButton_99.clicked.connect(self.get_passwords)
        self.pushButton_4.clicked.connect(self.clean)
        self.pushButton_2.clicked.connect(self.add)
        self.pushButton_7.clicked.connect(self.edit)
        self.pushButton_6.clicked.connect(self.delete)
        self.pushButton_5.clicked.connect(self.find_password)



        self.tableWidget.setColumnWidth(0, 100)
        self.tableWidget.setColumnWidth(1, 100)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)
        self.loaddata()
        self.find_password()







    def loaddata(self):
        connection = sqlite3.connect('passwords.sqlite')
        cur = connection.cursor()
        self.tableWidget.clear()

        self.tableWidget.setHorizontalHeaderLabels(['sourse', 'location', 'username', 'password'])
        sqlquaery = "SELECT * FROM passwords"
        a = cur.execute(sqlquaery)
        a = sorted(list(set(a)))

        self.tableWidget.setRowCount(50)
        tablerow = 0
        for row in a:
            self.tableWidget.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(row[0]))
            self.tableWidget.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
            tablerow += 1
        
        cur.execute("DELETE FROM passwords;")
        for row in a:
            cur.execute(f'INSERT INTO passwords (source, location, username, password) values("{row[0]}", "{row[1]}", "{row[2]}", "{row[3]}");')
        connection.commit()
        connection.close()








        
    
    def chrome_df(self):
        sender: QCheckBox = self.sender()
        if sender.isChecked():
            self.chrome = True
        else:
            self.chrome = False

    def wifi_df(self):
        sender: QCheckBox = self.sender()
        if sender.isChecked():
            self.wifi = True
        else:
            self.wifi = False

    def get_passwords(self):
        listt = []
        if self.chrome == True:
            try:
                listt.extend(get_chrome_passwords())
            except Exception:
                None
        if self.wifi == True:
            try:
                listt.extend(get_wifi_passwords())
            except Exception:
                None
        if len(listt) > 0:
            db=sqlite3.connect('passwords.sqlite')
            for _ in range(len(listt)):
                qry=f'INSERT INTO passwords (source, location, username, password) values("{listt[_][0]}", "{listt[_][1]}", "{listt[_][2]}", "{listt[_][3]}");'
                cur=db.cursor()
                cur.execute(qry)
                db.commit()
                db.rollback()
            db.close()
        self.loaddata()


    def find_password(self):
        connection = sqlite3.connect('passwords.sqlite')
        cur = connection.cursor()
        self.tableWidget_2.clear()
        self.tableWidget_2.setHorizontalHeaderLabels(['sourse', 'location', 'username', 'password'])
        sqlquaery = f'SELECT * FROM passwords WHERE location like "%{self.lineEdit_5.text()}%"'
        self.tableWidget_2.setRowCount(50)
        tablerow = 0
        for row in cur.execute(sqlquaery):
            self.tableWidget_2.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(row[0]))
            self.tableWidget_2.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget_2.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget_2.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
            tablerow += 1
        connection.commit()
        connection.close()

    def add(self):
        source, done1 = QInputDialog.getText(self, "source","Source:", QLineEdit.Normal, "")
        location, done1 = QInputDialog.getText(self, "location","Location:", QLineEdit.Normal, "")
        username, done1 = QInputDialog.getText(self, "username","Username:", QLineEdit.Normal, "")
        password, done1 = QInputDialog.getText(self, "password","Password:", QLineEdit.Normal, "")
        connection = sqlite3.connect('passwords.sqlite')
        cur = connection.cursor()
        cur.execute(f'INSERT INTO passwords (source, location, username, password) VALUES ("{source}", "{location}", "{username}", "{password}");')
        connection.commit()
        connection.close()
        self.loaddata()

    def delete(self):
        location, done1 = QInputDialog.getText(self, "location","Location:", QLineEdit.Normal, "")
        connection = sqlite3.connect('passwords.sqlite')
        cur = connection.cursor()
        cur.execute(f'DELETE FROM passwords WHERE location="{location}";')
        connection.commit()
        connection.close()
        self.loaddata()

        


    def clean(self):
        self.connection = sqlite3.connect('passwords.sqlite')
        self.cur = self.connection.cursor()
        sqlquaery = "DELETE from passwords;"
        self.cur.execute(sqlquaery)
        self.connection.commit()
        self.connection.close()
        self.loaddata()
    
    def edit(self):
        self.connection = sqlite3.connect('passwords.sqlite')
        self.cur = self.connection.cursor()
        sqlquaery = f'SELECT * FROM passwords WHERE location="{self.lineEdit.text()}";'
        a = list(self.cur.execute(sqlquaery))[0]

        source, done1 = QInputDialog.getText(self, "source","Source:", QLineEdit.Normal, f"{a[0]}")
        location, done1 = QInputDialog.getText(self, "location","Location:", QLineEdit.Normal, f"{a[1]}")
        username, done1 = QInputDialog.getText(self, "username","Username:", QLineEdit.Normal, f"{a[2]}")
        password, done1 = QInputDialog.getText(self, "password","Password:", QLineEdit.Normal, f"{a[3]}")

        self.cur.execute(f'UPDATE passwords SET source="{source}", location="{location}", username="{username}", password="{password}" WHERE location="{self.lineEdit.text()}";')
        self.connection.commit()
        self.connection.close()
        self.loaddata()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("""
    QWidget {
        background-color: #effafd; 
    }
    QPushButton {
        font-size: 16px;
        background-color: #6ACFC7;
    }
""")
    ex = Osnova()
    ex.show()
    sys.exit(app.exec())