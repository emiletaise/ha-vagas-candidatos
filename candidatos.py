import face_recognition as reconhecedor
import random
import secrets
import simpy
import json

FOTOS_VISITANTES = [
  "faces/personagens1.jpeg",
  "faces/personagens2.jpeg",
  "faces/personagens3.jpeg",
  "faces/personagens4.jpeg"
]

ARQUIVO_DE_CONFIGURACAO = "../ha-vagas-candidatos/configuracao.json"
ARQUIVO_DE_VAGAS = "../ha-vagas-candidatos/vagas.json"
VISITANTE_SEM_CADASTRO = 0

# Função para ler as configurações e vagas do arquivo JSON
def preparar():
  global configuracao
  configuracao = None

  global vagas
  vagas = None

  try:
    with open(ARQUIVO_DE_CONFIGURACAO, "r") as arquivo_configuração:
      configuracao = json.load(arquivo_configuração)
      if configuracao:
        print("Arquivo de configuração carregado")
      arquivo_configuração.close()

    with open(ARQUIVO_DE_VAGAS, "r") as arquivo_vagas:
      vagas = json.load(arquivo_vagas)
      if vagas:
        print("Arquivo de vagas carregado")
      arquivo_vagas.close()
  except Exception as e:
    print(f"Erro ao ler configuração ou vagas: {str(e)}")
  
  global candidatos_reconhecidos
  candidatos_reconhecidos = {}

  global candidatos_com_cadastro
  candidatos_com_cadastro = {}

  global candidatos_apto
  candidatos_apto = {}


def simular_visitas():
    foto = random.choice(FOTOS_VISITANTES)
    print(f"Foto de visitantes: {foto}")

    visitantes = {
        "foto": foto,
        "candidatos": None
    }
    return visitantes

def candidato_reconhecido_previamente(candidato):
  global candidatos_reconhecidos

  reconhecido_previamente = False
  for reconhecido in candidatos_reconhecidos.values():
    if candidato["codigo"] == reconhecido["codigo"]:
      reconhecido_previamente = True
      break
  return reconhecido_previamente

def reconhecer_candidatos(visitantes):
  global configuracao
  global candidatos_reconhecidos

  print("\nRealizando reconhecimento de candidatos...")

  foto_visitantes = reconhecedor.load_image_file(visitantes["foto"])
  caracteristicas_dos_visitantes = reconhecedor.face_encodings(foto_visitantes)

  candidatos = []
  for candidato in configuracao["candidatos"]:
    if not candidato_reconhecido_previamente(candidato):
      fotos = candidato["fotos"]
      total_de_reconhecimentos = 0

      for foto in fotos:
        foto = reconhecedor.load_image_file(foto)
        caracteristicas = reconhecedor.face_encodings(foto)[0]

        reconhecimentos = reconhecedor.compare_faces(
          caracteristicas_dos_visitantes, caracteristicas)
        if True in reconhecimentos:
          total_de_reconhecimentos += 1

      if total_de_reconhecimentos / len(fotos) >= 0.6:
        candidatos.append(candidato)
    else:
      print("Candidato reconhecido previamente")

  return (len(candidatos) > 0), candidatos

def imprimir_dados_do_candidato(candidato):
  print(f"\nCandidato reconhecido: {candidato['nome']}")
  print(f"Idade: {candidato['idade']}")
  print(f"Tem cadastro: {candidato['cadastro']}")
  print(f"Habilidade: {candidato['habilidade']}")


def verificar_vagas(ambiente_de_simulacao):
  global vagas
  global candidatos_com_cadastro
  global candidatos_apto

  while True:
    if len(candidatos_com_cadastro):
      print(f"\nVerificando vagas em {ambiente_de_simulacao.now}")

      for id, candidato in list(candidatos_com_cadastro.items()):
        vagas_compativeis = []
        for vaga in vagas["vagas"]:
          if candidato['habilidade'] in vaga['habilidade']:
              vagas_compativeis.append(vaga)

        if len(vagas_compativeis) == 0:
          print("\nNão há disponibilidade de vagas para a habilidade do candidato ", candidato["nome"])
        else:
          candidatos_apto[id] = candidato
          vaga_escolhida = vagas_compativeis[0]
          print("\nO candidato ", candidato["nome"], "está apto para a vaga:", vaga_escolhida["titulo"])

      yield ambiente_de_simulacao.timeout(40)
    else:
      yield ambiente_de_simulacao.timeout(1)


def agendar_entrevista(ambiente_de_simulacao):
  global candidatos_apto

  while True:
    if len(candidatos_apto):
      print(f"\nAgendando entrevista em {ambiente_de_simulacao.now}")

      for id, candidato in list(candidatos_apto.items()):
        print("\nO candidato", candidato["nome"], "está com sua entrevista marcada para a vaga compatível")

      yield ambiente_de_simulacao.timeout(40)
    else:
      yield ambiente_de_simulacao.timeout(1)

def encaminhar_recepcao(ambiente_de_simulacao):
  global candidatos_reconhecidos
  global candidatos_com_cadastro

  while True:
    if len(candidatos_reconhecidos):
      print(f"\nIdentificando cadidatos com cadastro em {ambiente_de_simulacao.now}")

      for id, candidato in list(candidatos_reconhecidos.items()):
        if candidato['cadastro'] == False:
          print("\nO candidato", candidato["nome"], "não tem cadastro e está sendo encaminhado para a recepção")
        else: 
          candidatos_com_cadastro[id] = candidato

      yield ambiente_de_simulacao.timeout(40)
    else:
      yield ambiente_de_simulacao.timeout(1)

def reconhecer_visitantes(ambiente_de_simulacao):
  global candidatos_reconhecidos

  while True:
    print(f"\nTentando reconhecer um candidato entre visitantes em {ambiente_de_simulacao.now}")

    visitantes = simular_visitas()
    ocorreram_reconhecimentos, candidatos = reconhecer_candidatos(visitantes)

    if ocorreram_reconhecimentos:
      for candidato in candidatos:
        id = secrets.token_hex(nbytes=16).upper()
        candidatos_reconhecidos[id] = candidato

        imprimir_dados_do_candidato(candidato)
    else:
      print(f"\nNenhum candidato foi reconhecido")

    yield ambiente_de_simulacao.timeout(40) 

def limpar_lista_candidatos(ambiente_de_simulacao):
  global candidatos_reconhecidos
  global candidatos_com_cadastro
  global candidatos_apto

  while True:
    if len(candidatos_reconhecidos):
      print(f"\nlimpando lista de candidatos em {ambiente_de_simulacao.now}")

      candidatos_reconhecidos = {}

      candidatos_com_cadastro = {}

      candidatos_apto = {}

      yield ambiente_de_simulacao.timeout(40)
    else:
      yield ambiente_de_simulacao.timeout(1)


if __name__ == "__main__":
  preparar()

  ambiente_de_simulacao = simpy.Environment()

  ambiente_de_simulacao.process(reconhecer_visitantes(ambiente_de_simulacao))
  ambiente_de_simulacao.process(encaminhar_recepcao(ambiente_de_simulacao))
  ambiente_de_simulacao.process(verificar_vagas(ambiente_de_simulacao))
  ambiente_de_simulacao.process(agendar_entrevista(ambiente_de_simulacao))
  ambiente_de_simulacao.process(limpar_lista_candidatos(ambiente_de_simulacao))

  ambiente_de_simulacao.run(until=1000)
