# Documentação do Projeto: Pipeline de Dados de E-commerce com CI/CD

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Conceitos Fundamentais](#2-conceitos-fundamentais)
3. [Estrutura de Pastas](#3-estrutura-de-pastas)
4. [Arquivo por Arquivo — Explicação Detalhada](#4-arquivo-por-arquivo--explicação-detalhada)
   - [requirements.txt](#41-requirementstxt)
   - [conftest.py](#42-conftestpy)
   - [data/raw_sales.csv](#43-dataraw_salescsv)
   - [src/transform.py](#44-srctransformpy)
   - [tests/test_pipeline.py](#45-teststest_pipelinepy)
   - [.github/workflows/ci-cd.yml](#46-githubworkflowsci-cdyml)
5. [Fluxo Completo de Dados](#5-fluxo-completo-de-dados)
6. [Fluxo do CI/CD](#6-fluxo-do-cicd)
7. [Comandos Locais — Referência Rápida](#7-comandos-locais--referência-rápida)
8. [O que acontece se um teste falhar?](#8-o-que-acontece-se-um-teste-falhar)
9. [Próximos Passos para Evoluir o Projeto](#9-próximos-passos-para-evoluir-o-projeto)

---

## 1. Visão Geral do Projeto

Este projeto simula um pipeline de dados real de e-commerce. O objetivo é demonstrar, de forma prática e local, como funciona o ciclo completo de **DataOps**:

```
Dado Bruto (CSV) → Limpeza/Transformação → Dado Limpo (Parquet) → Testes → Deploy
```

A ideia central é: **nenhum código vai para produção sem passar por testes automatizados**. Isso é exatamente o que o CI/CD garante.

### Tecnologias usadas

| Tecnologia | Para que serve neste projeto |
|---|---|
| Python | Linguagem principal |
| DuckDB | Banco de dados em memória para processar o CSV com SQL |
| Parquet | Formato de arquivo colunar, eficiente para dados analíticos |
| pytest | Framework de testes do Python |
| GitHub Actions | Ferramenta de CI/CD que roda automaticamente na nuvem |

---

## 2. Conceitos Fundamentais

### O que é um Pipeline de Dados?

Um pipeline de dados é uma sequência de etapas que transformam dados brutos (sujos, incompletos) em dados prontos para uso. Pense como uma linha de montagem:

```
[CSV bruto] → [Remove duplicatas] → [Preenche nulos] → [Salva Parquet limpo]
```

### O que é CI/CD?

- **CI (Continuous Integration)**: A cada vez que você envia código novo (push), um servidor roda os testes automaticamente e verifica se nada quebrou.
- **CD (Continuous Delivery/Deployment)**: Se o CI passar, o código é automaticamente preparado/enviado para o ambiente de produção.

A lógica é simples: **se os testes passam → o código é confiável → pode ser publicado**.

### O que é DuckDB?

DuckDB é um banco de dados que roda **dentro do processo Python**, sem precisar instalar nenhum servidor. Você escreve SQL normal e ele processa arquivos CSV, Parquet, JSON diretamente. É muito rápido para análises e pipelines de dados.

### O que é Parquet?

Parquet é um formato de arquivo para dados tabulares (como uma planilha), mas armazenado de forma **colunar** — ideal para análises porque você lê só as colunas que precisa. É o formato padrão em Data Engineering porque é comprimido e muito mais rápido que CSV para leituras analíticas.

---

## 3. Estrutura de Pastas

```
ci-cd/
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml        ← Receita do pipeline CI/CD (roda no GitHub)
│
├── data/
│   ├── raw_sales.csv        ← Dados de entrada (brutos, com problemas)
│   └── processed/
│       └── clean_sales.parquet  ← Gerado pelo pipeline (dados limpos)
│
├── src/
│   ├── __init__.py          ← Marca a pasta como um pacote Python
│   └── transform.py         ← Toda a lógica de limpeza dos dados
│
├── tests/
│   └── test_pipeline.py     ← Testes automáticos com pytest
│
├── conftest.py              ← Configuração do pytest (resolve imports)
└── requirements.txt         ← Lista de dependências Python
```

**Por que essa separação de pastas?**
- `src/` contém o código de produção — a lógica real do negócio.
- `tests/` contém os testes — nunca vão para produção, mas validam o que está em `src/`.
- `data/` contém os arquivos de dados — separados do código para facilitar versionamento.
- `.github/` é uma pasta especial que o GitHub reconhece automaticamente para CI/CD.

---

## 4. Arquivo por Arquivo — Explicação Detalhada

### 4.1 `requirements.txt`

```
duckdb==1.1.3
pytest==8.3.4
```

Lista as dependências do projeto com **versões fixas** (pinned versions). Isso é uma boa prática de engenharia porque garante que qualquer pessoa (ou o servidor de CI) que instalar as dependências vai ter exatamente as mesmas versões que você testou localmente.

- `duckdb==1.1.3` → banco de dados para processar os dados
- `pytest==8.3.4` → framework para rodar os testes

Para instalar:
```cmd
pip install -r requirements.txt
```

---

### 4.2 `conftest.py`

```python
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
```

Este arquivo é especial do pytest. Ele é carregado **automaticamente** antes de qualquer teste rodar.

**O problema que ele resolve:** quando o pytest tenta importar `from src.transform import run_pipeline` dentro de `tests/test_pipeline.py`, o Python não sabe onde está a pasta `src/` — ele só conhece o caminho padrão de bibliotecas instaladas.

**A solução:** `sys.path.insert(0, ...)` adiciona a raiz do projeto (`ci-cd/`) na lista de lugares onde o Python procura módulos. Assim, `from src.transform import ...` funciona corretamente.

- `sys.path` → lista de diretórios onde Python busca módulos
- `os.path.abspath(os.path.dirname(__file__))` → caminho absoluto da pasta onde `conftest.py` está (a raiz do projeto)
- `insert(0, ...)` → insere no início da lista, dando prioridade à raiz do projeto

---

### 4.3 `data/raw_sales.csv`

```csv
order_id,customer_id,product,quantity,unit_price,order_date
1001,C01,Notebook,2,1500.00,2024-01-10
1002,C02,Mouse,1,80.00,2024-01-11
1003,C03,Teclado,1,200.00,2024-01-12
1002,C02,Mouse,1,80.00,2024-01-11   ← DUPLICATA do order_id 1002
1005,C04,Monitor,,950.00,2024-01-13  ← quantity NULA (campo vazio)
1006,C05,Headset,2,350.00,2024-01-14
```

Este arquivo simula dados que chegam de um sistema de e-commerce — e dados reais **sempre têm problemas**. Os dois problemas intencionais são:

1. **Linha 4 (order_id 1002)**: duplicata exata da linha 2. Isso acontece em sistemas reais por re-processamento de eventos, falha de rede que reenvia a requisição, bug no sistema de origem, etc.

2. **Linha 5 (Monitor)**: `quantity` está vazia. Isso acontece quando um campo é opcional no sistema de origem, ou houve falha na coleta do dado.

**Colunas:**
| Coluna | Tipo | Descrição |
|---|---|---|
| order_id | Inteiro | Identificador único do pedido |
| customer_id | Texto | Identificador do cliente |
| product | Texto | Nome do produto |
| quantity | Inteiro | Quantidade comprada (pode ser nulo) |
| unit_price | Decimal | Preço unitário do produto |
| order_date | Data | Data do pedido |

---

### 4.4 `src/transform.py`

Este é o coração do projeto. Vamos dissecar cada parte.

#### Constantes de configuração

```python
RAW_PATH = "data/raw_sales.csv"
PROCESSED_DIR = "data/processed"
PROCESSED_PATH = os.path.join(PROCESSED_DIR, "clean_sales.parquet")
```

Caminhos definidos como constantes no topo do arquivo. Boa prática: se precisar mudar o caminho, muda em um lugar só. `os.path.join` constrói o caminho de forma compatível com qualquer sistema operacional (Windows usa `\`, Linux/Mac usam `/`).

#### Função `run_pipeline()`

```python
def run_pipeline(raw_path: str = RAW_PATH, output_path: str = PROCESSED_PATH) -> int:
```

A função aceita parâmetros com valores padrão. Isso é crucial para os testes: os testes podem chamar `run_pipeline()` sem argumentos (usa os padrões) ou passar caminhos customizados. O `-> int` indica que a função retorna um inteiro (o número de linhas processadas).

#### Passo 1: Criar pasta de saída

```python
os.makedirs(os.path.dirname(output_path), exist_ok=True)
```

Cria a pasta `data/processed/` se ela não existir. `exist_ok=True` evita erro caso a pasta já exista — sem esse parâmetro, rodaria com erro na segunda execução.

#### Passo 2: Conectar ao DuckDB

```python
con = duckdb.connect()
```

Cria uma conexão em memória com o DuckDB. Sem passar um arquivo como argumento, o banco de dados existe apenas enquanto o script roda — dados temporários, sem persistência além do Parquet que vamos salvar.

#### Passo 3: Carregar o CSV

```python
con.execute(f"CREATE TABLE raw AS SELECT * FROM read_csv_auto('{raw_path}')")
```

`read_csv_auto()` é uma função do DuckDB que lê um CSV e **detecta automaticamente** os tipos de cada coluna (inteiro, texto, data, etc.). O resultado vira uma tabela chamada `raw` dentro do DuckDB. A partir daqui, temos todos os dados do CSV disponíveis para consultas SQL.

Estado da tabela `raw` neste momento:
```
order_id | customer_id | product  | quantity | unit_price | order_date
---------|-------------|----------|----------|------------|----------
1001     | C01         | Notebook | 2        | 1500.00    | 2024-01-10
1002     | C02         | Mouse    | 1        | 80.00      | 2024-01-11
1003     | C03         | Teclado  | 1        | 200.00     | 2024-01-12
1002     | C02         | Mouse    | 1        | 80.00      | 2024-01-11  ← duplicata
1005     | C04         | Monitor  | NULL     | 950.00     | 2024-01-13  ← nulo
1006     | C05         | Headset  | 2        | 350.00     | 2024-01-14
```

#### Passo 4: Remover duplicatas

```python
con.execute("""
    CREATE TABLE deduped AS
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) AS rn
        FROM raw
    ) t WHERE rn = 1
""")
```

Esta é a parte mais sofisticada. Vamos entender linha a linha:

- `ROW_NUMBER()` → função de janela (window function) que numera as linhas
- `OVER (PARTITION BY order_id)` → reinicia a numeração para cada `order_id` diferente. Ou seja, para cada grupo de linhas com o mesmo `order_id`, a primeira recebe `rn=1`, a segunda `rn=2`, etc.
- `ORDER BY order_id` → define a ordem dentro de cada grupo (aqui é arbitrária, pois os dados são idênticos)
- `WHERE rn = 1` → mantém apenas a primeira ocorrência de cada `order_id`

Visualizando a subquery interna (antes do `WHERE rn = 1`):
```
order_id | ... | rn
---------|-----|----
1001     | ... | 1   ← único, rn=1
1002     | ... | 1   ← primeira ocorrência
1002     | ... | 2   ← segunda ocorrência, será removida
1003     | ... | 1   ← único, rn=1
1005     | ... | 1   ← único, rn=1
1006     | ... | 1   ← único, rn=1
```

Após `WHERE rn = 1`, a duplicata do `order_id 1002` é eliminada.

#### Passo 5: Preencher nulos

```python
con.execute("""
    CREATE TABLE clean AS
    SELECT
        order_id,
        customer_id,
        product,
        COALESCE(quantity, 1) AS quantity,
        unit_price,
        order_date
    FROM deduped
""")
```

`COALESCE(quantity, 1)` retorna o primeiro valor não-nulo da lista. Então:
- Se `quantity` tem um valor → retorna esse valor
- Se `quantity` é NULL → retorna `1` (assumimos pedido unitário)

Também serve para listar explicitamente as colunas sem o `rn` (número da linha) que criamos na etapa anterior.

#### Passo 6: Salvar como Parquet

```python
con.execute(f"COPY clean TO '{output_path}' (FORMAT PARQUET)")
```

O comando `COPY ... TO ...` exporta a tabela para um arquivo. `FORMAT PARQUET` indica o formato de saída. O DuckDB cuida de toda a serialização e compressão do Parquet automaticamente.

#### Passo 7: Contar e retornar

```python
row_count = con.execute("SELECT COUNT(*) FROM clean").fetchone()[0]
con.close()
print(f"[OK] Pipeline concluído. {row_count} linhas salvas em: {output_path}")
return row_count
```

- Conta as linhas para logar e retornar (útil para quem chama a função saber o resultado)
- `fetchone()` retorna uma tupla com a primeira linha do resultado, ex: `(5,)`
- `[0]` pega o primeiro elemento da tupla, o número `5`
- `con.close()` libera a memória

#### Bloco `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    run_pipeline()
```

Este bloco só executa quando o arquivo é rodado diretamente (`python src/transform.py`). Quando o arquivo é importado por outro módulo (como nos testes), este bloco é ignorado. É um padrão Python para separar "executar como script" de "importar como módulo".

---

### 4.5 `tests/test_pipeline.py`

#### Import e constante

```python
from src.transform import run_pipeline

PROCESSED_PATH = "data/processed/clean_sales.parquet"
```

Importa a função de transformação diretamente para usar nos testes. A constante do caminho é redefinida aqui para deixar os testes autocontidos e legíveis.

#### Fixture `run_transform`

```python
@pytest.fixture(scope="module", autouse=True)
def run_transform():
    """Executa o pipeline antes dos testes."""
    run_pipeline()
```

Uma **fixture** do pytest é uma função de configuração que prepara o ambiente antes dos testes.

- `@pytest.fixture` → marca a função como fixture
- `scope="module"` → executa apenas **uma vez** para todo o arquivo de testes (não uma vez por teste). Evita rodar o pipeline 4 vezes.
- `autouse=True` → aplica automaticamente a todos os testes do módulo, sem precisar declarar como parâmetro em cada teste

Em resumo: antes de qualquer teste rodar, o pipeline é executado para garantir que o arquivo Parquet existe.

#### Teste 1: arquivo existe

```python
def test_arquivo_processado_existe():
    assert os.path.exists(PROCESSED_PATH), f"Arquivo não encontrado: {PROCESSED_PATH}"
```

O teste mais básico. Verifica se o pipeline de fato gerou o arquivo de saída. Se `os.path.exists()` retornar `False`, o `assert` falha e o pytest reporta o erro com a mensagem descritiva.

#### Teste 2: sem duplicatas

```python
def test_sem_order_ids_duplicados():
    con = duckdb.connect()
    result = con.execute(f"""
        SELECT order_id, COUNT(*) AS cnt
        FROM read_parquet('{PROCESSED_PATH}')
        GROUP BY order_id
        HAVING cnt > 1
    """).fetchall()
    con.close()
    assert result == [], f"Duplicatas encontradas: {result}"
```

Lê o Parquet gerado e executa uma query que retorna todos os `order_id` que aparecem mais de uma vez (`HAVING cnt > 1`). Se a limpeza funcionou, essa query retorna uma lista vazia `[]`. O `assert result == []` falha se houver qualquer duplicata.

#### Teste 3: sem nulos em quantity

```python
def test_sem_quantity_nula():
    nulls = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{PROCESSED_PATH}')
        WHERE quantity IS NULL
    """).fetchone()[0]
    assert nulls == 0, f"Encontradas {nulls} linhas com quantity nula"
```

Conta quantas linhas têm `quantity IS NULL`. Se o `COALESCE` funcionou, esse número deve ser zero.

#### Teste 4: contagem de linhas

```python
def test_contagem_de_linhas():
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{PROCESSED_PATH}')").fetchone()[0]
    assert count == 5, f"Esperado 5 linhas, encontrado {count}"
```

Valida a contagem final. O raciocínio: 6 linhas no CSV bruto, menos 1 duplicata = 5 linhas esperadas. Este teste garante que não removemos linhas a mais (nem de menos).

---

### 4.6 `.github/workflows/ci-cd.yml`

Este arquivo usa a linguagem **YAML** (Yet Another Markup Language) — um formato de configuração baseado em indentação. O GitHub Actions lê este arquivo e executa as instruções automaticamente.

#### Cabeçalho e gatilhos

```yaml
name: CI/CD Pipeline - E-commerce Data

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

- `name` → nome que aparece na aba "Actions" do GitHub
- `on` → define os gatilhos (triggers) que disparam o pipeline
  - `push: branches: [main]` → dispara quando alguém faz `git push` para a branch `main`
  - `pull_request: branches: [main]` → dispara quando alguém abre ou atualiza um Pull Request com destino à `main`

#### Job de CI

```yaml
jobs:
  ci:
    name: "CI - Test & Validate"
    runs-on: ubuntu-latest
```

- `jobs` → bloco que contém todos os jobs (trabalhos) do pipeline
- `ci` → identificador do job (usado para referência entre jobs)
- `runs-on: ubuntu-latest` → o GitHub vai criar uma máquina virtual com Ubuntu para executar este job. Cada job roda em uma VM limpa e descartável.

#### Steps do CI

```yaml
    steps:
      - name: Checkout do repositório
        uses: actions/checkout@v4
```

`uses` referencia uma **Action** pré-construída. `actions/checkout@v4` é uma Action oficial do GitHub que baixa o código do repositório para dentro da VM. Sem este step, a VM estaria vazia.

```yaml
      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
```

`actions/setup-python@v5` instala o Python na VM. `with` passa parâmetros para a Action — neste caso, a versão específica do Python.

```yaml
      - name: Instalar dependências
        run: pip install -r requirements.txt
```

`run` executa um comando shell diretamente na VM. Instala as dependências listadas no `requirements.txt`.

```yaml
      - name: Rodar pipeline de transformação
        run: python src/transform.py

      - name: Executar testes com pytest
        run: pytest tests/ -v
```

Executa o pipeline e depois os testes. `-v` no pytest ativa o modo verbose, mostrando o nome e resultado de cada teste individualmente.

#### Job de CD

```yaml
  cd:
    name: "CD - Deploy (Simulado)"
    runs-on: ubuntu-latest
    needs: ci
```

`needs: ci` é a chave do encadeamento. Este job **só começa** depois que o job `ci` terminar com sucesso. Se qualquer step do CI falhar, o CD nem é iniciado.

```yaml
      - name: Deploy simulado
        run: |
          echo "Deploying to production server..."
```

O `|` em YAML indica um bloco de texto multilinha. Cada `echo` é executado sequencialmente. Em um projeto real, aqui você colocaria comandos como `scp` para copiar arquivos para um servidor, `kubectl apply` para atualizar um cluster Kubernetes, ou chamadas para APIs de serviços de nuvem.

---

## 5. Fluxo Completo de Dados

Visualizando a transformação que acontece dentro do `transform.py`:

```
raw_sales.csv (6 linhas)
│
│  order_id 1002 aparece 2x
│  quantity do Monitor é NULL
│
▼
[DuckDB: read_csv_auto()]
Tabela: raw (6 linhas)
│
▼
[ROW_NUMBER() OVER (PARTITION BY order_id)]
Numera ocorrências de cada order_id
│
▼
[WHERE rn = 1]
Tabela: deduped (5 linhas) — duplicata removida
│
▼
[COALESCE(quantity, 1)]
Tabela: clean (5 linhas) — nulo preenchido com 1
│
▼
[COPY TO ... FORMAT PARQUET]
clean_sales.parquet (5 linhas, dado limpo)
```

---

## 6. Fluxo do CI/CD

```
Desenvolvedor faz git push para main
           │
           ▼
    GitHub Actions detecta o evento
           │
           ▼
    ┌──────────────────────────────┐
    │     JOB: CI                  │
    │  1. Checkout do código        │
    │  2. Instala Python 3.11      │
    │  3. pip install -r req...    │
    │  4. python src/transform.py  │
    │  5. pytest tests/ -v         │
    └──────────────┬───────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
      PASSOU?              FALHOU?
         │                   │
         ▼                   ▼
  ┌─────────────┐    ┌──────────────────┐
  │  JOB: CD    │    │  Pipeline para.  │
  │  Deploy     │    │  Notificação de  │
  │  Simulado   │    │  erro no GitHub. │
  └─────────────┘    └──────────────────┘
```

**O ponto-chave:** se qualquer step falhar (um teste quebrar, o script jogar uma exceção), o GitHub Actions marca o pipeline como vermelho (❌) e o CD não roda. Isso garante que código com problemas nunca chega ao ambiente de produção.

---

## 7. Comandos Locais — Referência Rápida

```cmd
# Instalar dependências
pip install -r requirements.txt

# Rodar apenas o pipeline de transformação
python src/transform.py

# Rodar todos os testes
pytest tests/ -v

# Rodar um teste específico
pytest tests/test_pipeline.py::test_sem_order_ids_duplicados -v

# Ver o conteúdo do Parquet gerado (opcional, requer pandas ou duckdb no terminal)
python -c "import duckdb; print(duckdb.sql(\"SELECT * FROM 'data/processed/clean_sales.parquet'\").df())"
```

---

## 8. O que acontece se um teste falhar?

Para testar o comportamento do CI/CD quando algo quebra, você pode introduzir um problema intencional. Exemplo: edite `raw_sales.csv` e adicione mais uma duplicata sem corrigir o pipeline. O teste `test_sem_order_ids_duplicados` vai falhar com:

```
FAILED tests/test_pipeline.py::test_sem_order_ids_duplicados
AssertionError: Duplicatas encontradas: [(1002, 2)]
```

No GitHub Actions, isso aparece como um pipeline vermelho (❌) e o job de CD não executa. É exatamente esse comportamento que queremos — um portão de qualidade automático.

---

## 9. Próximos Passos para Evoluir o Projeto

Se quiser ir além, estas são as evoluções naturais deste projeto:

1. **Adicionar mais regras de qualidade** — validar que `unit_price` é sempre positivo, que `order_date` está em um intervalo válido, etc.

2. **Separar ambientes** — ter branches `develop`, `staging` e `main`, cada uma com seu próprio job de deploy para ambientes diferentes.

3. **Adicionar cobertura de testes** — configurar o `pytest-cov` para medir qual percentual do código está coberto pelos testes.

4. **Cache de dependências no CI** — usar `actions/cache` para cachear o `pip install` e deixar o pipeline mais rápido.

5. **Publicar artefatos** — usar `actions/upload-artifact` para salvar o Parquet gerado no CI como artefato downloadável no GitHub.

6. **Orquestração real** — substituir o script Python por um workflow do Apache Airflow ou Prefect para pipelines mais complexos com múltiplas etapas e dependências.
