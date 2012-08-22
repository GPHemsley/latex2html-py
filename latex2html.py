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

			if curr_state == 'comment':
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
		pass

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