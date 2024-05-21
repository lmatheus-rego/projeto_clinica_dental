class Paciente:
    def __init__(self, id, nome, fao, idade, data, sexo, filiacao, endereco, telefone, tipo_fissura, historia_tratamento, carac_oclusais, neces_odonto, neces_orto, neces_cirur, outros, diagnostico, plano_tratamento):
        self.id = id
        self.nome = nome
        self.fao = fao
        self.idade = idade
        self.data = data
        self.sexo = sexo
        self.filiacao = filiacao
        self.endereco = endereco
        self.telefone = telefone
        self.tipo_fissura = tipo_fissura
        self.historia_tratamento = historia_tratamento
        self.carac_oclusais = carac_oclusais
        self.neces_odonto = neces_odonto
        self.neces_orto = neces_orto
        self.neces_cirur = neces_cirur
        self.outros = outros
        self.diagnostico = diagnostico
        self.plano_tratamento = plano_tratamento
