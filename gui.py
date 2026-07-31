import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from scheduler import Scheduler
import os
import threading

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Gerador de Grade Curricular 2026.2")
        self.geometry("1100x700")
        self.disciplinas_atuais = []
        self.disciplinas_filtradas = []
        self.scheduler = None
        
        json_path = "dados_disciplinas.json"
        
        # Se o JSON não existe, vai precisar parsear o PDF. Mostra a tela de loading.
        if not os.path.exists(json_path):
            self.show_loading()
        else:
            self.scheduler = Scheduler()
            self.build_ui()
            
    def show_loading(self):
        self.loading_frame = ctk.CTkFrame(self)
        self.loading_frame.pack(expand=True, fill="both")
        
        lbl = ctk.CTkLabel(self.loading_frame, 
                           text="Configurando a base de dados...\nLendo o PDF pela primeira vez (isso pode levar alguns segundos).", 
                           font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(expand=True)
        
        # Inicia o parser em uma thread separada para não travar a interface
        threading.Thread(target=self.load_scheduler_bg, daemon=True).start()
        self.check_loading()
        
    def load_scheduler_bg(self):
        self.scheduler = Scheduler()
        
    def check_loading(self):
        if self.scheduler is not None:
            self.loading_frame.destroy()
            self.build_ui()
        else:
            self.after(100, self.check_loading)

    def build_ui(self):
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
        # LEFT FRAME (Controls)
        self.frame_left = ctk.CTkFrame(self)
        self.frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_left, text="Selecione o Curso:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        self.combo_cursos = ctk.CTkComboBox(self.frame_left, values=self.scheduler.cursos, command=self.on_curso_change)
        self.combo_cursos.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(self.frame_left, text="Disciplinas Disponíveis:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        
        self.entry_busca = ctk.CTkEntry(self.frame_left, placeholder_text="Buscar por nome...")
        self.entry_busca.pack(padx=10, pady=(0, 5), fill="x")
        self.entry_busca.bind("<KeyRelease>", self.on_search)
        
        self.lista_disciplinas = tk.Listbox(self.frame_left, height=20, bg="#2b2b2b", fg="white", selectbackground="#1f538d", font=("Arial", 11))
        self.lista_disciplinas.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.btn_add = ctk.CTkButton(self.frame_left, text="Adicionar à Grade", command=self.adicionar_disciplina)
        self.btn_add.pack(padx=10, pady=10, fill="x")
        
        # RIGHT FRAME (Schedule)
        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_right, text="Sua Grade (Segunda a Sábado)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.grade_container = ctk.CTkScrollableFrame(self.frame_right)
        self.grade_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Populate initial courses if available
        if self.scheduler.cursos:
            self.combo_cursos.set(self.scheduler.cursos[0])
            self.on_curso_change(self.scheduler.cursos[0])
            
        self.atualizar_grade()
            
    def on_curso_change(self, curso):
        self.disciplinas_atuais = self.scheduler.get_disciplinas_por_curso(curso)
        
        # Ordenar as disciplinas alfabeticamente pelo nome e depois pela turma
        self.disciplinas_atuais.sort(key=lambda x: (x.get('nome', ''), x.get('turma', '')))
        
        if hasattr(self, 'entry_busca'):
            self.entry_busca.delete(0, 'end')
        self.on_search()
        
    def on_search(self, event=None):
        termo = self.entry_busca.get().lower() if hasattr(self, 'entry_busca') else ""
        self.lista_disciplinas.delete(0, tk.END)
        self.disciplinas_filtradas = []
        
        for d in self.disciplinas_atuais:
            if termo in d.get('nome', '').lower():
                self.disciplinas_filtradas.append(d)
                
        for d in self.disciplinas_filtradas:
            prof = d.get('professor_1', '')
            if len(prof) > 15: prof = prof[:15] + "..."
            horarios_str = " | ".join([f"{dia}: {v['ini']}-{v['fim']}" for dia, v in d.get('horarios', {}).items()])
            display_text = f"{d['codigo']} - {d['nome']} (T:{d['turma']}) [{horarios_str}]"
            self.lista_disciplinas.insert(tk.END, display_text)
            
    def adicionar_disciplina(self):
        selection = self.lista_disciplinas.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma disciplina primeiro.")
            return
            
        idx = selection[0]
        disciplina = self.disciplinas_filtradas[idx]
        
        sucesso, msg = self.scheduler.add_disciplina(disciplina)
        if not sucesso:
            messagebox.showerror("Conflito de Horário", msg)
        else:
            self.atualizar_grade()
            
    def remover_disciplina(self, codigo, turma):
        self.scheduler.remove_disciplina(codigo, turma)
        self.atualizar_grade()
        
    def atualizar_grade(self):
        # Clear current grid
        for widget in self.grade_container.winfo_children():
            widget.destroy()
            
        dias = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB']
        
        # Configure column weights
        self.grade_container.grid_columnconfigure(0, weight=0) # Time column
        for i in range(len(dias)):
            self.grade_container.grid_columnconfigure(i + 1, weight=1)
            ctk.CTkLabel(self.grade_container, text=dias[i], font=ctk.CTkFont(weight="bold")).grid(row=0, column=i+1, padx=5, pady=5)
            
        from time_utils import get_real_time
        
        # Mostrar slots a partir das 15:20 (slot 9) até 22:00 (slot 16)
        slots_to_display = list(range(9, 17))
        
        # Create Time rows
        for r, slot in enumerate(slots_to_display):
            row_idx = r + 1
            ini_t, fim_t = get_real_time(str(slot))
            lbl_time = ctk.CTkLabel(self.grade_container, text=f"{ini_t}\n|\n{fim_t}", font=ctk.CTkFont(size=11, weight="bold"))
            lbl_time.grid(row=row_idx, column=0, padx=10, pady=5)
            
            # Add separator lines (optional, just filling grid with empty frames can also look nice)
            # We'll just let the frames fill the grid
            
        grade_por_dia = self.scheduler.get_grade_por_dia()
        
        for i, dia in enumerate(dias):
            aulas = grade_por_dia[dia]
            
            for aula in aulas:
                slot = aula['slot']
                if slot in slots_to_display:
                    row_idx = slots_to_display.index(slot) + 1
                    col_idx = i + 1
                    
                    frame_aula = ctk.CTkFrame(self.grade_container, fg_color="#33415c", corner_radius=5)
                    frame_aula.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky="nsew")
                    
                    texto = f"{aula['codigo']}\n{aula['nome'][:15]}...\nT:{aula['turma']}"
                    lbl = ctk.CTkLabel(frame_aula, text=texto, font=ctk.CTkFont(size=10))
                    lbl.pack(padx=2, pady=(5, 2), expand=True)
                    
                    btn_rm = ctk.CTkButton(frame_aula, text="X", width=20, height=20, fg_color="red", 
                                           command=lambda c=aula['codigo'], t=aula['turma']: self.remover_disciplina(c, t))
                    btn_rm.pack(pady=(0, 5))

if __name__ == "__main__":
    app = App()
    app.mainloop()
