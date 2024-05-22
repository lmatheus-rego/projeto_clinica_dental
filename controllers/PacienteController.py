import streamlit as st
from typing import List
import services.database as db
import models.Paciente as paciente

def incluir(paciente):
	db.cursor.execute("""
		INSERT INTO Paciente(nome, fao, idade, data_nascimento, sexo, filiacao, endereco, telefone, tipo_fissura, historia_tratamento) 
		VALUES (?, ? ,?, ?, ?, ?, ?, ?, ?, ?)""", (paciente.nome, paciente.fao, paciente.idade, paciente.data, paciente.sexo, paciente.filiacao, paciente.endereco, paciente.telefone, paciente.tipo_fissura, paciente.historia_tratamento))
	db.con.commit()

def SelecionarTodos():
	db.cursor.execute("SELECT * FROM PACIENTE")
	pacienteList = []

	for row in db.cursor.fetchall():
		pacienteList.append(paciente.Paciente(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17]))
	
	return pacienteList

def Ficha_Clinica():
	idficha = st.query_params["idpaciente"]
	db.cursor.execute("SELECT * FROM PACIENTE WHERE id = ?""",idficha)
	ficha = []
	for row in db.cursor.fetchall():
		ficha.append(paciente.Paciente(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17]))
	return ficha

def Buscar_Paciente(id):
	db.cursor.execute("SELECT * FROM PACIENTE WHERE id = ?""",id)
	ficha = []
	for row in db.cursor.fetchall():
		ficha.append(paciente.Paciente(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17]))
	st.query_params["idpaciente"] = id
	return ficha

def Alterar(paciente):
	
	db.cursor.execute("""
		UPDATE Paciente
		SET nome = ?, fao = ?, idade = ?, data_nascimento = ?, sexo = ?, filiacao = ?, endereco = ?, telefone = ?, tipo_fissura = ?, historia_tratamento = ? 
		WHERE id = ?""", (paciente.nome, paciente.fao, paciente.idade, paciente.data, paciente.sexo, paciente.filiacao, paciente.endereco, paciente.telefone, paciente.tipo_fissura, paciente.historia_tratamento, paciente.id))
	db.con.commit()

def Diagnostico_docs(paciente):
	
	db.cursor.execute("""
		UPDATE Paciente
		SET carac_oclusais = ?, neces_odonto = ?, neces_orto = ?, neces_cirur = ?, outros = ?, diagnostico = ?, plano_tratamento = ? 
		WHERE id = ?""", (paciente.carac_oclusais, paciente.neces_odonto, paciente.neces_orto, paciente.neces_cirur, paciente.outros, paciente.diagnostico, paciente.plano_tratamento, paciente.id))
	db.con.commit()