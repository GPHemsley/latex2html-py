#!/usr/local/bin/python

import re, os
import argparse

class LaTeX_Parser:
	tokens = []

	def tokenize( self, args ):
		with open( args.target ) as f:
			chars = list( f.read() )

		prev_state = []
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
				self.tokens.append( { 'state': prev_state[-1], 'text': text } )
				text = ''

				if curr_char == '\n':
					self.tokens.append( { 'state': curr_state } )
				else:
					text += curr_char

				curr_state = prev_state.pop()
			elif curr_state == 'comment':
				if curr_char == '\n' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					curr_state = prev_state.pop()
				else:
					text += curr_char
			elif curr_state == 'math':
				if curr_char == '$' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					curr_state = prev_state.pop()
				else:
					text += curr_char
			elif curr_state == 'command-begin':
				command += curr_char

				if re.match( '[a-z]', curr_char, re.I ):
					curr_state = 'command-internal'
				else:
					self.tokens.append( { 'state': 'command', 'command': command, 'args': command_args } )
					command = None
					command_args = None
					curr_state = prev_state.pop()
			elif curr_state == 'command-internal':
				if curr_char == '\\':
					self.tokens.append( { 'state': 'command', 'command': command, 'args': command_args } )
					command = ''
					command_args = []
					curr_state = 'command-begin'
				elif curr_char == '[':
					curr_state = 'command-arg-square'
					square_bracket_count = 1
					curly_bracket_count = 0
				elif curr_char == '{':
					curr_state = 'command-arg-curly'
					square_bracket_count = 0
					curly_bracket_count = 1
				else:
					command += curr_char

					if not re.match( '[a-z{\\[]', next_char, re.I ):
						self.tokens.append( { 'state': 'command', 'command': command, 'args': command_args } )
						command = None
						command_args = None
						curr_state = prev_state.pop()
			elif curr_state in [ 'command-arg-square', 'command-arg-curly' ]:
				if prev_char != '\\':
					if curr_char == '[':
						square_bracket_count += 1
					elif curr_char == ']':
						square_bracket_count -= 1
					elif curr_char == '{':
						curly_bracket_count += 1
					elif curr_char == '}':
						curly_bracket_count -= 1

				if ( curr_state == 'command-arg-square' and square_bracket_count == 0 ) or ( curr_state == 'command-arg-curly' and curly_bracket_count == 0 ):
					type = 'square' if curr_state == 'command-arg-square' else 'curly'

					command_args.append( { 'type': type, 'text': text } )

					text = ''

					if next_char not in [ '\\', '[', '{' ]:
						self.tokens.append( { 'state': 'command', 'command': command, 'args': command_args } )
						command = None
						command_args = None
						curr_state = prev_state.pop()
					else:
						curr_state = 'command-internal'
				else:
					text += curr_char
			else:
				if curr_char == '%' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					prev_state.append( curr_state )
					curr_state = 'comment'
				elif curr_char == '$' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					prev_state.append( curr_state )
					curr_state = 'math'
				elif curr_char == '\\' and prev_char != '\\':
					self.tokens.append( { 'state': curr_state, 'text': text } )
					text = ''
					command = ''
					command_args = []
					prev_state.append( curr_state )
					curr_state = 'command-begin'
				elif curr_char == '\n' and prev_char != '\\' and next_char == '\n':
					prev_state.append( curr_state )
					curr_state = 'blank'
				else:
					text += curr_char
		else:
			# Flush the last chunk of stored information
			if curr_state == 'command-internal':
				self.tokens.append( { 'state': 'command', 'command': command, 'args': command_args } )
				command = None
				command_args = None
			else:
				self.tokens.append( { 'state': curr_state, 'text': text } )

			text = ''

		return self.tokens

	def output_HTML( self, tokens ):
		html = '<!DOCTYPE html>\n<html>\n'

		title = ''
		packages = []
		in_document = False

		for i, token in enumerate( tokens ):
			if token['state'] == 'comment':
				comment = '<!--'

				if len( token['text'] ) > 0:
					if token['text'][0] != ' ':
						comment += ' '

					comment += token['text']

					if token['text'][-1] != ' ':
						comment += ' '
				else:
					comment += ' '

				comment += '-->\n'

				html += comment
			else:
				if in_document:
					if token['state'] == 'command':
						try:
							last_arg = token['args'][-1]
						except:
#							print token
							last_arg = None

						if token['command'] == 'end' and last_arg['text'] == 'document':
							in_document = False
							html += '</body>\n'
						else:
							html += '<span class="command-' + token['command'] + '">' + token['command'] + '</span>'

							for arg in token['args']:
								html += '<span class="argument-' + arg['type'] + '">' + arg['text'] + '</span>'
					elif token['state'] == 'math':
						html += '<math>' + token['text'] + '</math>'
					elif token['state'] == 'default':
						if tokens[i-1]['state'] == 'blank' or ( tokens[i-1]['state'] == 'command' and tokens[i-1]['command'] == 'begin' and tokens[i-1]['args'][-1]['text'] == 'document' ):
							html += '\t<p>'

						html += token['text']

						if tokens[i+1]['state'] == 'blank' or ( tokens[i+1]['state'] == 'command' and tokens[i+1]['command'] == 'end' and tokens[i+1]['args'][-1]['text'] == 'document' ):
							html += '</p>\n'
					else:
						if 'text' in token:
							html += token['text']
				else:
					if token['state'] == 'command':
						try:
							last_arg = token['args'][-1]
						except:
#							print token
							last_arg = None

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
	target_path = '.' if target_path == '' else target_path
	args.destination = target_path + '/'

parser = LaTeX_Parser()

tokens = parser.tokenize( args )

print tokens

html = parser.output_HTML( tokens )

print html

html_file = open( args.destination + target_file + '.html', 'w' )

html_file.write( html )
