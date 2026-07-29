import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from scheduler import Scheduler

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Gerador de Grade Curricular 2026.2")
        self.geometry("1100x700")
        
        self.scheduler = Scheduler()
        self.disciplinas_atuais = []
        
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
        self.lista_disciplinas.delete(0, tk.END)
        self.disciplinas_atuais = self.scheduler.get_disciplinas_por_curso(curso)
        for d in self.disciplinas_atuais:
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
        disciplina = self.disciplinas_atuais[idx]
        
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
        
        # Create columns
        for i, dia in enumerate(dias):
            self.grade_container.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(self.grade_container, text=dia, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=5, pady=5)
            
        grade_por_dia = self.scheduler.get_grade_por_dia()
        
        for i, dia in enumerate(dias):
            aulas = grade_por_dia[dia]
            row_idx = 1
            for aula in aulas:
                frame_aula = ctk.CTkFrame(self.grade_container, fg_color="#33415c", corner_radius=5)
                frame_aula.grid(row=row_idx, column=i, padx=5, pady=5, sticky="ew")
                
                texto = f"{aula['ini_time']} - {aula['fim_time']}\n{aula['codigo']}\n{aula['nome'][:15]}...\nT:{aula['turma']}"
                lbl = ctk.CTkLabel(frame_aula, text=texto, font=ctk.CTkFont(size=10))
                lbl.pack(padx=2, pady=2)
                
                # Button to remove
                btn_rm = ctk.CTkButton(frame_aula, text="X", width=20, height=20, fg_color="red", 
                                       command=lambda c=aula['codigo'], t=aula['turma']: self.remover_disciplina(c, t))
                btn_rm.pack(pady=2)
                
                row_idx += 1

if __name__ == "__main__":
    app = App()
    app.mainloop()
