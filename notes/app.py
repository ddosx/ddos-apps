#!/usr/bin/python3

import os

home_directory = os.path.expanduser("~")

import requests, base64, json

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

import sys
import json
import os
import uuid
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QPushButton,
    QWidget, QSplitter, QLabel, QHBoxLayout, QFrame, QScrollArea, 
    QInputDialog, QMenu, QDialog
)

from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from threading import Thread

p = home_directory+'/.notes'

# Функции для работы с заметками
def save_note(note_id, content):
    os.makedirs(p, exist_ok=True)
    with open(f'{p}/{note_id}.json', 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)

def load_note(note_id):
    try:
        with open(f'{p}/{note_id}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'title': 'Untitled', 'content': ''}

def delete_note(note_id):
    try:
        os.remove(f'{p}/{note_id}.json')
    except FileNotFoundError:
        pass

def load_notes():
    notes = []
    if not os.path.exists(p):
        os.makedirs(p)
    for note_filename in os.listdir(p):
        if note_filename.endswith('.json'):
            note_id, _ = os.path.splitext(note_filename)
            notes.append({
                'id':note_id,
                **load_note(note_id)
            })
    return notes

from PyQt5.QtCore import QThread, pyqtSignal

# Custom thread class
class AIThread(QThread):
    result_signal = pyqtSignal(dict)

    def __init__(self, action, note_text, parent=None):
        super().__init__(parent)
        self.action = action
        self.note_text = note_text

    def run(self):
        if self.action == "Summarize":
            result = summarize(self.note_text, self.action)
        elif self.action == "Auto-title":
            result = autotitle(self.note_text, self.action)
        else:  # Auto-format
            result = autoformat(self.note_text, self.action)
        self.result_signal.emit(result)

# Класс для виджета заметки
class NoteWidget(QFrame):
    def __init__(self, note_id, title, parent):
        super().__init__(parent)
        self.note_id = note_id
        self.parent = parent  # Сохраняем ссылку на класс NotesApp
        self.title_label = QLabel(title)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        self.title_label.setWordWrap(True)

        rename_button = QPushButton('✏️')
        delete_button = QPushButton('🗑')

        rename_button.clicked.connect(self.renameNote)
        delete_button.clicked.connect(self.deleteNote)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(rename_button)
        layout.addWidget(delete_button)

        self.setLayout(layout)

        self.setStyleSheet("""
        QPushButton { border: none; }
        NoteWidget { border: 1px solid grey; border-radius: 10px; padding: 7px; }
        NoteWidget:hover { border: 1px solid lightgrey; }
        """)
        self.setFixedHeight(50)

        self.setMouseTracking(True)

    def renameNote(self):
        new_title, ok = QInputDialog.getText(self, 'Rename note', 'Enter new note title:', text=self.title_label.text())
        if ok and new_title:
            self.title_label.setText(new_title)
            self.parent.noteUpdated(self.note_id, new_title, None)

    def deleteNote(self):
        self.parent.noteDeleted(self.note_id)

    def mousePressEvent(self, event):
        self.parent.noteSelected(self.note_id)

# Приложение для заметок
class NotesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.notes = {}
        self.current_note_id = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Заметки')
        self.setGeometry(100, 100, 640, 480)

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Левая панель
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        font = QFont()
        font.setPointSize(13)

        title_label = QLabel('Заметки')
        title_label.setFont(font)

        left_layout.addWidget(title_label)

        new_note_button = QPushButton('+')
        new_note_button.clicked.connect(self.createNote)

        self.notes_list = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()

        # Добавляем vertical layout в scroll_widget и добавляем растягивающий элемент (stretch)
        # в конец, чтобы заметки прилипали к верху
        notes_list_container = QVBoxLayout(scroll_widget)
        notes_list_container.addLayout(self.notes_list)
        notes_list_container.addStretch()

        scroll.setWidget(scroll_widget)

        left_layout.addWidget(new_note_button)
        left_layout.addWidget(scroll)

        splitter.addWidget(left_panel)
       
        # Правая панель изменен с добавлением контекстного меню
        self.note_editor = QTextEdit()
        self.note_editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.note_editor.customContextMenuRequested.connect(self.openEditorContextMenu)
        self.note_editor.textChanged.connect(self.contentChanged)
        self.note_editor.setReadOnly(True)
        splitter.addWidget(self.note_editor)

        self.loadNotes()
        self.show()

    def openEditorContextMenu(self, position):
        context_menu = QMenu(self)
        
        # Добавляем стандартные действия
        undo_action = context_menu.addAction("Undo")
        redo_action = context_menu.addAction("Redo")
        context_menu.addSeparator()
        cut_action = context_menu.addAction("Cut")
        copy_action = context_menu.addAction("Copy")
        paste_action = context_menu.addAction("Paste")
        delete_action = context_menu.addAction("Delete")
        context_menu.addSeparator()
        select_all_action = context_menu.addAction("Select All")
        context_menu.addSeparator()
        
        # Добавляем пользовательские действия
        summarize_action = context_menu.addAction("Summarize")
        autotitle_action = context_menu.addAction("Auto-title")
        autoformat_action = context_menu.addAction("Auto-format")
        
        # Выполняем выбранное действие
        action = context_menu.exec_(self.note_editor.mapToGlobal(position))

        if action == undo_action:
            self.note_editor.undo()
        elif action == redo_action:
            self.note_editor.redo()
        elif action == cut_action:
            self.note_editor.cut()
        elif action == copy_action:
            self.note_editor.copy()
        elif action == paste_action:
            self.note_editor.paste()
        elif action == delete_action:
            self.note_editor.textCursor().removeSelectedText()
        elif action == select_all_action:
            self.note_editor.selectAll()
        elif action in [summarize_action, autotitle_action, autoformat_action]:
            self.processAIAction(action)

    def showWaitDialog(self):
        self.wait_dialog = QProgressDialog("Processing, please wait...", None, 0, 0, self)
        self.wait_dialog.setCancelButton(None)
        self.wait_dialog.setModal(True)
        self.wait_dialog.show()

    # def processAIAction(self, action):
    #     note_text = self.note_editor.toPlainText()

    #     self.showWaitDialog()

    #     if action.text() == "Summarize":
    #         result = summarize(note_text)
    #     elif action.text() == "Auto-title":
    #         result = autotitle(note_text)
    #     else:  # Auto-format
    #         result = autoformat(note_text)

    #     self.wait_dialog.accept()

    #     if result['status'] == 200:
    #         self.showAIModal(result, action.text())
    #     elif result['status'] == 500:
    #         QMessageBox.critical(self, "Error", f"An error occurred: {result['error']}")
    #     elif result['status'] == 429:
    #         QMessageBox.warning(self, "Warning", "Rate limit exceeded. Try again later.")

    # Функция обратного вызова для выполнения асинхронной задачи
    def run_ai_function(self, ai_action, note_text, callback):
        try:
            if ai_action == "Summarize":
                result = summarize(note_text, ai_action)
            elif ai_action == "Auto-title":
                result = autotitle(note_text, ai_action)
            else:  # Auto-format
                result = autoformat(note_text, ai_action)
            # Вызываем callback функцию в главном потоке
            self.wait_dialog.accept()
            callback(result)
        except Exception as e:
            self.wait_dialog.accept()
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")


    def processAIAction(self, action):
        note_text = self.note_editor.toPlainText()
        self.showWaitDialog()
        self.ai_thread = AIThread(action.text(), note_text)
        self.ai_thread.result_signal.connect(self.onAIActionComplete)
        self.ai_thread.finished.connect(self.wait_dialog.accept)  # To close the dialog once thread finishes
        self.ai_thread.start()

    def onAIActionComplete(self, result):
        action_name = result['action_name']
        if result['status'] == 200:
            self.showAIModal(result, action_name)  # Pass the action_name to this method
        elif result['status'] == 500:
            QMessageBox.critical(self, "Error", f"An error occurred: {result['error']}")
        elif result['status'] == 429:
            QMessageBox.warning(self, "Warning", "Rate limit exceeded. Try again later.")

    def showAIModal(self, ai_result, action_type):
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle(action_type)

        # Создаем layout для содержимого диалога
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setPlainText(ai_result.get('summary') or ai_result.get('title') or ai_result.get('result'))
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        # Кнопки для подтверждения или отмены изменений
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        
        # Связываем кнопки с слотами
        save_button.clicked.connect(lambda: self.applyAIResult(ai_result))
        cancel_button.clicked.connect(lambda: self.dialog.reject())
        
        layout.addLayout(buttons_layout)
        self.dialog.setLayout(layout)
        self.dialog.exec_()

    def applyAIResult(self, ai_result):
        if 'summary' in ai_result:
            self.note_editor.setPlainText(ai_result['summary'])
        elif 'title' in ai_result:
            self.noteUpdated(self.current_note_id, ai_result['title'], None)
        elif 'result' in ai_result:
            self.note_editor.setPlainText(ai_result['result'])
        self.dialog.accept()
        
    def loadNotes(self):
        for note in load_notes():
            self.addNoteWidget(note['id'], note['title'])

    def addNoteWidget(self, note_id, title):
        note_widget = NoteWidget(note_id, title, self)
        self.notes[note_id] = note_widget
        # Добавляем виджеты заметок по порядку наверх.
        self.notes_list.insertWidget(self.notes_list.count() - 1, note_widget)

    def createNote(self):
        note_id = str(uuid.uuid4())
        self.addNoteWidget(note_id, 'Untitled')
        self.noteSelected(note_id)

    def noteSelected(self, note_id):
        self.note_editor.setReadOnly(False)
        if self.current_note_id != note_id:
            self.current_note_id = note_id
            note_data = load_note(note_id)
            self.note_editor.setPlainText(note_data.get('content', ''))

    def noteUpdated(self, note_id, title, content):
        if title is not None:
            note_data = load_note(note_id)
            note_data['title'] = title
            save_note(note_id, note_data)
            if note_id == self.current_note_id:
                self.notes[note_id].title_label.setText(title)
        elif content is not None:
            save_note(self.current_note_id, {'title': self.notes[note_id].title_label.text(), 'content': content})

    def noteDeleted(self, note_id):
        if note_id in self.notes:
            self.notes[note_id].deleteLater()
            delete_note(note_id)
            del self.notes[note_id]
            # Если текущая заметка была удалена, очистим редактор.
            if self.current_note_id == note_id:
                self.current_note_id = None
                self.note_editor.clear()

    def contentChanged(self):
        # Сохраняем изменения в текущей заметке
        if self.current_note_id is not None:
            current_content = self.note_editor.toPlainText()
            self.noteUpdated(self.current_note_id, None, current_content)

    def closeEvent(self, event):
        # Переопределяем событие закрытия окна, чтобы сохранить текущую заметку
        if self.current_note_id is not None:
            current_content = self.note_editor.toPlainText()
            self.noteUpdated(self.current_note_id, None, current_content)
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    ex = NotesApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
