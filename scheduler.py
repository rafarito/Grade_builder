import json
import os
from time_utils import get_slots_range

class Scheduler:
    def __init__(self, json_path="dados_disciplinas.json"):
        self.json_path = json_path
        self.disciplinas = []
        self.cursos = []
        self.grade = [] # list of added subjects

        if not os.path.exists(json_path):
            from pdf_parser import parse_pdf
            
            # Procura pelo primeiro PDF na pasta atual
            pdf_path = None
            for arquivo in os.listdir('.'):
                if arquivo.lower().endswith('.pdf'):
                    pdf_path = arquivo
                    break
                    
            if pdf_path:
                print(f"Arquivo JSON não encontrado. Gerando a partir de {pdf_path}...")
                parse_pdf(pdf_path, json_path)
            else:
                print("Aviso: Nenhum arquivo PDF encontrado na pasta para gerar o JSON.")

        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                self.disciplinas = json.load(f)
            
            # Extract unique courses
            cursos_set = set(d['curso'] for d in self.disciplinas if d['curso'])
            self.cursos = sorted(list(cursos_set))
            
    def get_disciplinas_por_curso(self, curso):
        return [d for d in self.disciplinas if d['curso'] == curso]
        
    def add_disciplina(self, disciplina):
        """
        Adiciona disciplina na grade se não houver choque de horário.
        Retorna (sucesso, mensagem_erro)
        """
        # Checar se a disciplina já está na grade
        for d in self.grade:
            if d['codigo'] == disciplina['codigo'] and d['turma'] == disciplina['turma']:
                return False, "Esta disciplina/turma já está na sua grade."
        
        # Checar choques de horário
        novos_slots = self._extract_slots(disciplina)
        
        for d in self.grade:
            slots_existentes = self._extract_slots(d)
            # intersecção
            for dia, slots in novos_slots.items():
                if dia in slots_existentes:
                    interseccao = set(slots).intersection(set(slots_existentes[dia]))
                    if interseccao:
                        return False, f"Choque de horário na(o) {dia} com a disciplina {d['nome']} ({', '.join(interseccao)})."
                        
        self.grade.append(disciplina)
        return True, ""
        
    def remove_disciplina(self, codigo, turma):
        self.grade = [d for d in self.grade if not (d['codigo'] == codigo and d['turma'] == turma)]
        
    def _extract_slots(self, disciplina):
        """ Retorna dict: { 'SEG': ['11', '12'], 'TER': ['13', '14'] } """
        slots = {}
        for dia, horarios in disciplina.get('horarios', {}).items():
            ini = horarios.get('ini')
            fim = horarios.get('fim')
            if ini and fim:
                slots[dia] = get_slots_range(ini, fim)
        return slots
        
    def get_grade_por_dia(self):
        """ 
        Retorna um dicionário { dia: [lista de dicts com horario real e nome da disc] }
        """
        from time_utils import get_real_time
        dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB']
        grade_dia = {dia: [] for dia in dias_semana}
        
        for d in self.grade:
            for dia, slots in self._extract_slots(d).items():
                if dia in grade_dia:
                    # add each slot
                    for slot in slots:
                        ini_time, fim_time = get_real_time(slot)
                        grade_dia[dia].append({
                            'slot': int(slot),
                            'ini_time': ini_time,
                            'fim_time': fim_time,
                            'nome': d['nome'],
                            'codigo': d['codigo'],
                            'turma': d['turma'],
                            'professores': f"{d.get('professor_1','')} {d.get('professor_2','')}".strip()
                        })
                        
        # Sort by slot inside each day
        for dia in grade_dia:
            grade_dia[dia] = sorted(grade_dia[dia], key=lambda x: x['slot'])
            
        return grade_dia
