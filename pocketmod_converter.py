#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""PocketMod converter

This script should be called from the command line with a valid input
file argument. It takes the input PDF and converts it into a pocketmod
format PDF. This pocketmod PDF is output into the directory the script
was called from.

This tool accepts a PDF file as input. PDFs with pages not divisible by 8
will have extra blank pages converted into a pocketmod. For multipule
input files, put all files in 'InputPdfs' folder and enter 'file' as input.


This script requires `PyPDF2` be installed within the Python environment
you are running this script in: see https://github.com/mstamy2/PyPDF2.

Example (single file)
-------
Run the script from the command line with the PDF file to be converted
as the input argument.

$ python pocketmod_converter.py input.pdf
Enter output file name (without.pdf): custom_name
The file has been converted. The output file is: custom_name.pdf

$ ls
pocketmod_converter.py input.pdf output_20200407123547.pdf

Example (multiple files)
-------
Run the script from the command line with 'file' as the input argument.

$ python pocketmod_converter.py file
Current converting file: input1.pdf
Enter output file name (without.pdf): output1
The file has been converted.  The output file is: output1.pdf
-----------------------------------------------------
Current converting file: input2.pdf
Enter output file name (without.pdf): output2
The file has been converted.  The output file is: output2.pdf
...
Conversion finished.

The directory will now have a custom named PDF as output from the script.
"""

import os
import argparse
import math

# PyPDF2 repo: https://github.com/mstamy2/PyPDF2
from PyPDF2 import PdfFileReader, PdfFileWriter

def check_input_file(input_file):
	"""Check the input file if is a pdf or folder."""

	if os.path.isfile(input_file):
		if os.path.basename(input_file)[-3:].lower() == 'pdf':
			return 'pdf'
		else:
			raise ValueError('File type is not a pdf.')	
					
	if os.path.isdir(input_file):
		return 'folder'
	else:
		raise FileNotFoundError('Please enter a valid foldername.')

def input_size_orientation(input_file):
	"""Determine the paper size and orientation of the input file."""
	media_box = PdfFileReader(input_file).getPage(0).mediaBox
	# 0.3528 is the mm approximation of 1/72 of an inch
	# PyPDF2 uses increments of 1/72 of an inch for sizing
	width = round(float(media_box[2]) * 0.3528)
	height = round(float(media_box[3]) * 0.3528)
	
	if width > height:
		orientation = 'Landscape'
	else:
		orientation = 'Portrait'

	return(width, height, orientation)

def pocket_modder(input_file, width, height, orientation):
	"""Convert and output a PDF file into a pocketmod PDF file.

	Parameters
	----------
	input_file : str
		The path of the pdf file to be converted.
	width : int
		The width in mm of the input file's first page.
	height: int
		The height in mm of the input file's first page.
	orientation : str
		The orientation of the input file's first page - either
		'Portrait' or 'Landscape' returned.

	Notes
	-----
	The output PDF will be the same dimension as the input file's first
	page. For example, an A4-sized input PDF will result in an A4-sized
	output PDF, likewise, an A3-sized input PDF will result in an
	A3-sized output PDF.
	"""
	with open(input_file, 'rb') as input_pdf:
		input_pdf = PdfFileReader(input_pdf)
		writer = PdfFileWriter()
		# 0.3528 is the mm approximation of 1/72 of an inch
		# PyPDF2 uses increments of 1/72 of an inch for sizing
		pypdf_scale = 0.3528

		if orientation == 'Landscape':
			width, height = height, width

		# calculate the desired width of single page when it has been converted
		output_width = height / 4
		output_height = width / 2
		# convert the output width and height to the PyPDF2 scale
		x_translation = output_width/ pypdf_scale
		y_translation = output_height / pypdf_scale

		# get best scale as to maximise the area of the converted pdf
		scale = min(output_width / width, output_height / height)

		transformation_dict = {
			'Landscape' : {
				0 : (0, y_translation, 270),
				1 : (x_translation, y_translation, 90),
				2 : ((x_translation * 2), y_translation, 90),
				3 : ((x_translation * 3), y_translation, 90),
				4 : ((x_translation * 4), y_translation, 90),
				5 : (x_translation * 3 , y_translation, 270),
				6 : (x_translation * 2 , y_translation, 270),
				7 : (x_translation , y_translation, 270)},
			'Portrait' : {
				0 : (x_translation, y_translation, 180),
				1 : (0 , y_translation, 0),
				2 : (x_translation, y_translation, 0),
				3 : ((x_translation * 2), y_translation, 0),
				4 : ((x_translation * 3), y_translation, 0),
				5 : (x_translation * 4, y_translation, 180),
				6 : (x_translation * 3, y_translation, 180),
				7 : (x_translation * 2, y_translation, 180)}
			}

		new_pdf = []
		new_pdf_pageNum = math.ceil(input_pdf.getNumPages() / 8)
		page = 0
		for i in range(0, new_pdf_pageNum):
			new_pdf.append(writer.addBlankPage(height / pypdf_scale, width / pypdf_scale))
			for key in range(0, 8):
				if page == input_pdf.getNumPages():
					break
				content_page = input_pdf.getPage(page)
				new_pdf[i].mergeRotatedScaledTranslatedPage(
					content_page,
					transformation_dict[orientation][key][2],
					scale,
					transformation_dict[orientation][key][0],
					transformation_dict[orientation][key][1],
					expand=False)
				page += 1 

		#check if input name already exists
		response = 'N'
		while not (response == 'Y' or response == 'y'):
			response = 'Y'
			output_pdf = input('Enter output file name (without.pdf): ') + '.pdf'
			if os.path.exists(output_pdf):
				response = input('Output file name already exists, do you want to replace the file? (Y/N): ')
				
		with open(output_pdf, 'wb') as out_file:
			writer.write(out_file)
			print('The file has been converted.',
					' The output file is: {}'.format(output_pdf))

def main():
	"""Collect and parse the command line input argument.
	Check the validity of the input file, then convert and output
	the PDF.
	"""
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('input_file', type=str, help='Input file to convert')
	args = parser.parse_args()

	file_type = check_input_file(args.input_file)

	#multipule input files
	if file_type == 'folder':
		for file in os.listdir(args.input_file):
			if(file[-3:].lower() == 'pdf'):
				print('Current converting file: ', file)
				filePath = args.input_file + '/' + file
				width, height, orientation = input_size_orientation(filePath)
				pocket_modder(filePath, width, height, orientation)
			else:
				print('{}  is not pdf thus will be skipped.'.format(file))
			print('-----------------------------------------------------')
		print('Conversion finished.\n')

	#single input file
	if file_type == 'pdf':
		width, height, orientation = input_size_orientation(args.input_file)
		pocket_modder(args.input_file, width, height, orientation)


if __name__ == '__main__':
	main()