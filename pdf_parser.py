import pdfplumber
import json
import re
import os

def parse_pdf(pdf_path, output_json):
    all_data = []
    
    current_course = "Desconhecido"
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract words with bounding boxes
            words = page.extract_words()
            
            # Find all course headers on this page and their Y coordinates (top)
            # Pattern: look for "MATRÍCULA" and then capture the rest of the line or next line if it's the course
            course_headers = []
            
            # Since pdfplumber groups words, it might be easier to use page.extract_text() with layout=True, 
            # or just look at lines. Let's do a simple heuristic:
            # The green bar with the course name has a specific position or follows the OBS line.
            
            # Let's extract lines using bounding boxes
            lines = {}
            for w in words:
                # group by approximate vertical position
                top_rounded = round(w['top'], 1)
                found = False
                for t in lines:
                    if abs(t - top_rounded) < 4:
                        lines[t].append(w)
                        found = True
                        break
                if not found:
                    lines[top_rounded] = [w]
                    
            sorted_lines = sorted(lines.items(), key=lambda x: x[0])
            
            for i, (y_pos, line_words) in enumerate(sorted_lines):
                line_words = sorted(line_words, key=lambda x: x['x0'])
                text = " ".join([w['text'] for w in line_words])
                
                # Check if this line is the course name (e.g. ENGENHARIA ELÉTRICA)
                # Usually it follows the "GUIA DE MATRÍCULA" line, or is in the same line
                if "GUIA DE MATR" in text.upper():
                    # The course name could be in the same line after MATRÍCULA
                    idx = text.upper().find("MATR") + len("MATRÍCULA")
                    c = text[idx:].strip()
                    if c:
                        if c.upper().startswith("CURSO:"):
                            c = c[6:].strip()
                        course_headers.append({'y': y_pos, 'course': c})
                    else:
                        # might be on the next line
                        if i + 1 < len(sorted_lines):
                            next_line_words = sorted(sorted_lines[i+1][1], key=lambda x: x['x0'])
                            next_text = " ".join([w['text'] for w in next_line_words]).strip()
                            if next_text and next_text.upper() != "CÓD DISCIPLINA":
                                c = next_text
                                if c.upper().startswith("CURSO:"):
                                    c = c[6:].strip()
                                course_headers.append({'y': sorted_lines[i+1][0], 'course': c})
            
            # Extract tables
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines"
            }
            # extract_table doesn't give us bounding boxes of rows directly, 
            # but we can use extract_words to map row text to Y position, or use cell bboxes.
            
            tables = page.find_tables(table_settings)
            
            for table in tables:
                extracted_table = table.extract()
                
                for r_idx, row in enumerate(extracted_table):
                    if not row: continue
                    # Get Y coordinate of the first cell of the row
                    try:
                        row_top = table.rows[r_idx].bbox[1]
                    except:
                        row_top = 0
                        
                    # Determine course for this row
                    # Use the last course header that is ABOVE this row (y < row_top)
                    course_for_row = current_course
                    for ch in course_headers:
                        if ch['y'] < row_top:
                            course_for_row = ch['course']
                            
                    # Update global current_course so it carries over to next page
                    current_course = course_for_row
                    
                    row_strs = [str(c).replace('\n', ' ').strip() if c else '' for c in row]
                    
                    # Ensure it's a data row (has code like ABC123 or just len > 2 and starts with 3 letters)
                    cod = row_strs[0]
                    if not re.match(r'^[A-Z]{3,4}\d{1,3}[A-Z]?$', cod) and not re.match(r'^[A-Z]{3,4}\s\d{1,3}$', cod):
                        # P01 etc might be just classes, let's just check if it's not empty and not 'Cód'
                        if not cod or cod.upper() == 'CÓD' or 'PROFESSOR' in cod.upper():
                            continue
                            
                    # Sometimes headers are empty, we just map by fixed indices
                    # 0:Cód 1:Disciplina 2:TURMA 3:SEG_INI 4:SEG_FIM 5:TER_INI 6:TER_FIM 7:QUA_INI 8:QUA_FIM 9:QUI_INI 10:QUI_FIM 11:SEX_INI 12:SEX_FIM 13:SAB_INI 14:SAB_FIM 15:VAGAS 16:PROF1 17:PROF2
                    
                    if len(row_strs) < 18:
                        row_strs.extend([''] * (18 - len(row_strs)))
                        
                    disciplina = row_strs[1]
                    turma = row_strs[2]
                    vagas = row_strs[15]
                    prof1 = row_strs[16]
                    prof2 = row_strs[17] if len(row_strs) > 17 else ""
                    
                    horarios = {}
                    dias = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB']
                    for d_idx, dia in enumerate(dias):
                        ini = row_strs[3 + (d_idx * 2)]
                        fim = row_strs[4 + (d_idx * 2)]
                        if ini and fim:
                            horarios[dia] = {'ini': ini, 'fim': fim}
                            
                    if not cod and not disciplina:
                        continue
                        
                    subject = {
                        'curso': course_for_row,
                        'codigo': cod,
                        'nome': disciplina,
                        'turma': turma,
                        'horarios': horarios,
                        'vagas': vagas,
                        'professor_1': prof1,
                        'professor_2': prof2
                    }
                    all_data.append(subject)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    pdf_file = "Divulgacao_por_Cursos_Horarios_2026.2_Ensino_Superior.pdf"
    output_file = "dados_disciplinas.json"
    if os.path.exists(pdf_file):
        print(f"Lendo {pdf_file}...")
        parse_pdf(pdf_file, output_file)
        print(f"Dados salvos em {output_file}")
    else:
        print(f"Erro: Arquivo {pdf_file} não encontrado.")
