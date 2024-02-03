#!/usr/bin/python3

import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication, QTextEdit, QAction,
                             QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel,
                             QMenu)
from PyQt5.QtGui import QKeySequence
# from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QThread, pyqtSignal, Qt


import requests, base64, json

import sys

p = None
if len(sys.argv) != 1:
    p = sys.argv[1]

LANG = 'russian'
api_url = 'https://notes.ddosxd.ru'

def send_to_server(endpoint, data):
    encoded_data = base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
    response = requests.post(f'{api_url}/{endpoint}', json={'data': encoded_data})
    if response.status_code == 200:
        decoded_data = base64.b64decode(response.json()['data']).decode('utf-8')
        return json.loads(decoded_data)
    else:
        return {'status': 500, 'message': 'Failed to communicate with server'}

def api_req(messages, ponos=''):
    return send_to_server('ponos', {
        'messages':messages
    })

def summarize(text, ai_action):

    print('[+] Summarizing')

    x = api_req([{
        'role':'user',
        'content':f'Hi, summarize this note pls.Reply in {LANG} language. Also add basic formatting to this note (like \\n)\n{text}\n\nAssistant: Here"s a summary: '
    }])

    print('[+] Summarized')
    print('--------')
    print(x)
    print('--------')

    if x['status'] == 200:
        return {
            'status': 200,
            'summary':x['reply'].strip(),
            'action_name':ai_action
        }
    return {
        'status':x['status'],
        'error':'Internal server error',
        'action_name':ai_action
    }

def autotitle(text, ai_action):
    print('[+] Generating title...')

    x = api_req([{
        'role':'user',
        'content':f'Hi, generate title (about 2-3 words) for this note pls. Reply in {LANG} language\n{text}\n\nAssistant: Here"s a title for note: '
    }])

    print('[+] Title: ', x)

    if x['status'] == 200:
        return {
            'status': 200,
            'title':x['reply'].strip(),
            'action_name':ai_action
        }
    return {
        'status':x['status'],
        'error':'Internal server error',
        'action_name':ai_action
    }

def autoformat(text, ai_action):
    print('[+] Formatting')

    x = api_req([{
        'role':'user',
        'content':f'Hi, restore formatting in note pls. Reply in {LANG} language.\n{text}\n\nAssistant: Here"s a this text with restored formatting: '
    }])

    print('[+] Formatted')
    print('--------')
    print(x)
    print('--------')

    if x['status'] == 200:
        return {
            'status': 200,
            'result':x['reply'].strip(),
            'action_name':ai_action
        }
    return {
        'status':x['status'],
        'action_name':ai_action,
        'error':'Internal server error',
    }


def generate(text, ai_action, x):
    print(text)
    x = api_req([{
        'role':'user',
        'content':text
    }])

    print('[+] Generated')
    print('--------')
    print(x)
    print('--------')

    if x['status'] == 200:
        return {
            'status': 200,
            'generated_text':x['reply'].strip(),
            'action_name':ai_action
        }
    return {
        'status':x['status'],
        'error':'Internal server error',
        'action_name':ai_action
    }


def change_tone(text, tone, ai_action):
    print('[+] Changing tone...')

    x = api_req([{
        'role':'user',
        'content':f'Hi, change tone in this text to {tone}:\n{text}\n\nAssistant: Here"s text with changed tone:\n'
    }])

    print('[+] Changed')
    print('--------')
    print(x)
    print('--------')

    if x['status'] == 200:
        return {
            'status': 200,
            'result':x['reply'].strip(),
            'action_name':ai_action
        }
    return {
        'status':x['status'],
        'error':'Internal server error',
        'action_name':ai_action
    }

class AIThread(QThread):
    requestCompleted = pyqtSignal(object)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        result = self.func(*self.args)
        self.requestCompleted.emit(result)

class WaitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Пожалуйста, подождите')
        layout = QVBoxLayout()
        self.label = QLabel("Обработка запроса. Пожалуйста, подождите...")
        layout.addWidget(self.label)
        self.setLayout(layout)

class Notepad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_filename = None
        self.initUI()

    def initUI(self):
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.setWindowTitle('write')
        self.setGeometry(300, 300, 640, 480)
        self.createActions()
        self.createMenus()

        if p != None:
            with open(p, 'r', encoding='utf-8') as file:
                self.textEdit.setText(file.read())
            self.current_filename = p


    def createActions(self):
        self.newAct = QAction('Новый', self)
        self.newAct.setShortcut(QKeySequence.New)
        self.newAct.triggered.connect(self.newFile)

        self.openAct = QAction('Открыть...', self)
        self.openAct.setShortcut(QKeySequence.Open)
        self.openAct.triggered.connect(self.openFile)

        self.saveAct = QAction('Сохранить', self)
        self.saveAct.setShortcut(QKeySequence.Save)
        self.saveAct.triggered.connect(self.saveFile)

        self.exitAct = QAction('Выход', self)
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.triggered.connect(self.close)

        self.summarizeAct = QAction('Суммаризировать', self)
        self.summarizeAct.setShortcut('Ctrl+M')
        self.summarizeAct.triggered.connect(lambda: self.runAIAction(summarize))

        self.changeToneMenu = QMenu('Изменить Тон', self)
        self.changeToneSubActions = {
            'Официальный': ('Официальный',),
            'Неформальный': ('Неформальный',),
            'Дружелюбный': ('Дружелюбный',),
            'Агрессивный': ('Агрессивный',)
        }
        for toneName, args in self.changeToneSubActions.items():
            action = QAction(toneName, self)
            action.triggered.connect(lambda checked, a=args: self.runAIAction(change_tone, *a))
            self.changeToneMenu.addAction(action)

        self.autoformatAct = QAction('Автоформат', self)
        self.autoformatAct.setShortcut('Ctrl+Shift+F')
        self.autoformatAct.triggered.connect(lambda: self.runAIAction(autoformat))

        self.autoformatAct = QAction('Автоформат', self)
        self.autoformatAct.setShortcut('Ctrl+Shift+F')
        self.autoformatAct.triggered.connect(lambda: self.runAIAction(autoformat))

        self.generateAct = QAction('Сгенерировать', self)
        self.generateAct.triggered.connect(self.onGenerate)

    def createMenus(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&Файл')
        fileMenu.addAction(self.newAct)
        fileMenu.addAction(self.openAct)
        fileMenu.addAction(self.saveAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAct)

        aiMenu = menubar.addMenu('&ИИ')
        aiMenu.addAction(self.summarizeAct)
        aiMenu.addMenu(self.changeToneMenu)
        aiMenu.addAction(self.autoformatAct)
        aiMenu.addAction(self.generateAct)

    def newFile(self):
        self.textEdit.clear()
        self.current_filename = None

    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Открыть файл', '', 'Текстовые файлы (*.txt);;Все файлы (*)')
        if filename:
            with open(filename, 'r', encoding='utf-8') as file:
                self.textEdit.setText(file.read())
            self.current_filename = filename

    def saveFile(self):
        if self.current_filename is None:
            self.current_filename, _ = QFileDialog.getSaveFileName(self, 'Сохранить файл', '', 'Текстовые файлы (*.txt);;Все файлы (*)')
        
        if self.current_filename:
            with open(self.current_filename, 'w', encoding='utf-8') as file:
                text = self.textEdit.toPlainText()
                file.write(text)
                # Обновление заголовка окна после сохранения файла
                self.setWindowTitle(self.current_filename + " - write")

    def onGenerate(self):
        selected_text = self.textEdit.textCursor().selectedText()
        if not selected_text.strip():
            QMessageBox.information(self, 'Информация', 'Нет выделенного текста для обработки.')
            return
        self.runAIAction(generate, selected_text)

    def runAIAction(self, ai_func, *args):
        text = self.textEdit.toPlainText()
        if not text.strip():
            QMessageBox.information(self, 'Информация', 'Нет текста для обработки.')
            return

        args = (text, *args, ai_func.__name__)
        self.ai_thread = AIThread(ai_func, *args)

        self.wait_dialog = WaitDialog(self)
        self.wait_dialog.show()

        self.ai_thread.requestCompleted.connect(self.onAIRequestCompleted)
        self.ai_thread.start()

    def onAIRequestCompleted(self, result):
        self.wait_dialog.close()

        if result['status'] == 200:
            prompt = QMessageBox(self)
            prompt.setWindowTitle('Подтверждение изменений')
            prompt.setText('Применить изменения?')
            prompt.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            prompt.setDefaultButton(QMessageBox.Yes)
            prompt.setDetailedText(result.get('summary') or result.get('result') or result.get('generated_text'))

            if prompt.exec_() == QMessageBox.Yes:
                if 'summary' in result:
                    self.textEdit.setText(result['summary'])
                elif 'result' in result:
                    self.textEdit.setText(result['result'])
                elif 'generated_text' in result:
                    self.insertGeneratedText(result['generated_text'])
        else:
            QMessageBox.critical(self, 'Ошибка', result.get('error', 'Неизвестная ошибка'))

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Сообщение',
                                     "Вы хотите сохранить файл перед выходом?",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.saveFile()
            event.accept()
        elif reply == QMessageBox.Cancel:
            event.ignore()
        else:
            event.accept()

        # Метод для добавления заголовка
    def setWindowTitleOnModified(self):
        if not self.current_filename:
            self.setWindowTitle("*Безымянный - Простой Блокнот с ИИ Функциями")
        else:
            self.setWindowTitle("*" + self.current_filename + " - Простой Блокнот с ИИ Функциями")

    def insertGeneratedText(self, generated_text):
        cursor = self.textEdit.textCursor()
        cursor.insertText(generated_text)

def main():
    app = QApplication(sys.argv)
    notepad = Notepad()
    notepad.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
