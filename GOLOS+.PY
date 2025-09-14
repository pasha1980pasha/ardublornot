import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import speech_recognition as sr
import threading
import pyperclip
import time
from ahk import AHK

class InstantVoiceNotepad:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 МГНОВЕННЫЙ ГОЛОСОВОЙ БЛОКНОТ")
        self.root.geometry("800x500")
        self.root.configure(bg='#f0f0f0')
        
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.current_text = ""
        self.ahk = AHK()  # AutoHotKey для надежной вставки
        
        # Настройка распознавателя
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Более короткая пауза
        
        # Стиль
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 10), padding=6)
        
        # Заголовок
        title_label = ttk.Label(root, text="🎤 МГНОВЕННАЯ ВСТАВКА ГОЛОСА", 
                               font=('Arial', 14, 'bold'), background='#f0f0f0')
        title_label.pack(pady=10)
        
        # Кнопка записи
        self.record_btn = ttk.Button(root, text="🎤 ГОВОРИТЬ", command=self.toggle_recording,
                                   style='TButton')
        self.record_btn.pack(pady=10)
        
        # Индикатор
        self.status_var = tk.StringVar()
        self.status_var.set("✅ Нажмите 'ГОВОРИТЬ' и говорите прямо в нужное поле!")
        status_label = ttk.Label(root, textvariable=self.status_var, 
                                font=('Arial', 10), background='#f0f0f0')
        status_label.pack(pady=5)
        
        # Текстовое поле для просмотра
        text_label = ttk.Label(root, text="Последний распознанный текст:", 
                              font=('Arial', 9, 'bold'), background='#f0f0f0')
        text_label.pack(pady=(20, 5))
        
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=8, 
                                                  font=('Arial', 10), bg='white')
        self.text_area.pack(pady=5, padx=10)
        
        # Инструкция
        instruction = ttk.Label(root, 
            text="💡 ПЕРЕД НАЖАТИЕМ КНОПКИ:\n1. Поставьте курсор в нужное поле (чат, документ)\n2. Нажмите 'ГОВОРИТЬ'\n3. Говорите - текст появится прямо там!",
            font=('Arial', 8), background='#e8f4f8', justify=tk.LEFT)
        instruction.pack(pady=10, padx=10)
        
        # Проверяем микрофон
        try:
            self.microphone = sr.Microphone(device_index=0)
        except:
            self.microphone = None
            self.record_btn.config(state='disabled')
            self.status_var.set("❌ Микрофон не найден!")
    
    def instant_paste(self, text):
        """Мгновенная вставка текста прямо в активное поле"""
        try:
            # Используем AutoHotKey для надежной вставки
            self.ahk.type(text)
            return True
        except Exception as e:
            try:
                # Резервный вариант
                pyperclip.copy(text)
                time.sleep(0.1)
                self.ahk.send('^v')  # Ctrl+V через AHK
                return True
            except:
                return False
    
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
        self.record_btn.config(text="⏹️ ОСТАНОВИТЬ")
        self.status_var.set("🎤 Запись... ГОВОРИТЕ прямо в нужное поле!")
        
        self.thread = threading.Thread(target=self.continuous_listen)
        self.thread.daemon = True
        self.thread.start()
    
    def stop_listening(self):
        self.listening = False
        self.record_btn.config(text="🎤 ГОВОРИТЬ")
        self.status_var.set("✅ Готово! Нажмите 'ГОВОРИТЬ' для новой записи")
    
    def continuous_listen(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            while self.listening:
                try:
                    # Слушаем короткие фразы для мгновенной вставки
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    text = self.recognizer.recognize_google(audio, language="ru-RU")
                    
                    # Немедленно вставляем туда, где курсор
                    success = self.instant_paste(text + " ")
                    
                    if success:
                        self.root.after(0, self.update_display, text)
                        self.root.after(0, lambda: self.status_var.set(f"✅ Вставлено: {text}"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("❌ Ошибка вставки"))
                        
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set(f"⚠️ Ошибка: {str(e)}"))
                    time.sleep(1)
    
    def update_display(self, text):
        """Только для отображения, не для вставки"""
        self.current_text += text + " "
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.current_text)
        self.text_area.see(tk.END)
    
    def on_closing(self):
        self.listening = False
        time.sleep(0.5)
        self.root.destroy()

if __name__ == "__main__":
    # Устанавливаем AHK если нужно
    try:
        from ahk import AHK
    except ImportError:
        print("Устанавливаем AutoHotKey...")
        import subprocess
        subprocess.check_call(["pip", "install", "ahk"])
        from ahk import AHK
    
    root = tk.Tk()
    app = InstantVoiceNotepad(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
