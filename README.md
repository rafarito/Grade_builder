# Gerador de Grade Curricular - IFBA 2026.2

Uma aplicação desktop moderna desenvolvida em Python para automatizar a leitura de horários em formato PDF e facilitar a montagem visual da grade de disciplinas do semestre.

A ferramenta foi pensada para resolver o problema dos "códigos de horários" difíceis de interpretar e o trabalho manual de cruzar disciplinas buscando evitar choques de horários.

---

## 🏗️ Estrutura do Projeto

A aplicação foi projetada com uma arquitetura **desacoplada**, separando a lógica de extração de dados, regras de negócio e interface visual. Isso facilita a manutenção ou até uma futura migração para um formato Web.

* `pdf_parser.py`: O "Motor de Leitura". Responsável por vasculhar a pasta atrás do primeiro `.pdf` de horários que encontrar, lendo linha a linha usando coordenadas visuais e gerando uma base de dados estruturada no arquivo `dados_disciplinas.json`.
* `scheduler.py`: O "Cérebro". Contém as regras de negócio. Ele carrega os dados do JSON, gerencia a grade atual do usuário e barra a inclusão de matérias caso haja **choque de horário**.
* `time_utils.py`: Módulo utilitário simples responsável por traduzir os códigos institucionais do IFBA (ex: `11`, `12`) em horários reais (ex: `17:00 - 17:50`).
* `gui.py`: A Interface Gráfica. Construída utilizando `CustomTkinter`, apresenta um visual moderno, no modo escuro, permitindo que o usuário interaja e visualize a sua semana.
* `dados_disciplinas.json`: O "Banco de Dados" cacheado gerado automaticamente no primeiro uso.
* `requirements.txt`: Lista as bibliotecas Python necessárias para rodar o projeto.

---

## ⚙️ Como a Aplicação Funciona?

1. Ao abrir o programa (`gui.py` ou o `.exe`), o sistema verifica se já existe o arquivo `dados_disciplinas.json`.
2. Se **não existir**, o motor de extração busca pelo primeiro arquivo PDF na pasta e lê o conteúdo para criar o `.json` na hora.
3. A tela principal é exibida com um menu para o usuário **selecionar o seu curso**.
4. As matérias disponíveis são listadas. Ao clicar em **"Adicionar à Grade"**, o sistema varre os dias e horários para verificar se não há colisão com outra disciplina já adicionada.
5. Se o caminho estiver livre, a matéria é plotada na tabela semanal (Segunda a Sábado) convertendo os blocos em horários reais.

---

## 🚀 Como Executar o Projeto (Código-Fonte)

Se você quiser rodar ou modificar o código Python na sua máquina, siga os passos:

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o arquivo principal da interface:
   ```bash
   python gui.py
   ```

*(Lembre-se de deixar um PDF de horários na mesma pasta para o uso inicial)*.

---

## 📦 Como Compilar seu Próprio Executável (Windows e Linux)

O projeto já está configurado para ser facilmente empacotado em um único arquivo, possibilitando enviar para outros alunos que não possuem o Python instalado.

Certifique-se de que instalou o `pyinstaller` (incluso no `requirements.txt`) e rode o comando abaixo na pasta raiz. O comando é o mesmo para ambos os sistemas:

```bash
pyinstaller --noconsole --onefile --collect-all customtkinter gui.py
```

**O que esse comando faz?**
* `--noconsole`: Impede que a tela do terminal apareça no fundo da aplicação.
* `--onefile`: Junta todos os arquivos em um único arquivo executável.
* `--collect-all customtkinter`: Garante que as fontes, temas e cores do `CustomTkinter` sejam embarcados corretamente.

Assim que o processo terminar, acesse a pasta **`dist/`**. 
* No **Windows**, o seu executável será o arquivo **`gui.exe`**.
* No **Linux**, o seu executável será um arquivo binário chamado **`gui`** (talvez seja necessário rodar `chmod +x gui` para dar permissão de execução, além de garantir que o pacote `python3-tk` esteja instalado no sistema operacional previamente).

**Aviso aos Usuários:** Para o executável funcionar na máquina de quem receber o programa, basta que o usuário **coloque o PDF de horários do IFBA na mesma pasta onde o executável for salvo**, antes de abrir o aplicativo pela primeira vez.
