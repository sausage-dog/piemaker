import pandas as pd
import numpy as np
import requests
import math
import time
import datetime


def AddCompositeETFs(settings, matrix, current_row):	

	## info
	matrix[current_row][0] = "ETF name"
	matrix[current_row][1] = "ETF weight"

	current_row = current_row + 1

	for original_etf in settings.etf_locations:
		matrix[current_row][0] = original_etf[0]
		matrix[current_row][1] = original_etf[2]
		current_row = current_row + 1

	return matrix, current_row

def AddUserInput(settings, matrix, current_row):

	current_row = current_row + 1

	matrix[current_row][0] = "Initial securities"
	matrix[current_row][3] = "Final securities"

	fc = 1
	ic = 1

	## loop over sec
	for user_sec in settings.user_securities:
		print("user sec: ",user_sec)
		if user_sec[2]:
			matrix[current_row + ic][0] = user_sec[0] + str(user_sec[1])
			matrix[current_row + ic][1] = user_sec[1]
			ic = ic + 1
		else:			
			matrix[current_row + fc][3] = user_sec[0]
			matrix[current_row + fc][4] = user_sec[1]
			fc = fc + 1

	current_row = current_row + max([fc,ic])

	return matrix, current_row

def FailedAllocate(matrix, failed_add, current_row):

	if len(failed_add) > 1:

		current_row = current_row + 1

		matrix[current_row][0] = "Failed to add due to rounding"

		current_row = current_row + 1
		column = 0

		for idx,fail in enumerate(failed_add): 
			matrix[current_row][column] = fail[0]

			current_row = current_row + 1

			print((idx +1) % 5)

			if (idx + 1) % 5 == 0:
				current_row = current_row - 5
				column = column + 1


	return matrix, current_row


def PupulatePies(matrix, pies, current_row):

	starting_column = 6

	for pie_idx, pie in enumerate(pies):

		if len(pie.securities) > 0:

			staring_row = 1

			## add pie number
			matrix[staring_row][starting_column] = "Pie " + str(pie_idx + 1)

			staring_row = staring_row + 1

			for idx,sec in enumerate(pie.securities):
				matrix[staring_row + idx][starting_column] = sec[0]
				matrix[staring_row + idx][starting_column + 2] = sec[1]
				if len(sec) > 2:
					matrix[staring_row + idx][starting_column + 1] = sec[2]

			starting_column = starting_column + 4

	return matrix

def WriteMatrix(matrix):
	## convert your array into a dataframe
	df = pd.DataFrame (matrix)

	filepath = "pie_"+str(time.time())[5:-4] + ".xlsx"

	df.to_excel(filepath, index=False)


def ProduceSpreadsheet(settings, pies, failed_add):

	## make a big empty array
	matrix = [[None for x in range(60)] for y in range(60)] 

	current_row = 1 ## leave a line blank

	## line for which etfs this was made from along with their weights
	matrix, current_row = AddCompositeETFs(settings, matrix, current_row)

	## added by the user
	matrix, current_row = AddUserInput(settings, matrix, current_row)

	## secs failed to allocate
	matrix, current_row = FailedAllocate(matrix, failed_add, current_row)

	## place pies on spreadsheet
	matrix = PupulatePies(matrix, pies, current_row)	

	WriteMatrix(matrix) 










