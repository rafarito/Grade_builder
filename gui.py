import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from scheduler import Scheduler
import os
import threading

ctk.set_appearance_mode("Dark")
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
        
        main_font = "Segoe UI"
        
        # LEFT FRAME (Controls)
        self.frame_left = ctk.CTkFrame(self, fg_color="#18181B", corner_radius=15)
        self.frame_left.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(self.frame_left, text="Selecione o Curso:", font=ctk.CTkFont(family=main_font, size=15, weight="bold")).pack(pady=(15, 5))
        
        self.combo_cursos = ctk.CTkComboBox(self.frame_left, values=self.scheduler.cursos, command=self.on_curso_change, font=ctk.CTkFont(family=main_font, size=13), dropdown_font=ctk.CTkFont(family=main_font, size=13))
        self.combo_cursos.pack(padx=15, pady=5, fill="x")
        
        ctk.CTkLabel(self.frame_left, text="Disciplinas Disponíveis:", font=ctk.CTkFont(family=main_font, size=15, weight="bold")).pack(pady=(20, 5))
        
        self.entry_busca = ctk.CTkEntry(self.frame_left, placeholder_text="Buscar por nome...", font=ctk.CTkFont(family=main_font, size=13))
        self.entry_busca.pack(padx=15, pady=(0, 10), fill="x")
        self.entry_busca.bind("<KeyRelease>", self.on_search)
        
        self.lista_disciplinas = ctk.CTkScrollableFrame(self.frame_left, fg_color="transparent")
        self.lista_disciplinas.pack(padx=10, pady=5, fill="both", expand=True)
        
        # RIGHT FRAME (Schedule)
        self.frame_right = ctk.CTkFrame(self, fg_color="#18181B", corner_radius=15)
        self.frame_right.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        
        ctk.CTkLabel(self.frame_right, text="Sua Grade Curricular", font=ctk.CTkFont(family=main_font, size=22, weight="bold"), text_color="#4361EE").pack(pady=(15, 5))
        
        self.grade_container = ctk.CTkScrollableFrame(self.frame_right, fg_color="transparent")
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
        for widget in self.lista_disciplinas.winfo_children():
            widget.destroy()
            
        self.disciplinas_filtradas = []
        
        for d in self.disciplinas_atuais:
            if termo in d.get('nome', '').lower():
                self.disciplinas_filtradas.append(d)
                
        main_font = "Segoe UI"
        for i, d in enumerate(self.disciplinas_filtradas):
            if i >= 150: # Limit to avoid UI lag for extremely long lists
                break
                
            card = ctk.CTkFrame(self.lista_disciplinas, fg_color="#24242B", corner_radius=10)
            card.pack(fill="x", padx=(5, 15), pady=5) # Added padding on right to avoid scrollbar
            
            horarios_str = " | ".join([f"{dia}: {v['ini']}-{v['fim']}" for dia, v in d.get('horarios', {}).items()])
            
            # Truncate long names to avoid layout issues
            nome_display = d['nome']
            if len(nome_display) > 55:
                nome_display = nome_display[:52] + "..."
                
            texto = f"{d['codigo']} - {nome_display}\nTurma: {d['turma']}  •  {horarios_str}"
            
            # Pack button FIRST on the right so it claims its space and doesn't get squished
            btn = ctk.CTkButton(card, text="Adicionar", width=70, font=ctk.CTkFont(family=main_font, size=12, weight="bold"),
                                fg_color="#4361EE", hover_color="#3A0CA3", corner_radius=8,
                                command=lambda disc=d: self.adicionar_disciplina(disc))
            btn.pack(side="right", padx=12, pady=10)
            
            # Pack label SECOND, allowing it to take remaining space
            lbl = ctk.CTkLabel(card, text=texto, justify="left", anchor="w", font=ctk.CTkFont(family=main_font, size=12), text_color="#E0E0E0")
            lbl.pack(side="left", padx=12, pady=10, expand=True, fill="x")
            
    def adicionar_disciplina(self, disciplina):
        if not disciplina:
            return
        
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
        main_font = "Segoe UI"
        
        # Configure column weights
        self.grade_container.grid_columnconfigure(0, weight=0) # Time column
        for i in range(len(dias)):
            self.grade_container.grid_columnconfigure(i + 1, weight=1)
            ctk.CTkLabel(self.grade_container, text=dias[i], font=ctk.CTkFont(family=main_font, size=13, weight="bold"), text_color="#A0A0A0").grid(row=0, column=i+1, padx=5, pady=10)
            
        from time_utils import get_real_time
        
        # Mostrar slots a partir das 15:20 (slot 9) até 22:00 (slot 16)
        slots_to_display = list(range(9, 17))
        
        # Create Time rows
        for r, slot in enumerate(slots_to_display):
            row_idx = r + 1
            ini_t, fim_t = get_real_time(str(slot))
            lbl_time = ctk.CTkLabel(self.grade_container, text=f"{ini_t}\n{fim_t}", font=ctk.CTkFont(family=main_font, size=11, weight="bold"), text_color="#6c757d")
            lbl_time.grid(row=row_idx, column=0, padx=10, pady=5)
            
        grade_por_dia = self.scheduler.get_grade_por_dia()
        
        # List of nice colors for subjects
        colors = ["#4361EE", "#F72585", "#7209B7", "#3A0CA3", "#4CC9F0", "#00B4D8", "#03045E"]
        subject_colors = {}
        
        for i, dia in enumerate(dias):
            aulas = grade_por_dia[dia]
            
            for aula in aulas:
                slot = aula['slot']
                codigo = aula['codigo']
                
                # Assign a consistent color to each subject code
                if codigo not in subject_colors:
                    subject_colors[codigo] = colors[len(subject_colors) % len(colors)]
                bg_color = subject_colors[codigo]
                
                if slot in slots_to_display:
                    row_idx = slots_to_display.index(slot) + 1
                    col_idx = i + 1
                    
                    frame_aula = ctk.CTkFrame(self.grade_container, fg_color=bg_color, corner_radius=8)
                    frame_aula.grid(row=row_idx, column=col_idx, padx=4, pady=4, sticky="nsew")
                    
                    texto = f"{aula['nome'][:18]}...\nT:{aula['turma']}"
                    lbl = ctk.CTkLabel(frame_aula, text=texto, font=ctk.CTkFont(family=main_font, size=11, weight="bold"), text_color="white")
                    lbl.pack(padx=2, pady=(10, 5), expand=True)
                    
                    btn_rm = ctk.CTkButton(frame_aula, text="✕", width=22, height=22, corner_radius=11,
                                           fg_color="transparent", hover_color="#2b2b2b", text_color="white",
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           command=lambda c=codigo, t=aula['turma']: self.remover_disciplina(c, t))
                    btn_rm.place(relx=0.98, rely=0.02, anchor="ne")

if __name__ == "__main__":
    app = App()
    app.mainloop()
