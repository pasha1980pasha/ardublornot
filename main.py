import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import speech_recognition as sr
import threading
import pyperclip
import time
import pyautogui
import keyboard
from ahk import AHK

class SmartInstantVoiceNotepad:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 АРДУ БЛОКНОТ")
        self.root.geometry("900x650")
        self.root.configure(bg='#2c3e50')  # Темный фон для современного вида
        
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.current_text = ""
        
        # Инициализируем AHK для мгновенной вставки
        self.ahk = AHK()
        
        # Регистрируем ГЛОБАЛЬНУЮ горячую клавишу F12
        try:
            keyboard.add_hotkey('f12', self.paste_text_global)
            print("✅ Глобальная клавиша F12 зарегистрирована!")
        except Exception as e:
            print(f"❌ Ошибка регистрации F12: {e}")
            messagebox.showwarning("Предупреждение", f"Не удалось зарегистрировать F12: {str(e)}")
        
        # Настройка распознавателя
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0  # Баланс между скоростью и точностью
        
        # Стили для разноцветных кнопок
        style = ttk.Style()
        style.configure('Start.TButton', font=('Arial', 10, 'bold'), padding=8, background='#e74c3c', foreground='white')
        style.configure('Clear.TButton', font=('Arial', 10, 'bold'), padding=8, background='#f39c12', foreground='white')
        style.configure('Copy.TButton', font=('Arial', 10, 'bold'), padding=8, background='#27ae60', foreground='white')
        style.configure('Fix.TButton', font=('Arial', 10, 'bold'), padding=8, background='#9b59b6', foreground='white')
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), background='#2c3e50', foreground='white')
        style.configure('TFrame', background='#2c3e50')
        style.configure('TLabel', background='#2c3e50', foreground='white')
        
        # Главный контейнер
        main_container = ttk.Frame(root, style='TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        title_label = ttk.Label(main_container, text="🎤 АРДУ БЛОКНОТ", style='Title.TLabel')
        title_label.pack(pady=20)
        
        # Фрейм для кнопок
        button_frame = ttk.Frame(main_container, style='TFrame')
        button_frame.pack(pady=15)
        
        # Кнопки с разными цветами
        self.start_btn = ttk.Button(button_frame, text="🎤 Начать запись", command=self.toggle_recording, style='Start.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=8)
        
        self.clear_btn = ttk.Button(button_frame, text="🧹 Очистить", command=self.clear_text, style='Clear.TButton')
        self.clear_btn.pack(side=tk.LEFT, padx=8)
        
        self.copy_btn = ttk.Button(button_frame, text="📋 Скопировать", command=self.copy_to_clipboard, style='Copy.TButton')
        self.copy_btn.pack(side=tk.LEFT, padx=8)
        
        self.fix_btn = ttk.Button(button_frame, text="✨ Исправить", command=self.auto_correct, style='Fix.TButton')
        self.fix_btn.pack(side=tk.LEFT, padx=8)
        
        # Индикатор записи
        self.record_indicator = ttk.Label(main_container, text="🔴 НЕ ЗАПИСЫВАЕТ", 
                                        font=('Arial', 12, 'bold'), foreground='red')
        self.record_indicator.pack(pady=10)
        
        # Метка для текста
        text_label = ttk.Label(main_container, text="Распознанный текст:", 
                             font=('Arial', 11, 'bold'), foreground='#ecf0f1')
        text_label.pack(pady=(15, 5), anchor=tk.W)
        
        # Текстовое поле с современным стилем
        self.text_area = scrolledtext.ScrolledText(main_container, wrap=tk.WORD, width=100, height=18, 
                                                  font=('Arial', 11), bg='#34495e', fg='#ecf0f1', 
                                                  relief=tk.FLAT, bd=2, insertbackground='white')
        self.text_area.pack(pady=5, fill=tk.BOTH, expand=True)
        self.text_area.insert(tk.END, "Здесь появится текст...\n\n")
        
        # Инструкция в стильной рамке
        instruction_frame = ttk.Frame(main_container, style='TFrame')
        instruction_frame.pack(pady=20, fill=tk.X)
        
        instruction_text = """💡 КАК ИСПОЛЬЗОВАТЬ:
1. Поставьте курсор в нужное поле (чат, Word, Excel, браузер).
2. Нажмите 'Начать запись' — начните говорить.
3. 💥 Текст мгновенно вставится туда, где курсор!
4. Если вставка не сработала — используйте комбинацию Ctrl+V.
5. Используйте 'Исправить' для авто-пунктуации и 'Очистить' для сброса."""

        instruction = ttk.Label(instruction_frame, text=instruction_text, font=('Arial', 10), 
                               background='#34495e', foreground='#bdc3c7', wraplength=850, 
                               justify=tk.LEFT, padding=15)
        instruction.pack(fill=tk.X)
        
        # Индикатор состояния (внизу)
        self.status_var = tk.StringVar()
        self.status_var.set("✅ Готов к работе! Нажмите 'Начать запись'")
        status_bar = ttk.Label(main_container, textvariable=self.status_var, relief=tk.SUNKEN, 
                              anchor=tk.W, background='#34495e', foreground='#ecf0f1')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Проверяем микрофон
        try:
            self.microphone = sr.Microphone(device_index=0)
            mic_list = sr.Microphone.list_microphone_names()
            if mic_list:
                self.status_var.set(f"✅ Микрофон: {mic_list[0]}")
            else:
                self.microphone = None
                self.start_btn.config(state='disabled')
                self.status_var.set("❌ Микрофон не найден!")
        except Exception as e:
            self.microphone = None
            self.start_btn.config(state='disabled')
            self.status_var.set(f"❌ Ошибка микрофона: {str(e)}")

    def instant_paste(self, text):
        """Мгновенная вставка текста прямо в активное поле через AutoHotKey"""
        try:
            self.ahk.type(text + " ")
            return True
        except Exception as e:
            try:
                # Резервный вариант: Ctrl+V через pyautogui
                pyperclip.copy(text + " ")
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'v')
                return True
            except Exception as e2:
                print(f"Ошибка мгновенной вставки: {e}, {e2}")
                return False

    def paste_text_global(self):
        """Глобальная функция для F12 — работает из любого приложения"""
        if not hasattr(self, 'current_text') or not self.current_text.strip():
            return
        
        try:
            pyperclip.copy(self.current_text.strip())
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            if self.root.winfo_exists():
                self.status_var.set("✅ Текст вставлен!")
        except Exception as e:
            if self.root.winfo_exists():
                self.status_var.set(f"❌ Ошибка вставки: {str(e)}")

    def add_punctuation(self, text):
        """Автоматическая расстановка знаков препинания"""
        text = text.lower().strip()
        
        punctuation_commands = {
            'точка': '.', 'точку': '.', 'точки': '.',
            'запятая': ',', 'запятую': ',', 'запятые': ',',
            'восклицательный знак': '!', 'вопросительный знак': '?',
            'двоеточие': ':', 'тире': ' - ', 'новая строка': '\n',
            'кавычки': '"', 'скобки': '()', 'точка с запятой': ';'
        }
        
        for command, symbol in punctuation_commands.items():
            if command in text:
                return symbol
        
        question_words = {'кто', 'что', 'где', 'когда', 'почему', 'как', 'сколько', 'чей', 'какой'}
        words = text.split()
        
        if len(words) > 0:
            if any(word in question_words for word in words[:2]):
                return '?'
            
            if any(word in {'ого', 'ух', 'ах', 'вау', 'здорово'} for word in words):
                return '!'
            
            if len(words) > 6 and text[-1] not in {'.', '!', '?'}:
                return '.'
        
        return ''

    def auto_correct_text(self, text):
        """Автоматическое исправление распространённых ошибок"""
        corrections = {
            'скопироаноо': 'скопировано',
            'привет': 'привет',
            'какдела': 'как дела',
            'спасибо': 'спасибо',
            'пожалуйста': 'пожалуйста',
            'здравствуйте': 'здравствуйте',
            'извините': 'извините',
            'хорошо': 'хорошо',
            'плохо': 'плохо',
            'нормально': 'нормально',
            'тут': 'тут',
            'здесь': 'здесь',
            'можно': 'можно',
            'нет': 'нет',
            'да': 'да',
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text

    def process_text(self, text):
        """Обработка и улучшение текста"""
        text = text.lower().strip()
        text = self.auto_correct_text(text)
        punctuation = self.add_punctuation(text)
        
        # Удаляем команды пунктуации из текста
        for command in {'точка', 'запятая', 'восклицательный', 'вопросительный', 
                       'двоеточие', 'тире', 'новая строка', 'кавычки', 'скобки', 'точка с запятой'}:
            text = text.replace(command, '')
        
        text = text.strip()
        
        if punctuation:
            if punctuation in {'.', '!', '?', ';', ':'}:
                return text + punctuation + ' '
            elif punctuation == ',':
                return text + punctuation + ' '
            elif punctuation == '\n':
                return text + '\n'
            else:
                return punctuation + text + ' '
        else:
            return text + ' '

    def toggle_recording(self):
        if not self.listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        if self.microphone is None:
            messagebox.showerror("Ошибка", "Микрофон не доступен!")
            return
            
        self.listening = True
        self.start_btn.config(text="⏹️ Остановить запись")
        self.record_indicator.config(text="🟢 ЗАПИСЬ ИДЁТ... ГОВОРИТЕ", foreground='green')
        self.status_var.set("🎤 Запись начата... Говорите естественно!")
        
        self.thread = threading.Thread(target=self.continuous_listen)
        self.thread.daemon = True
        self.thread.start()

    def stop_listening(self):
        self.listening = False
        self.start_btn.config(text="🎤 Начать запись")
        self.record_indicator.config(text="🔴 НЕ ЗАПИСЫВАЕТ", foreground='red')
        self.status_var.set("⏸️ Запись остановлена")

    def continuous_listen(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                    text = self.recognizer.recognize_google(audio, language="ru-RU")
                    
                    processed_text = self.process_text(text)
                    
                    # 🔥 МГНОВЕННАЯ ВСТАВКА — главная фича!
                    if self.instant_paste(processed_text.strip()):
                        self.root.after(0, lambda: self.status_var.set(f"✅ Вставлено: {text}"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("⚠️ Не удалось вставить — используйте Ctrl+V"))
                    
                    # Обновляем отображаемый текст
                    self.root.after(0, self.update_text, processed_text)
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    self.root.after(0, lambda: self.status_var.set("❌ Речь не распознана"))
                    continue
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set(f"⚠️ Ошибка: {str(e)}"))
                    time.sleep(1)

    def update_text(self, text):
        self.current_text += text
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.current_text.capitalize())
        self.copy_to_clipboard()  # Автокопирование
        self.text_area.see(tk.END)

    def auto_correct(self):
        if not self.current_text.strip():
            return
        
        # Добавляем заглавную букву и точку, если нужно
        text = self.current_text.strip()
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        if text and text[-1] not in {'.', '!', '?', ',', ';', ':'}:
            text = text + '.'
        
        self.current_text = text
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.current_text)
        self.copy_to_clipboard()
        self.status_var.set("✨ Текст автоматически исправлен!")

    def clear_text(self):
        self.current_text = ""
        self.text_area.delete(1.0, tk.END)
        pyperclip.copy("")
        self.status_var.set("🧹 Текст очищен")

    def copy_to_clipboard(self):
        if self.current_text.strip():
            pyperclip.copy(self.current_text.strip())
            self.status_var.set("📋 Текст скопирован в буфер обмена!")

    def on_closing(self):
        self.listening = False
        try:
            keyboard.remove_hotkey('f12')
        except:
            pass
        time.sleep(0.5)
        self.root.destroy()


if __name__ == "__main__":
    # Устанавливаем зависимости, если их нет
    dependencies = [
        ("pyautogui", "pyautogui"),
        ("keyboard", "keyboard"),
        ("ahk", "ahk")
    ]
    
    for module_name, import_name in dependencies:
        try:
            __import__(import_name)
        except ImportError:
            print(f"Устанавливаем {module_name}...")
            import subprocess
            subprocess.check_call(["pip", "install", module_name])
    
    # Импортируем после установки
    from ahk import AHK
    
    root = tk.Tk()
    app = SmartInstantVoiceNotepad(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
