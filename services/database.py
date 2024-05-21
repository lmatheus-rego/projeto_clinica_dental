import sqlite3



with sqlite3.connect('db_clinica_dental_teste.db', check_same_thread=False) as con:
	cursor = con.cursor()
	cursor.execute(
		"""
		CREATE TABLE IF NOT EXISTS Paciente
		(
			id integer primary key autoincrement,
			nome text not null,
			fao text not null,
			idade integer not null,
			data_nascimento date not null,
			sexo text not null,
			filiacao text not null,
			endereco text not null,
			telefone text not null,
			tipo_fissura text not null,
			historia_tratamento text
		)
		""") 