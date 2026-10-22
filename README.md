# TCC

TCC de Ciência da Computação, no qual o tema é a redução do tempo de espera (ou tempo total de fila) no diagnóstico com avaliação neuropsicológica, utilizando Simulação de Eventos Discretos para análise de resultados

Hoje o código está em uma fase inicial, mas a ideia é que o simulador haja dois fluxos, onde um é com triagem e o outro é sem. Espera-se que o fluxo com triagem funcione da seguinte forma:
- Os pacientes vão chegando em uma fila única, onde cada um pode ter uma suspeita diferente
- De acordo com a suspeita, cada paciente iria para um canal de atendimento diferente, onde a suspeita do paciente vai determinar o tempo de atendimento na triagem, além de existir a possibilidade do paciente nem possuir a doença na qual ele suspeita, liberando-o já na triagem
- Caso na triagem, o paciente não tenha sido liberado, ele irá passar pelos exames neuropsicológicos
- Após os exames, é dado o diagnóstico do paciente

No processo sem triagem, o que muda é que o paciente vai diretamente para os exames.

Estima-se que com o processo da triagem, a quantidade mínima de exames da avaliação neuropsicológica para o diagnóstico seja reduzida.

Cada avaliação, tem a duração de uma hora, e geralmente os pacientes levam em torno de 4 à 6 avaliações para receber o diagnóstico (Sem a triagem).

É esperado que a simulação dure alguns meses (Provavelmente de 3-6 meses). E como as avaliações são feitas em dias diferentes, os pacientes que vieram na clínica antes voltam, só que sem realizar a etapa da triagem.

> [!TIP]
> A versão mais recente do artigo está em `./articles/tcc2`

# Setup

## Pré-requisitos
- Python >= 3.13
- Poetry instalado (Instruções de instalação: https://python-poetry.org/docs/)

Para instalar as dependências, é necessário utilizar o poetry:
```bash
poetry install
```

É possível carregar o ambiente virtual do python com o seguinte comando:
```bash
poetry env activate
```

Atualmente, temos os seguintes scripts no `taskipy`:
- `task run`: Executa o código contendo a simulação
- `task test`: Roda os testes automatizados
- `task commit`: Cria um commit interativamente com Commitizen
- `task lint:black:check`: Checa se os arquivos estão formatados de acordo com a biblioteca `black`
- `task lint:black:fix`: Formata os arquivos de acordo com a biblioteca `black`
- `task build:article`: Compila o latex usando o `mklatex` em `./articles/tcc2`

# Arquitetura de pastas

- `./src`: Contém o código fonte das aplicações
- `./tests`: Contém os testes automatizados das aplicações
- `./articles`: Contém os artigos em LaTeX, incluindo o TCC
- `./docs`: Rascunhos, documentações, orientações e anotações do projeto

## Parametrização por agenda histórica

`Parametros.carregar(caminho)` importa CSV (UTF-8) ou XLSX com uma linha por agendamento.
Os campos obrigatórios são `ID do Paciente`, `ID do Profissional`, `Início da agenda`,
`Fim da agenda`, `Suspeita do paciente` e `Status da agenda`. `ID de Agendamento`,
`Nome do Paciente` e `Nome do Profissional` são opcionais. Os timestamps precisam ser
texto ISO 8601 com fuso horário. A suspeita deve corresponder a um valor de `Suspeita`
(atualmente `Autismo` ou `TDAH`); status aceitos: `Pendente`, `Falta` e `Concluída`.

```python
import simpy
from classes import Equipe, Parametros, Simulador

parametros = Parametros.carregar("agenda.xlsx")
ids = list(parametros.probabilidades_profissionais)
nomes = [parametros.nomes_profissionais.get(id_profissional) for id_profissional in ids]
equipe = Equipe(simpy.Environment(), ids=ids, nomes=nomes)
simulador = Simulador(equipe, parametros=parametros)
simulador.iniciar(duracao=480)
```

A taxa por faixa de dia da semana/horário é calculada sobre datas observadas com pelo
menos um agendamento naquele dia da semana. Se o arquivo omitir dias sem agenda, essa
taxa é condicional e pode superestimar a demanda; a cobertura temporal do arquivo deve
ser conhecida para interpretar o resultado. O no-show é estimado como `Falta / (Falta +
Concluída)`, excluindo `Pendente`. A duração do atendimento continua sendo hipótese
configurável (`tempo_avaliacao`), pois os horários de agenda não provam o tempo efetivo
de consulta. Os registros calibram a geração estocástica; não são reproduzidos como
eventos exatos. A simulação começa na primeira faixa de horário encontrada no arquivo,
em vez da meia-noite, de modo que durações como 480 minutos representem um dia útil
iniciado no horário de atendimento observado.

# TODOs

1. Implementação da Lógica de Triagem:
  - É necessário criar a lógica para direcionar os pacientes para canais de atendimento distintos baseados na suspeita inicial da condição médica.

2. Mecanismo de Liberação e Retorno de Pacientes:
  - Desenvolver a funcionalidade de liberar pacientes durante a triagem caso a suspeita inicial esteja incorreta, finalizando o atendimento ao invés de seguir para a avaliação neuropsicológica.

3. Processo de Avaliação Neuropsicológica:
  - Implementar a etapa de avaliação (Duração: 1 hora), que ocorre após a triagem correta ou direto no fluxo sem triagem, coletando resultados que definirão o diagnóstico.

4. Gerenciamento de Pacientes de Retorno:
  - Desenvolver a capacidade de simular pacientes que retornam ao sistema. Estes precisam ignorar a triagem e ser direcionados direto para a avaliação, diferenciando-os dos pacientes novos.

5. Ajuste da Escala de Tempo do Simulador
  - Atualmente o código roda uma simulação de 8 horas (480 min). É necessário alterar a lógica para simular um período de 3 a 6 meses, ajustando a taxa de chegada de pacientes para essa duração.

6. Loop de Diagnóstico
  - Implementar a lógica de repetição: o paciente precisará passar por uma avaliação neuropsicológica, ter seu resultado processado e, se necessário, passar por novas avaliações até a conclusão do diagnóstico (Estimado: 4 a 6 avaliações).

7. Exportar Métricas
  - Criar o relatório de métricas estatísticas, com os resultados da simulação, incluindo o tempo médio de espera por fila, taxa de ocupação dos canais de avaliação e análise comparativa entre os fluxos (com triagem vs. sem triagem).
