#!/usr/local/bin/python

import re, os
import argparse

def parse_command( name, args ):
	print 'parse', name, args

	html = ''

	if name == 'documentclass':
		html += '<head>\n'
		html += '\t<meta charset="UTF-8" />\n'
		html += '\t<link rel="stylesheet" href="packages/' + name + '/' + args[ len( args ) - 1 ] + '.css" />\n'
	elif name == 'title':
		html += '\t<title>' + args[ len( args ) - 1 ] + '</title>\n'
	else:
		html += ' '.join( args )

	return html

def open_environment( name, args ):
	print 'open', name, args

	html = ''

	if name == 'document':
		html += '</head>\n'
		html += '<body>\n'
	else:
#		html += '<' + name + ' ' + ' '.join( args ) + '>'
		html += '<div class="' + name + '" ' + ' '.join( args ) + '>\n'

	return html

def close_environment( name, args ):
	print 'close', name, args

	html = ''

	if name == 'document':
		html += '</body>\n'
	else:
#		html += '</' + name + '>'
		html += '</div>\n'

	return html

def parse_math( math ):
	def get_math_mode( m ):
		if m in [ '+', '-', '*', '/', '=', '<', '>', '(', ')', '[', ']', '{', '}', ',' ]:
			return 'mo'
		elif m.isdigit() or m == '.':
			return 'mn'
		else:
			return 'mi'

	print math

	html = ''

	math_mode = 'mi'
	math_string = ''

	for m in math:
		if m.isspace():
			html += m
		elif m == '_':
#			html += '<msub>' +
			pass
		elif m == '^':
#			html += '<msub>' +
			pass
		else:
			new_math_mode = get_math_mode( m )

			if math_mode == new_math_mode and new_math_mode != 'mo':
				math_string += m
			else:
				html += '<' + math_mode + '>' + math_string + '</' + math_mode + '>'

				math_mode = new_math_mode
				math_string = m

	html += '<' + math_mode + '>' + math_string + '</' + math_mode + '>'

	return html

parser = argparse.ArgumentParser( prog = 'latex2html.py', description = 'Convert LaTeX documents to HTML.' )

parser.add_argument( 'target', help = 'LaTeX file to be converted' )
parser.add_argument( 'destination', nargs = '?', default = None, help = 'Destination of HTML output' )

args = parser.parse_args()

print args

target_path = os.path.dirname( args.target )
target_file = os.path.basename( args.target )

if args.destination == None:
	args.destination = target_path

html = '<!DOCTYPE html>\n<html>\n'

last_char = ''

current_modes = ['']
current_environments = ['']

with open( args.target ) as f:
	while True:
		c = f.read( 1 )

		print last_char
		print current_modes
		print current_environments
		print c

		mode = current_modes.pop()
		current_modes.append(mode)

		environment = current_environments.pop()
		current_environments.append(environment)

		if mode == 'command':
			if c.isspace() or c in ['#', '$', '%', '^', '&', '_', '}', '~', '\\'] or not c:
				if command_name == 'begin':
					# Get environment name
					new_environment = command_args.pop()

					# Enter environment
					current_environments.append( new_environment )

					# Open environment
					html += open_environment( new_environment, command_args )
				elif command_name == 'end':
					# Get environment name
					old_environment = command_args.pop()

					# Make sure the environment we want to close is actually open and available
					if environment == old_environment:
						# Close environment
						html += close_environment( old_environment, command_args )

						# Exit environment
						current_environments.pop()
					else:
						raise Error
				else:
					html += parse_command( command_name, command_args )

				# Exit command mode
				current_modes.pop()
			elif c == '{':
				# Enter argument mode
				current_modes.append('argument')

				argument_name = ''
			else:
				command_name += c
		elif mode == 'argument':
			if c == '}':
				command_args.append( argument_name )

				# Exit argument mode
				current_modes.pop()
			else:
				argument_name += c
		elif mode == 'math':
			if c == '$':
				html += parse_math( math )

				# Close math element
				html += '</math>'

				# Exit math mode
				current_modes.pop()
			else:
				math.append( c )
		elif mode == 'comment':
			if c == '\n':
				# Close comment
				html += ' -->\n'

				# Exit comment mode
				current_modes.pop()
			else:
				html += c
		else:
			if c == '\\':
				# Enter command mode
				current_modes.append('command')

				command_name = ''
				command_args = []
			elif c == '$':
				# Enter math mode
				current_modes.append('math')

				# Cancel last char
				last_char = ''

				math = []

				# Open comment
				html += '<math>'
			elif c == '%':
				# Enter comment mode
				current_modes.append('comment')

				# Open comment
				html += '<!-- '
			else:
				html += c

				if c == '\n' and environment == 'document' and last_char == '\n':
					html += '<p>'

				last_char = c

		# EOF
		if not c:
			html += '</html>'
			break

print html

html_file = open( args.destination + target_file + '.html', 'w' )

html_file.write( html )