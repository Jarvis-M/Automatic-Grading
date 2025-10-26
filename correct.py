import re
import os
from collections import defaultdict
import Levenshtein
import logging
from typing import List, Tuple, Dict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedCppOCRCorrector:
    def __init__(self):
        # C++ 关键词词典（扩展版）
        self.cpp_keywords = {
            'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor',
            'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t',
            'class', 'compl', 'concept', 'const', 'consteval', 'constexpr', 'const_cast',
            'continue', 'co_await', 'co_return', 'co_yield', 'decltype', 'default',
            'delete', 'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit',
            'export', 'extern', 'false', 'float', 'for', 'friend', 'goto', 'if',
            'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not',
            'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 'private', 'protected',
            'public', 'register', 'reinterpret_cast', 'requires', 'return', 'short',
            'signed', 'sizeof', 'static', 'static_assert', 'static_cast', 'struct',
            'switch', 'template', 'this', 'thread_local', 'throw', 'true', 'try',
            'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using', 'virtual',
            'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq', 'main', 'include'
        }

        # 不需要分号的语句开头关键词
        self.no_semicolon_starts = {
            '#', 'for', 'if', 'while', 'switch', 'else', 'struct', 'class',
            'namespace', 'public', 'private', 'protected', 'try', 'catch'
        }

        # 不需要分号的语句结尾关键词
        self.no_semicolon_ends = {
            '{', '}', '//', '/*'
        }

        # C++ 标准库常见标识符（扩展版）
        self.cpp_std_lib = {
            'cout', 'cin', 'cerr', 'clog', 'endl', 'string', 'vector', 'list', 'map',
            'set', 'unordered_map', 'unordered_set', 'array', 'tuple', 'pair', 'make_pair',
            'shared_ptr', 'unique_ptr', 'weak_ptr', 'move', 'forward', 'initializer_list',
            'iostream', 'fstream', 'sstream', 'algorithm', 'functional', 'iterator',
            'numeric', 'memory', 'stdexcept', 'type_traits', 'utility', 'std'
        }

        # 高置信度字符映射（强制纠正）- 增强流符号相关
        self.high_confidence_corrections = {
            '《': '<<',  # 中文全角书名号→C++流输出运算符
            '》': '>>',  # 中文全角书名号→C++流输入运算符
            '〈': '<<',  # 中文单角书名号→C++流输出运算符
            '〉': '>>',  # 中文单角书名号→C++流输入运算符
            '＜': '<',  # 中文全角小于号→半角小于号
            '＞': '>',  # 中文全角大于号→半角大于号
            '1': 'i',  # 数字1 -> 字母i
            '0': 'o',  # 数字0 -> 字母o
            '5': 's',  # 数字5 -> 字母s
            'l': '1',  # 字母l -> 数字1（在数字上下文中）
            'O': '0',  # 字母O -> 数字0
            'o': '0',  # 字母o -> 数字0（在数字上下文中）
            ':': ';',  # 冒号 -> 分号（在某些上下文中）
            '：': ';',  # 中文全角冒号 -> 分号
            '<': '<',  # 保留左尖括号（用于头文件校验）
            '>': '>',  # 保留右尖括号（用于头文件校验）
        }

        # 常见OCR错误模式（增强流符号相关错误）
        self.common_ocr_errors = {
            '1nclude': 'include',
            'ma1n': 'main',
            'c0ut': 'cout',
            'c1n': 'cin',
            'end1': 'endl',
            'str1ng': 'string',
            'vect0r': 'vector',
            '1nt': 'int',
            'f0r': 'for',
            '1f': 'if',
            'v0id': 'void',
            'retrn': 'return',
            'c1ass': 'class',
            'namespce': 'namespace',
            'publ1c': 'public',
            'pr1vate': 'private',
            'd0uble': 'double',
            'd0ub1e': 'double',
            'doub1e': 'double',
            'bo0l': 'bool',
            'ch0r': 'char',
            '10stream': 'iostream',
            's1ze': 'size',
            'display1nf0': 'displayInfo',
            'setName': 'setName',
            'setAge': 'setAge',
            # 流符号相关错误模式
            'cout《': 'cout<<',
            'cout<': 'cout<<',
            'cout<<<': 'cout<<',
            'cout>>': 'cout>>',
            'cin>>': 'cin>>',
            'cin《': 'cin>>',
            'cin>': 'cin>>',
            'cerr《': 'cerr<<',
            'clog《': 'clog<<',
            'endl《': 'endl<<',
            '< endl': '<<endl',
            'std《': 'std::',
            # 混合流符号错误模式
            '<《': '<<',
            '《<': '<<',
            '>》': '>>',
            '》>': '>>',
            '《《': '<<',
            '》》': '>>',
            '<<<': '<<',
            '>>>': '>>',
            # 头文件相关错误模式
            '#include iostream': '#include <iostream>',
            '#include "iostream"': '#include <iostream>',
            '#include <iostream': '#include <iostream>',
            '#include iostream>': '#include <iostream>',
            '#include [iostream]': '#include <iostream>',
            '#include {iostream}': '#include <iostream>',
        }

        # C++ 标准头文件列表
        self.standard_headers = {
            'iostream', 'fstream', 'sstream', 'string', 'vector', 'list', 'map', 'set',
            'unordered_map', 'unordered_set', 'array', 'tuple', 'algorithm', 'functional',
            'iterator', 'numeric', 'memory', 'stdexcept', 'type_traits', 'utility',
            'cstdio', 'cstdlib', 'cstring', 'cmath', 'ctime', 'cwchar', 'bitset', 'deque',
            'forward_list', 'initializer_list', 'limits', 'locale', 'queue', 'stack',
            'valarray', 'atomic', 'condition_variable', 'future', 'mutex', 'thread'
        }

        # 流操作符相关标识符
        self.stream_identifiers = {'cout', 'cin', 'cerr', 'clog', 'endl', 'std'}

        # 构建所有有效词的集合
        self.valid_words = self.cpp_keywords.union(self.cpp_std_lib).union(self.standard_headers)

        # 编译正则模式（增强流符号相关模式）
        self.preprocessor_pattern = re.compile(r'^\s*#\s*(\w+)')
        self.include_pattern = re.compile(
            r'#\s*include\s*([<"\[{(]?)\s*([\w/\.]+)\s*([>"\]}]?)',
            re.IGNORECASE
        )
        self.string_pattern = re.compile(r'"[^"]*"')
        self.comment_pattern = re.compile(r'//.*?$|/\*.*?\*/', re.DOTALL | re.MULTILINE)

        # 增强流操作符模式识别
        self.stream_operator_pattern = re.compile(
            r'(\b(cout|cin|cerr|clog|endl|std)\b\s*[《〈＜<]+\s*)|'
            r'([》〉＞>]+\s*\b(cout|cin|cerr|clog|endl|std)\b)|'
            r'(\b(cout|cin|cerr|clog|endl|std)\b\s*[》〉＞>]+\s*)|'
            r'([《〈＜<]+\s*\b(cout|cin|cerr|clog|endl|std)\b)',
            re.IGNORECASE
        )

        # 混合流符号模式
        self.mixed_stream_pattern = re.compile(
            r'<《|《<|>》|》>|[《〈＜]{2,}|[》〉＞]{2,}|<<<|>>>',
            re.IGNORECASE
        )

    def preprocess_text(self, text: str) -> str:
        """预处理文本"""
        text = text.replace('\ufeff', '')  # 移除BOM字符
        text = text.replace('\r\n', '\n').replace('\r', '\n')  # 标准化行尾符
        return text

    def aggressive_char_correction(self, text: str) -> str:
        """激进字符级纠错（增强流符号处理）"""
        lines = text.split('\n')
        corrected_lines = []

        for line_num, line in enumerate(lines, 1):
            # 首先处理混合流符号错误
            line = self.fix_mixed_stream_symbols(line)

            # 扩展字符提取：包含流符号相关字符
            words = re.findall(r'\b\w+\b|[^\w\s《》〈〉＜＞<>"\[\]{}()]|《|》|〈|〉|＜|＞|<|>|"|\[|\]|\{|\}|\(|\)', line)
            word_positions = []
            pos = 0

            # 找到每个单词/符号的位置
            for word in words:
                start = line.find(word, pos)
                if start == -1:
                    continue
                end = start + len(word)
                word_positions.append((word, start, end))
                pos = end

            # 处理每个单词/符号
            corrected_chars = list(line)
            for word, start, end in word_positions:
                # 跳过注释和字符串中的内容
                if self.is_in_comment_or_string(line, start):
                    continue

                # 处理常见错误模式
                if word in self.common_ocr_errors:
                    correction = self.common_ocr_errors[word]
                    for i, (orig_char, corr_char) in enumerate(zip(word, correction)):
                        if orig_char != corr_char:
                            pos = start + i
                            if pos < len(corrected_chars):
                                corrected_chars[pos] = corr_char
                    continue

                # 专门处理流符号错误
                if word in ['《', '〈', '＜']:
                    if not self.is_in_comment_or_string(line, start):
                        # 检查上下文确定是输出流还是输入流
                        context_before = line[max(0, start - 10):start].lower()

                        is_input_stream = any(keyword in context_before for keyword in ['cin', '>>'])
                        is_output_stream = any(
                            keyword in context_before for keyword in ['cout', 'cerr', 'clog', 'endl', '<<'])

                        if is_input_stream or ('cin' in context_before and not is_output_stream):
                            # 输入流上下文，纠正为>>
                            if start < len(corrected_chars):
                                corrected_chars[start] = '>'
                                corrected_chars.insert(start + 1, '>')
                        else:
                            # 默认输出流上下文，纠正为<<
                            if start < len(corrected_chars):
                                corrected_chars[start] = '<'
                                corrected_chars.insert(start + 1, '<')
                    continue

                elif word in ['》', '〉', '＞']:
                    if not self.is_in_comment_or_string(line, start):
                        # 检查上下文
                        context_after = line[end:min(len(line), end + 5)].lower()

                        is_input_stream = any(keyword in context_after for keyword in ['cin', '>>'])
                        is_output_stream = any(
                            keyword in context_after for keyword in ['cout', 'cerr', 'clog', 'endl', '<<'])

                        if is_input_stream or ('cin' in context_after and not is_output_stream):
                            # 输入流上下文，纠正为>>
                            if start < len(corrected_chars):
                                corrected_chars[start] = '>'
                                corrected_chars.insert(start + 1, '>')
                        else:
                            # 默认输出流上下文，纠正为<<
                            if start < len(corrected_chars):
                                corrected_chars[start] = '<'
                                corrected_chars.insert(start + 1, '<')
                    continue

                # 处理头文件相关符号错误
                if word in ['<', '>']:
                    if 'include' in line[:start].lower():
                        context = self.get_char_context(line, start, window_size=10)
                        if '<' in context and 'include' in context.lower():
                            continue

                # 其他高置信度纠正
                for i, char in enumerate(word):
                    if char in self.high_confidence_corrections and char not in ['《', '》', '〈', '〉', '＜', '＞']:
                        pos = start + i
                        if pos < len(corrected_chars):
                            correction = self.high_confidence_corrections[char]
                            context = self.get_char_context(line, pos)
                            if self.should_apply_correction(char, correction, context):
                                corrected_chars[pos] = correction

            corrected_line = ''.join(corrected_chars)
            corrected_lines.append(corrected_line)

        return '\n'.join(corrected_lines)

    def fix_mixed_stream_symbols(self, line: str) -> str:
        """修复混合流符号错误"""
        # 定义混合符号纠正规则
        mixed_corrections = {
            '<《': '<<',  # 半角+全角混合
            '《<': '<<',  # 全角+半角混合
            '>》': '>>',  # 半角+全角混合
            '》>': '>>',  # 全角+半角混合
            '《《': '<<',  # 双全角
            '》》': '>>',  # 双全角
            '<<<': '<<',  # 三半角
            '>>>': '>>',  # 三半角
            '《〉': '<<',  # 不同全角混合
            '〈》': '<<',  # 不同全角混合
            '>〉': '>>',  # 半角+全角混合
            '》>': '>>',  # 全角+半角混合
        }

        # 应用混合符号纠正
        for wrong_pattern, correct_pattern in mixed_corrections.items():
            if wrong_pattern in line:
                # 检查是否在注释或字符串中
                positions = []
                start = 0
                while True:
                    pos = line.find(wrong_pattern, start)
                    if pos == -1:
                        break
                    if not self.is_in_comment_or_string(line, pos):
                        positions.append(pos)
                    start = pos + 1

                # 从后往前替换以避免位置变化
                for pos in sorted(positions, reverse=True):
                    line = line[:pos] + correct_pattern + line[pos + len(wrong_pattern):]

        return line

    def is_in_comment_or_string(self, line: str, position: int) -> bool:
        """检查位置是否在注释或字符串中"""
        # 检查单行注释
        if '//' in line:
            comment_start = line.find('//')
            if position >= comment_start:
                return True

        # 检查字符串
        for match in self.string_pattern.finditer(line):
            if match.start() <= position < match.end():
                return True

        # 检查块注释
        if '/*' in line and '*/' in line:
            comment_start = line.find('/*')
            comment_end = line.find('*/')
            if comment_start <= position <= comment_end:
                return True

        return False

    def get_char_context(self, text: str, position: int, window_size: int = 3) -> str:
        """获取字符上下文"""
        start = max(0, position - window_size)
        end = min(len(text), position + window_size + 1)
        return text[start:end]

    def should_apply_correction(self, original: str, correction: str, context: str) -> bool:
        """决定是否应用纠正"""
        # 如果original是数字，correction是字母，检查上下文是否有字母
        if original.isdigit() and correction.isalpha():
            return any(c.isalpha() for c in context)

        # 如果original是字母，correction是数字，检查上下文是否有数字
        if original.isalpha() and correction.isdigit():
            return any(c.isdigit() for c in context)

        # 针对流运算符的额外判断
        if original in ['《', '〈', '＜'] and correction == '<<':
            return any(keyword in context.lower() for keyword in ['cout', 'cerr', 'clog', 'endl'])

        # 针对头文件分隔符的判断
        if original in ['[', '{', '('] and correction == '<':
            return 'include' in context.lower()

        return True

    def token_based_correction(self, text: str) -> str:
        """基于令牌的智能纠错（增强流符号处理）"""
        lines = text.split('\n')
        corrected_lines = []

        for line_num, line in enumerate(lines, 1):
            # 首先处理混合流符号
            line = self.fix_mixed_stream_symbols(line)

            # 跳过注释但不跳过预处理指令
            if '//' in line or '/*' in line:
                comment_pos = min(line.find('//'), line.find('/*')) if '//' in line and '/*' in line else \
                    line.find('//') if '//' in line else line.find('/*')
                line_content = line[:comment_pos]
            else:
                line_content = line

            # 提取令牌（增强流操作符识别）
            tokens = re.findall(r'\b\w+\b|[^\w\s]|<<|>>|《|》|〈|〉|＜|＞', line_content)
            token_positions = []
            pos = 0

            for token in tokens:
                start = line_content.find(token, pos)
                if start == -1:
                    continue
                end = start + len(token)
                token_positions.append((token, start, end))
                pos = end

            # 纠正令牌
            corrected_chars = list(line)
            for token, start, end in token_positions:
                if len(token) <= 1:
                    continue

                # 专门处理流操作符相关令牌
                if token in ['cout<', 'cerr<', 'clog<', 'cin>']:
                    if token.endswith('<'):
                        correction = token + '<'
                    else:  # cin>
                        correction = token + '>'

                    for i, (orig_char, corr_char) in enumerate(zip(token, correction)):
                        if i < len(token) and orig_char != corr_char and (start + i) < len(corrected_chars):
                            pos = start + i
                            corrected_chars[pos] = corr_char
                    continue

                # 处理不完整的流操作符
                if token in ['cout<<<', 'cin>>>', 'cerr<<<', 'clog<<<']:
                    if token.startswith('cout') or token.startswith('cerr') or token.startswith('clog'):
                        correction = token[:4] + '<<'
                    else:  # cin
                        correction = token[:3] + '>>'

                    # 替换整个令牌
                    corrected_segment = list(corrected_chars[start:end])
                    for i in range(len(correction)):
                        if i < len(corrected_segment):
                            corrected_segment[i] = correction[i]
                        else:
                            corrected_segment.append(correction[i])

                    # 如果新令牌更短，需要删除多余字符
                    if len(correction) < len(corrected_segment):
                        corrected_segment = corrected_segment[:len(correction)]

                    corrected_chars[start:end] = corrected_segment
                    continue

                # 检查头文件名称是否正确
                if 'include' in line_content[:start].lower():
                    if token in self.standard_headers:
                        continue
                    else:
                        suggestions = self.get_header_suggestions(token)
                        if suggestions:
                            best_suggestion, confidence = suggestions[0]
                            if confidence > 0.7:
                                for i in range(min(len(token), len(best_suggestion))):
                                    if token[i] != best_suggestion[i] and (start + i) < len(corrected_chars):
                                        pos_in_line = start + i
                                        corrected_chars[pos_in_line] = best_suggestion[i]
                                if len(best_suggestion) > len(token):
                                    for i in range(len(token), len(best_suggestion)):
                                        pos_in_line = start + i
                                        corrected_chars.insert(pos_in_line, best_suggestion[i])
                        continue

                # 原有令牌有效性检查
                if not self.is_valid_token(token):
                    suggestions = self.get_best_suggestions(token)
                    if suggestions:
                        best_suggestion, confidence = suggestions[0]
                        if confidence > 0.7:
                            for i, (orig_char, corr_char) in enumerate(zip(token, best_suggestion)):
                                if i < len(best_suggestion) and orig_char != corr_char and (start + i) < len(
                                        corrected_chars):
                                    pos = start + i
                                    corrected_chars[pos] = corr_char

            corrected_line = ''.join(corrected_chars)
            corrected_lines.append(corrected_line)

        return '\n'.join(corrected_lines)

    def get_header_suggestions(self, token: str, max_suggestions: int = 3) -> List[Tuple[str, float]]:
        """获取头文件名称的最佳建议"""
        suggestions = []
        for header in self.standard_headers:
            if abs(len(header) - len(token)) > 3:
                continue

            distance = Levenshtein.distance(token, header)
            max_len = max(len(token), len(header))
            similarity = 1 - (distance / max_len)

            if header.startswith(token[:2]) or header.endswith(token[-2:]):
                similarity += 0.15

            suggestions.append((header, similarity))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:max_suggestions]

    def is_valid_token(self, token: str) -> bool:
        """检查令牌是否有效"""
        if token in self.valid_words:
            return True
        if token.isdigit():
            return True
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token):
            return True
        if token in ['<<', '>>', '+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', '&&', '||', ';', ',']:
            return True
        return False

    def get_best_suggestions(self, token: str, max_suggestions: int = 3) -> List[Tuple[str, float]]:
        """获取最佳建议"""
        suggestions = []

        for valid_word in self.valid_words:
            if abs(len(valid_word) - len(token)) > 2:
                continue
            distance = Levenshtein.distance(token, valid_word)
            max_len = max(len(token), len(valid_word))
            similarity = 1 - (distance / max_len)

            if valid_word.startswith(token[0]):
                similarity += 0.1

            if valid_word.endswith(token[-1]):
                similarity += 0.1

            suggestions.append((valid_word, similarity))

        # 针对流运算符的手动建议
        stream_errors = {
            'cout<': 'cout<<', 'cerr<': 'cerr<<', 'clog<': 'clog<<',
            'cin>': 'cin>>', 'cout<<<': 'cout<<', 'cin>>>': 'cin>>'
        }
        if token in stream_errors:
            suggestions.append((stream_errors[token], 0.9))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:max_suggestions]

    def enhanced_syntax_correction(self, text: str) -> str:
        """增强的语法纠错（重点增强流符号修复和分号补全）"""
        lines = text.split('\n')
        corrected_lines = []

        # 首先进行括号匹配检查
        text = self.fix_bracket_matching(text)
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            corrected_line = line
            line_lower = line.lower()
            line_strip = line.strip()

            # 修复#include指令
            if 'include' in line_lower:
                match = self.include_pattern.search(line)
                if match:
                    full_match = match.group(0)
                    left_delim = match.group(1)
                    header_name = match.group(2)
                    right_delim = match.group(3)

                    header_suggestions = self.get_header_suggestions(header_name)
                    if header_suggestions and header_suggestions[0][1] > 0.8:
                        corrected_header = header_suggestions[0][0]
                        if corrected_header != header_name:
                            line = line.replace(header_name, corrected_header)
                            corrected_line = corrected_line.replace(header_name, corrected_header)
                            match = self.include_pattern.search(corrected_line)
                            if match:
                                left_delim = match.group(1)
                                header_name = match.group(2)
                                right_delim = match.group(3)

                    is_standard_header = header_name in self.standard_headers
                    required_left = '<' if is_standard_header else '"'
                    required_right = '>' if is_standard_header else '"'

                    if not left_delim or left_delim not in ['<', '"']:
                        if left_delim:
                            corrected_line = corrected_line.replace(left_delim, required_left, 1)
                        else:
                            header_pos = corrected_line.find(header_name)
                            if header_pos != -1:
                                corrected_line = corrected_line[:header_pos] + required_left + corrected_line[
                                    header_pos:]

                    if not right_delim or right_delim not in ['>', '"']:
                        if right_delim:
                            corrected_line = corrected_line.replace(right_delim, required_right, 1)
                        else:
                            header_end_pos = corrected_line.find(header_name) + len(header_name)
                            if header_end_pos != -1:
                                corrected_line = corrected_line[:header_end_pos] + required_right + corrected_line[
                                    header_end_pos:]

                    if is_standard_header and left_delim == '"' and right_delim == '"':
                        corrected_line = corrected_line.replace('"', '<', 1).replace('"', '>', 1)

            # 增强流符号修复
            stream_corrections = self.fix_stream_operators(line)
            for original, corrected in stream_corrections:
                if original in corrected_line:
                    corrected_line = corrected_line.replace(original, corrected)

            # 修复include拼写错误
            if line.strip().startswith('1nclude') or line.strip().startswith('#1nclude'):
                corrected_line = line.replace('1nclude', 'include')

            # 修复不完整的流运算符（增强版）
            incomplete_stream_fixes = self.fix_incomplete_stream_operators(corrected_line)
            for original, corrected in incomplete_stream_fixes:
                if original in corrected_line:
                    corrected_line = corrected_line.replace(original, corrected)

            # 增强的分号补全逻辑
            semicolon_fix = self.fix_missing_semicolon(corrected_line)
            if semicolon_fix:
                corrected_line = semicolon_fix

            # 修复for循环相关错误
            if 'for' in line and '1++' in line:
                corrected_line = corrected_line.replace('1++', 'i++')

            if 'for' in line and '1 <' in line:
                corrected_line = corrected_line.replace('1 <', 'i <')

            if 'for' in line and '1nt 1 =' in line:
                corrected_line = corrected_line.replace('1nt 1 =', 'int i =')

            # 修复数组索引
            if 'numbers[1]' in line:
                corrected_line = corrected_line.replace('numbers[1]', 'numbers[i]')

            # 修复main函数
            if 'ma1n(' in corrected_line:
                corrected_line = corrected_line.replace('ma1n(', 'main()')

            corrected_lines.append(corrected_line)

        return '\n'.join(corrected_lines)

    def fix_bracket_matching(self, text: str) -> str:
        """修复括号匹配问题"""
        lines = text.split('\n')
        bracket_stack = []

        for i, line in enumerate(lines):
            for j, char in enumerate(line):
                if char in ['(', '{', '[']:
                    bracket_stack.append((char, i, j))
                elif char in [')', '}', ']']:
                    if bracket_stack:
                        last_bracket, last_i, last_j = bracket_stack.pop()
                        expected = self.get_matching_bracket(last_bracket)
                        if char != expected:
                            # 修复不匹配的括号
                            lines[i] = lines[i][:j] + expected + lines[i][j + 1:]
                    else:
                        # 多余的闭括号，删除
                        lines[i] = lines[i][:j] + lines[i][j + 1:]

        # 处理未闭合的括号
        for bracket, line_num, pos in bracket_stack:
            expected_close = self.get_matching_bracket(bracket)
            lines[line_num] = lines[line_num] + expected_close

        return '\n'.join(lines)

    def get_matching_bracket(self, bracket: str) -> str:
        """获取匹配的括号"""
        bracket_pairs = {'(': ')', '{': '}', '[': ']', ')': '(', '}': '{', ']': '['}
        return bracket_pairs.get(bracket, bracket)

    def fix_missing_semicolon(self, line: str):
        """修复缺失的分号"""
        line_strip = line.strip()

        # 空行或只有空格的行跳过
        if not line_strip:
            return None

        # 跳过注释
        if line_strip.startswith('//') or line_strip.startswith('/*') or line_strip.endswith('*/'):
            return None

        # 跳过预处理指令
        if line_strip.startswith('#'):
            return None

        # 跳过不需要分号的语句开头
        if any(line_strip.startswith(keyword) for keyword in self.no_semicolon_starts):
            return None

        # 跳过不需要分号的语句结尾
        if any(line_strip.endswith(char) for char in self.no_semicolon_ends):
            return None

        # 跳过控制流语句
        control_flow_keywords = ['for', 'if', 'while', 'switch', 'else', 'try', 'catch']
        if any(f"{keyword}(" in line_strip for keyword in control_flow_keywords):
            return None

        # 跳过函数定义、类定义等
        if re.search(r'(class|struct|namespace|enum)\s+\w+(\s*{)?\s*$', line_strip):
            return None

        # 跳过已经以分号结尾的行
        if line_strip.endswith(';'):
            return None

        # 跳过只有括号的行
        if line_strip in ['{', '}', '({', '})', '({})']:
            return None

        # 检查是否是有效的C++语句（包含字母数字或常见运算符）
        if (re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*=', line_strip) or  # 赋值语句
                re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line_strip) or  # 函数调用
                re.search(r'(cout|cin|cerr|clog)\s*<<', line_strip, re.IGNORECASE) or  # 流输出
                re.search(r'cin\s*>>', line_strip, re.IGNORECASE) or  # 流输入
                re.search(r'return\s+', line_strip, re.IGNORECASE) or  # return语句
                re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/%&|^]=', line_strip) or  # 复合赋值
                re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/%]', line_strip) or  # 算术运算
                re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*;?\s*$', line_strip)):  # 变量声明

            # 确保不是函数定义
            if not re.search(r'(\w+)\s+(\w+)\s*\([^)]*\)\s*{?$', line_strip):
                return line.rstrip() + ';'

        return None

    def fix_stream_operators(self, line: str):
        """专门修复流操作符错误"""
        corrections = []

        # 检测并修复错误的流操作符模式
        stream_patterns = [
            # 输出流错误模式
            (r'(\b(cout|cerr|clog)\b\s*)[《〈＜](\s*\w+)', r'\1<<\3'),
            (r'(\b(cout|cerr|clog)\b\s*)[》〉＞](\s*\w+)', r'\1>>\3'),

            # 输入流错误模式
            (r'(\bcin\b\s*)[《〈＜](\s*\w+)', r'\1>>\3'),
            (r'(\bcin\b\s*)[》〉＞](\s*\w+)', r'\1<<\3'),

            # endl相关错误
            (r'(\bendl\b\s*)[《〈＜]', r'\1<<'),
            (r'(\bendl\b\s*)[》〉＞]', r'\1>>'),

            # 多余的操作符
            (r'(\b(cout|cerr|clog)\b\s*<<<)', r'\1<<'),
            (r'(\bcin\b\s*>>>)', r'\1>>'),
        ]

        for pattern, replacement in stream_patterns:
            matches = list(re.finditer(pattern, line, re.IGNORECASE))
            for match in matches:
                original = match.group(0)
                corrected = re.sub(pattern, replacement, original, flags=re.IGNORECASE)
                if original != corrected:
                    corrections.append((original, corrected))

        return corrections

    def fix_incomplete_stream_operators(self, line: str):
        """修复不完整的流操作符"""
        corrections = []

        # 不完整输出流操作符（缺少第二个<）
        incomplete_output = re.findall(r'(\b(cout|cerr|clog)\b\s*<(?![<=]))', line, re.IGNORECASE)
        for match in incomplete_output:
            original = match[0]
            corrected = original + '<'
            corrections.append((original, corrected))

        # 不完整输入流操作符（缺少第二个>）
        incomplete_input = re.findall(r'(\bcin\b\s*>(?![>=]))', line, re.IGNORECASE)
        for match in incomplete_input:
            original = match[0]
            corrected = original + '>'
            corrections.append((original, corrected))

        return corrections

    def correct_code(self, input_file: str, output_file: str):
        """主纠错函数"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                original_text = f.read()
        except UnicodeDecodeError:
            with open(input_file, 'r', encoding='latin-1') as f:
                original_text = f.read()

        logger.info(f"开始处理文件: {input_file}")

        text = self.preprocess_text(original_text)

        text = self.aggressive_char_correction(text)
        text = self.token_based_correction(text)
        text = self.enhanced_syntax_correction(text)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)

        logger.info(f"处理完成。输出文件: {output_file}")

# 使用示例
if __name__ == "__main__":
    corrector = EnhancedCppOCRCorrector()
    # 执行纠错
    corrector.correct_code('test.cpp', 'test_corrected.cpp')