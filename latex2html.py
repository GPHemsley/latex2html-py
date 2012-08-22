#!/usr/local/bin/python

import re, os
import argparse

class LaTeX_Parser:
	tokens = []

	def tokenize( self, args ):
		with open( args.target ) as f:
			chars = list( f.read() )

		prev_state = None
		curr_state = 'default'
		text = ''
		command = command_args = None

		for i, curr_char in enumerate( chars ):
			prev_char = None if ( i - 1 ) < 0 else chars[i-1]
			next_char = None if ( i + 1 ) >= len( chars ) else chars[i+1]

#			print prev_state, curr_state
#			print curr_char
#			print command, command_args

			if curr_state == 'blank':
				if curr_char == '\n':
					if text != '':
						self.tokens.append( { 'state': prev_state, 'text': text } )
						text = ''
				else:
					text += curr_char

				curr_state = prev_state
				prev_state = None
			elif curr_state == 'comment':
				if curr_char == '\n' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					curr_state = prev_state
					prev_state = None
				else:
					text += curr_char
			elif curr_state == 'math':
				if curr_char == '$' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					curr_state = prev_state
					prev_state = None
				else:
					text += curr_char
			elif curr_state in [ 'command-begin', 'command-arg-square', 'command-arg-curly', 'command-end' ]:
				if curr_state == 'command-begin' and curr_char in [ ' ', '\n' ]:
					self.tokens.append( { 'state': 'command', 'command': command, 'args': [] } )
					text = ''
					command = None
					command_args = None
					curr_state = prev_state
					prev_state = None
				elif curr_state in [ 'command-begin', 'command-end' ] and curr_char == '[' and prev_char != '\\':
					curr_state = 'command-arg-square'
				elif curr_state in [ 'command-begin', 'command-end' ] and curr_char == '{' and prev_char != '\\':
					curr_state = 'command-arg-curly'
				elif curr_state in [ 'command-arg-square', 'command-arg-curly' ]:
					if ( ( curr_state == 'command-arg-square' and curr_char == ']' ) or ( curr_state == 'command-arg-curly' and curr_char == '}' ) ) and prev_char != '\\':
						type = 'square' if curr_state == 'command-arg-square' else 'curly'

						command_args.append( { 'type': type, 'text': text } )

						text = ''

						if next_char not in [ '[', '{' ]:
							self.tokens.append( { 'state': 'command', 'command': command, 'args': command_args } )
							command = None
							command_args = None
							curr_state = prev_state
							prev_state = None
						else:
							curr_state = 'command-end'
					else:
						text += curr_char
				else:
					command += curr_char
			else:
				if curr_char == '%' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					prev_state = curr_state
					curr_state = 'comment'
				elif curr_char == '$' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					prev_state = curr_state
					curr_state = 'math'
				elif curr_char == '\\' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					command = ''
					command_args = []
					prev_state = curr_state
					curr_state = 'command-begin'
				elif curr_char == '\n' and prev_char != '\\':
					prev_state = curr_state
					curr_state = 'blank'
				else:
					text += curr_char
		else:
			# Flush the last chunk of stored information
			if curr_state == 'command-end':
				self.tokens.append( { 'state': 'command', 'command': command, 'args': command_args } )
				command = None
				command_args = None
			else:
				self.tokens.append( { 'state': curr_state, 'text': text } )

			text = ''
			curr_state = prev_state
			prev_state = None

		return self.tokens

	def output_HTML( self, tokens ):
		html = '<!DOCTYPE html>\n<html>\n'

		title = ''
		packages = []
		in_document = False

		for i, token in enumerate( tokens ):
			if token['state'] == 'comment':
				comment = '\t<!--'

				if token['text'][0] != ' ':
					comment += ' '

				comment += token['text']

				if token['text'][len( token['text'] ) - 1] != ' ':
					comment += ' '

				comment += '-->\n'

				html += comment
			else:
				if in_document:
					if token['state'] == 'command':
						last_arg = token['args'].pop()

						if token['command'] == 'end' and last_arg['text'] == 'document':
							in_document = False
							html += '</body>\n'
						else:
							print token['command']
#							html += '<' + token['command'] + '>'
#							html += token['args'].join()
#							html += '</' + token['command'] + '>\n'
					elif token['state'] == 'math':
						html += '\t<math>' + token['text'] + '</math>\n'
					elif token['state'] == 'default':
						if token['text'] == '' and tokens[i-1]['state'] != 'default':
							html += '\n'
						else:
							html += '\t<p>' + token['text'] + '</p>\n'
					else:
						if 'text' in token:
							html += token['text']
				else:
					if token['state'] == 'command':
						last_arg = token['args'].pop()

						if token['command'] == 'documentclass':
							pass
						elif token['command'] == 'title':
							title = last_arg['text']
						elif token['command'] == 'usepackage':
							pass
						elif token['command'] == 'begin' and last_arg['text'] == 'document':
							html += '<head>\n\t<meta charset="UTF-8" />\n'
							html += '\t<title>' + title + '</title>\n'

							for pkg in packages:
								html += '\t<link rel="stylesheet" href="packages/' + pkg['name'] + '" />'

							html += '</head>\n'

							in_document = True
							html += '<body>\n'

		html += '</html>\n'

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

parser = LaTeX_Parser()

tokens = parser.tokenize( args )

print tokens

html = parser.output_HTML( tokens )

print html

html_file = open( args.destination + target_file + '.html', 'w' )

html_file.write( html )
