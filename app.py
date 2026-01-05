import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item
import os

class PomodoroApp:
    def __init__(self):
        self.work_time = 25 * 60  # 25 minutos em segundos
        self.break_time = 5 * 60   # 5 minutos em segundos
        self.current_time = self.work_time
        self.is_work = True
        self.is_running = False
        self.timer_thread = None
        
        # Criar janela principal (pode ser minimizada)
        self.root = tk.Tk()
        self.root.title("Pomodoro Timer")
        self.root.geometry("300x200")
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        
        # Criar ícone na bandeja
        self.create_tray_icon()
        
        # Interface
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Display do timer
        self.time_label = ttk.Label(main_frame, text="25:00", font=("Arial", 40))
        self.time_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Tempo de Trabalho", font=("Arial", 12))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Iniciar", command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(button_frame, text="Pausar", command=self.pause_timer, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="Resetar", command=self.reset_timer)
        self.reset_button.grid(row=0, column=2, padx=5)
        
        # Configurações
        settings_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(settings_frame, text="Trabalho (min):").grid(row=0, column=0)
        self.work_var = tk.StringVar(value="25")
        work_spin = ttk.Spinbox(settings_frame, from_=1, to=60, textvariable=self.work_var, width=5)
        work_spin.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Descanso (min):").grid(row=0, column=2)
        self.break_var = tk.StringVar(value="5")
        break_spin = ttk.Spinbox(settings_frame, from_=1, to=30, textvariable=self.break_var, width=5)
        break_spin.grid(row=0, column=3, padx=5)
        
        apply_btn = ttk.Button(settings_frame, text="Aplicar", command=self.apply_settings)
        apply_btn.grid(row=0, column=4, padx=10)
        
    def create_tray_icon(self):
        # Criar ícone temporário para a bandeja
        image = Image.new('RGB', (64, 64), color='red')
        
        # Menu da bandeja
        menu = (
            item('Mostrar', self.show_window),
            item('Iniciar', self.start_timer),
            item('Pausar', self.pause_timer),
            item('Resetar', self.reset_timer),
            item('Sair', self.quit_app)
        )
        
        self.icon = pystray.Icon("pomodoro", image, "Pomodoro Timer", menu)
        
        # Iniciar ícone em thread separada
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()
    
    def update_tray_icon(self, color='red'):
        """Atualiza a cor do ícone na bandeja"""
        image = Image.new('RGB', (64, 64), color=color)
        self.icon.icon = image
        self.icon.update_menu()
    
    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def timer_thread_func(self):
        while self.is_running and self.current_time > 0:
            time.sleep(1)
            self.current_time -= 1
            
            # Atualizar interface na thread principal
            self.root.after(0, self.update_display)
            
            # Atualizar cor do ícone baseado no tempo
            if self.current_time <= 60:  # Último minuto
                self.root.after(0, lambda: self.update_tray_icon('orange'))
        
        if self.current_time <= 0:
            self.root.after(0, self.timer_finished)
    
    def update_display(self):
        self.time_label.config(text=self.format_time(self.current_time))
        
        # Atualizar título da janela
        status = "Trabalho" if self.is_work else "Descanso"
        self.root.title(f"Pomodoro - {self.format_time(self.current_time)} - {status}")
        
        # Atualizar status label
        status_text = "Tempo de Trabalho" if self.is_work else "Tempo de Descanso"
        self.status_label.config(text=status_text)
        
        # Atualizar ícone da bandeja
        icon_color = 'red' if self.is_work else 'green'
        self.update_tray_icon(icon_color)
    
    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            
            self.timer_thread = threading.Thread(target=self.timer_thread_func, daemon=True)
            self.timer_thread.start()
    
    def pause_timer(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
    
    def reset_timer(self):
        self.is_running = False
        time.sleep(0.1)  # Dar tempo para a thread parar
        
        if self.is_work:
            self.current_time = self.work_time
        else:
            self.current_time = self.break_time
            
        self.update_display()
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
    
    def apply_settings(self):
        try:
            self.work_time = int(self.work_var.get()) * 60
            self.break_time = int(self.break_var.get()) * 60
            
            if self.is_work:
                self.current_time = self.work_time
            else:
                self.current_time = self.break_time
                
            self.update_display()
            messagebox.showinfo("Sucesso", "Configurações aplicadas!")
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira valores válidos")
    
    def timer_finished(self):
        self.is_running = False
        
        # Alternar entre trabalho e descanso
        self.is_work = not self.is_work
        
        if self.is_work:
            self.current_time = self.work_time
            messagebox.showinfo("Pomodoro", "Tempo de trabalho terminado! Hora de descansar.")
        else:
            self.current_time = self.break_time
            messagebox.showinfo("Pomodoro", "Tempo de descanso terminado! Volte ao trabalho.")
        
        self.update_display()
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        
        # Piscar ícone
        for _ in range(3):
            self.update_tray_icon('yellow')
            time.sleep(0.5)
            self.update_tray_icon('red' if self.is_work else 'green')
            time.sleep(0.5)
    
    def hide_window(self):
        self.root.withdraw()
    
    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def quit_app(self, icon=None, item=None):
        self.is_running = False
        self.icon.stop()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PomodoroApp()
    app.run()