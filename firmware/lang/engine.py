"""
Custom Language Engine
محرك اللغة المخصصة المبنية على Python
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import re

class TokenType(Enum):
    """أنواع الرموز"""
    # الحرفيات
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"
    
    # الكلمات المفتاحية
    IF = "IF"
    WHILE = "WHILE"
    FOR = "FOR"
    FUNC = "FUNC"
    RETURN = "RETURN"
    VAR = "VAR"
    CONST = "CONST"
    MOTOR = "MOTOR"
    SENSOR = "SENSOR"
    LED = "LED"
    
    # العمليات
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULT = "MULT"
    DIV = "DIV"
    MOD = "MOD"
    ASSIGN = "ASSIGN"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    LESS = "LESS"
    GREATER = "GREATER"
    
    # الفواصل
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    COLON = "COLON"
    
    # خاص
    EOF = "EOF"
    NEWLINE = "NEWLINE"

@dataclass
class Token:
    """رمز لغوي"""
    type: TokenType
    value: Any
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"

class Lexer:
    """محلل الرموز (Lexical Analyzer)"""
    
    KEYWORDS = {
        'if': TokenType.IF,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'func': TokenType.FUNC,
        'return': TokenType.RETURN,
        'var': TokenType.VAR,
        'const': TokenType.CONST,
        'motor': TokenType.MOTOR,
        'sensor': TokenType.SENSOR,
        'led': TokenType.LED,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """تحويل المصدر إلى رموز"""
        while self.pos < len(self.source):
            self._skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            # تخطي التعليقات
            if self.source[self.pos:self.pos+2] == '//':
                self._skip_line_comment()
                continue
            
            # الأرقام
            if self.source[self.pos].isdigit():
                self._read_number()
            # النصوص
            elif self.source[self.pos] == '"':
                self._read_string()
            # المعرفات والكلمات المفتاحية
            elif self.source[self.pos].isalpha() or self.source[self.pos] == '_':
                self._read_identifier()
            # العمليات والفواصل
            else:
                self._read_operator()
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
    
    def _current_char(self) -> Optional[str]:
        """الحرف الحالي"""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None
    
    def _peek(self, offset: int = 1) -> Optional[str]:
        """النظر للأمام"""
        if self.pos + offset < len(self.source):
            return self.source[self.pos + offset]
        return None
    
    def _advance(self):
        """التقدم للحرف التالي"""
        if self.pos < len(self.source) and self.source[self.pos] == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1
    
    def _skip_whitespace(self):
        """تخطي المسافات والجدولة"""
        while self._current_char() and self._current_char() in ' \t\n\r':
            self._advance()
    
    def _skip_line_comment(self):
        """تخطي تعليق السطر"""
        while self._current_char() and self._current_char() != '\n':
            self._advance()
    
    def _read_number(self):
        """قراءة رقم"""
        start_line, start_col = self.line, self.column
        num_str = ""
        
        while self._current_char() and (self._current_char().isdigit() or self._current_char() == '.'):
            num_str += self._current_char()
            self._advance()
        
        value = float(num_str) if '.' in num_str else int(num_str)
        self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_col))
    
    def _read_string(self):
        """قراءة نص"""
        start_line, start_col = self.line, self.column
        self._advance()  # تخطي الاقتباس الفاتح
        
        string_val = ""
        while self._current_char() and self._current_char() != '"':
            if self._current_char() == '\\':
                self._advance()
                if self._current_char() == 'n':
                    string_val += '\n'
                elif self._current_char() == 't':
                    string_val += '\t'
                else:
                    string_val += self._current_char()
            else:
                string_val += self._current_char()
            self._advance()
        
        self._advance()  # تخطي الاقتباس المغلق
        self.tokens.append(Token(TokenType.STRING, string_val, start_line, start_col))
    
    def _read_identifier(self):
        """قراءة معرف أو كلمة مفتاحية"""
        start_line, start_col = self.line, self.column
        identifier = ""
        
        while self._current_char() and (self._current_char().isalnum() or self._current_char() == '_'):
            identifier += self._current_char()
            self._advance()
        
        token_type = self.KEYWORDS.get(identifier, TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, identifier, start_line, start_col))
    
    def _read_operator(self):
        """قراءة عمليات وفواصل"""
        start_line, start_col = self.line, self.column
        char = self._current_char()
        
        # عمليات متعددة الأحرف
        if char == '=' and self._peek() == '=':
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.EQUAL, '==', start_line, start_col))
        elif char == '!' and self._peek() == '=':
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.NOT_EQUAL, '!=', start_line, start_col))
        elif char == '<' and self._peek() == '=':
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.LESS, '<=', start_line, start_col))
        elif char == '>' and self._peek() == '=':
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.GREATER, '>=', start_line, start_col))
        # عمليات فردية
        elif char == '+':
            self._advance()
            self.tokens.append(Token(TokenType.PLUS, '+', start_line, start_col))
        elif char == '-':
            self._advance()
            self.tokens.append(Token(TokenType.MINUS, '-', start_line, start_col))
        elif char == '*':
            self._advance()
            self.tokens.append(Token(TokenType.MULT, '*', start_line, start_col))
        elif char == '/':
            self._advance()
            self.tokens.append(Token(TokenType.DIV, '/', start_line, start_col))
        elif char == '%':
            self._advance()
            self.tokens.append(Token(TokenType.MOD, '%', start_line, start_col))
        elif char == '=':
            self._advance()
            self.tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_col))
        elif char == '<':
            self._advance()
            self.tokens.append(Token(TokenType.LESS, '<', start_line, start_col))
        elif char == '>':
            self._advance()
            self.tokens.append(Token(TokenType.GREATER, '>', start_line, start_col))
        elif char == '(':
            self._advance()
            self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
        elif char == ')':
            self._advance()
            self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
        elif char == '{':
            self._advance()
            self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
        elif char == '}':
            self._advance()
            self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
        elif char == '[':
            self._advance()
            self.tokens.append(Token(TokenType.LBRACKET, '[', start_line, start_col))
        elif char == ']':
            self._advance()
            self.tokens.append(Token(TokenType.RBRACKET, ']', start_line, start_col))
        elif char == ',':
            self._advance()
            self.tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
        elif char == ';':
            self._advance()
            self.tokens.append(Token(TokenType.SEMICOLON, ';', start_line, start_col))
        elif char == ':':
            self._advance()
            self.tokens.append(Token(TokenType.COLON, ':', start_line, start_col))
        else:
            # حرف غير معروف
            self._advance()

class Parser:
    """محلل بناء الجملة (Parser)"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> Dict[str, Any]:
        """تحليل البرنامج"""
        program = {
            "type": "program",
            "statements": []
        }
        
        while not self._is_at_end():
            stmt = self._parse_statement()
            if stmt:
                program["statements"].append(stmt)
        
        return program
    
    def _current_token(self) -> Token:
        """الرمز الحالي"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF
    
    def _peek(self, offset: int = 1) -> Token:
        """النظر للأمام"""
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return self.tokens[-1]
    
    def _advance(self) -> Token:
        """التقدم للرمز التالي"""
        current = self._current_token()
        if not self._is_at_end():
            self.pos += 1
        return current
    
    def _is_at_end(self) -> bool:
        """هل وصلنا للنهاية"""
        return self._current_token().type == TokenType.EOF
    
    def _expect(self, token_type: TokenType):
        """توقع رمز معين"""
        if self._current_token().type != token_type:
            raise SyntaxError(f"Expected {token_type.name}, got {self._current_token().type.name} "
                            f"at L{self._current_token().line}")
        self._advance()
    
    def _parse_statement(self) -> Optional[Dict]:
        """تحليل تصريح"""
        token = self._current_token()
        
        if token.type == TokenType.VAR:
            return self._parse_var_declaration()
        elif token.type == TokenType.IF:
            return self._parse_if_statement()
        elif token.type == TokenType.WHILE:
            return self._parse_while_loop()
        elif token.type == TokenType.FOR:
            return self._parse_for_loop()
        elif token.type == TokenType.FUNC:
            return self._parse_function_definition()
        elif token.type == TokenType.RETURN:
            return self._parse_return_statement()
        elif token.type == TokenType.IDENTIFIER:
            return self._parse_expression_statement()
        else:
            self._advance()
            return None
    
    def _parse_var_declaration(self) -> Dict:
        """var x = 10;"""
        self._expect(TokenType.VAR)
        name = self._current_token().value
        self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.ASSIGN)
        value = self._parse_expression()
        self._expect(TokenType.SEMICOLON)
        
        return {
            "type": "var_declaration",
            "name": name,
            "value": value
        }
    
    def _parse_if_statement(self) -> Dict:
        """if (condition) { ... }"""
        self._expect(TokenType.IF)
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        
        statements = []
        while self._current_token().type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        self._expect(TokenType.RBRACE)
        
        return {
            "type": "if_statement",
            "condition": condition,
            "body": statements
        }
    
    def _parse_while_loop(self) -> Dict:
        """while (condition) { ... }"""
        self._expect(TokenType.WHILE)
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        
        statements = []
        while self._current_token().type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        self._expect(TokenType.RBRACE)
        
        return {
            "type": "while_loop",
            "condition": condition,
            "body": statements
        }
    
    def _parse_for_loop(self) -> Dict:
        """for (init; cond; update) { ... }"""
        self._expect(TokenType.FOR)
        self._expect(TokenType.LPAREN)
        init = self._parse_statement()
        condition = self._parse_expression()
        self._expect(TokenType.SEMICOLON)
        update = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        
        statements = []
        while self._current_token().type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        self._expect(TokenType.RBRACE)
        
        return {
            "type": "for_loop",
            "init": init,
            "condition": condition,
            "update": update,
            "body": statements
        }
    
    def _parse_function_definition(self) -> Dict:
        """func name(args) { ... }"""
        self._expect(TokenType.FUNC)
        name = self._current_token().value
        self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN)
        
        args = []
        while self._current_token().type != TokenType.RPAREN:
            args.append(self._current_token().value)
            self._expect(TokenType.IDENTIFIER)
            if self._current_token().type == TokenType.COMMA:
                self._advance()
        
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        
        statements = []
        while self._current_token().type != TokenType.RBRACE:
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        self._expect(TokenType.RBRACE)
        
        return {
            "type": "function_definition",
            "name": name,
            "args": args,
            "body": statements
        }
    
    def _parse_return_statement(self) -> Dict:
        """return expr;"""
        self._expect(TokenType.RETURN)
        value = self._parse_expression()
        self._expect(TokenType.SEMICOLON)
        
        return {
            "type": "return_statement",
            "value": value
        }
    
    def _parse_expression_statement(self) -> Dict:
        """expr;"""
        expr = self._parse_expression()
        self._expect(TokenType.SEMICOLON)
        
        return {
            "type": "expression_statement",
            "expression": expr
        }
    
    def _parse_expression(self) -> Dict:
        """تحليل تعبير"""
        return self._parse_assignment()
    
    def _parse_assignment(self) -> Dict:
        """x = 10"""
        left = self._parse_equality()
        
        if self._current_token().type == TokenType.ASSIGN:
            self._advance()
            right = self._parse_assignment()
            return {
                "type": "assignment",
                "left": left,
                "right": right
            }
        
        return left
    
    def _parse_equality(self) -> Dict:
        """== !="""
        left = self._parse_comparison()
        
        while self._current_token().type in [TokenType.EQUAL, TokenType.NOT_EQUAL]:
            op = self._current_token().value
            self._advance()
            right = self._parse_comparison()
            left = {
                "type": "binary_op",
                "op": op,
                "left": left,
                "right": right
            }
        
        return left
    
    def _parse_comparison(self) -> Dict:
        """< > <= >="""
        left = self._parse_additive()
        
        while self._current_token().type in [TokenType.LESS, TokenType.GREATER]:
            op = self._current_token().value
            self._advance()
            right = self._parse_additive()
            left = {
                "type": "binary_op",
                "op": op,
                "left": left,
                "right": right
            }
        
        return left
    
    def _parse_additive(self) -> Dict:
        """+ -"""
        left = self._parse_multiplicative()
        
        while self._current_token().type in [TokenType.PLUS, TokenType.MINUS]:
            op = self._current_token().value
            self._advance()
            right = self._parse_multiplicative()
            left = {
                "type": "binary_op",
                "op": op,
                "left": left,
                "right": right
            }
        
        return left
    
    def _parse_multiplicative(self) -> Dict:
        """* / %"""
        left = self._parse_unary()
        
        while self._current_token().type in [TokenType.MULT, TokenType.DIV, TokenType.MOD]:
            op = self._current_token().value
            self._advance()
            right = self._parse_unary()
            left = {
                "type": "binary_op",
                "op": op,
                "left": left,
                "right": right
            }
        
        return left
    
    def _parse_unary(self) -> Dict:
        """- +"""
        left = self._parse_postfix()
        return left
    
    def _parse_postfix(self) -> Dict:
        """func() arr[]"""
        left = self._parse_primary()
        
        while True:
            if self._current_token().type == TokenType.LPAREN:
                # دالة
                self._advance()
                args = []
                while self._current_token().type != TokenType.RPAREN:
                    args.append(self._parse_expression())
                    if self._current_token().type == TokenType.COMMA:
                        self._advance()
                self._expect(TokenType.RPAREN)
                left = {
                    "type": "function_call",
                    "function": left,
                    "args": args
                }
            elif self._current_token().type == TokenType.LBRACKET:
                # مصفوفة
                self._advance()
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET)
                left = {
                    "type": "array_access",
                    "array": left,
                    "index": index
                }
            else:
                break
        
        return left
    
    def _parse_primary(self) -> Dict:
        """أساسي"""
        token = self._current_token()
        
        if token.type == TokenType.NUMBER:
            self._advance()
            return {
                "type": "literal",
                "value": token.value
            }
        elif token.type == TokenType.STRING:
            self._advance()
            return {
                "type": "literal",
                "value": token.value
            }
        elif token.type == TokenType.IDENTIFIER:
            self._advance()
            return {
                "type": "identifier",
                "name": token.value
            }
        elif token.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr
        else:
            raise SyntaxError(f"Unexpected token: {token}")

class LanguageEngine:
    """محرك اللغة المخصصة"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, Dict] = {}
    
    def compile(self, source: str) -> Dict:
        """تجميع المصدر"""
        # المرحلة 1: التحليل اللغوي
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # المرحلة 2: التحليل النحوي
        parser = Parser(tokens)
        ast = parser.parse()
        
        return ast
    
    def execute(self, ast: Dict):
        """تنفيذ الشفرة المترجمة"""
        for statement in ast.get("statements", []):
            self._execute_statement(statement)
    
    def _execute_statement(self, stmt: Dict):
        """تنفيذ تصريح"""
        stmt_type = stmt.get("type")
        
        if stmt_type == "var_declaration":
            name = stmt["name"]
            value = self._evaluate_expression(stmt["value"])
            self.variables[name] = value
            print(f"[LANG] var {name} = {value}")
        
        elif stmt_type == "if_statement":
            condition = self._evaluate_expression(stmt["condition"])
            if condition:
                for s in stmt["body"]:
                    self._execute_statement(s)
        
        elif stmt_type == "while_loop":
            while self._evaluate_expression(stmt["condition"]):
                for s in stmt["body"]:
                    self._execute_statement(s)
        
        elif stmt_type == "for_loop":
            if stmt["init"]:
                self._execute_statement(stmt["init"])
            while self._evaluate_expression(stmt["condition"]):
                for s in stmt["body"]:
                    self._execute_statement(s)
                self._evaluate_expression(stmt["update"])
        
        elif stmt_type == "function_definition":
            name = stmt["name"]
            self.functions[name] = stmt
            print(f"[LANG] func {name}() defined")
        
        elif stmt_type == "expression_statement":
            self._evaluate_expression(stmt["expression"])
    
    def _evaluate_expression(self, expr: Dict) -> Any:
        """تقييم تعبير"""
        expr_type = expr.get("type")
        
        if expr_type == "literal":
            return expr["value"]
        
        elif expr_type == "identifier":
            return self.variables.get(expr["name"], 0)
        
        elif expr_type == "binary_op":
            left = self._evaluate_expression(expr["left"])
            right = self._evaluate_expression(expr["right"])
            op = expr["op"]
            
            if op == "+": return left + right
            elif op == "-": return left - right
            elif op == "*": return left * right
            elif op == "/": return left / right
            elif op == "%": return left % right
            elif op == "==": return left == right
            elif op == "!=": return left != right
            elif op == "<": return left < right
            elif op == ">": return left > right
            elif op == "<=": return left <= right
            elif op == ">=": return left >= right
        
        elif expr_type == "assignment":
            left_name = expr["left"]["name"]
            value = self._evaluate_expression(expr["right"])
            self.variables[left_name] = value
            return value
        
        elif expr_type == "function_call":
            func_name = expr["function"]["name"]
            args = [self._evaluate_expression(arg) for arg in expr.get("args", [])]
            
            # دوال مدمجة
            if func_name == "print":
                print(*args)
            elif func_name == "delay":
                import time
                time.sleep(args[0] / 1000)  # تحويل من ms إلى s
            
            return None
        
        return None
