import ast
p='dashboard.py'
text=open(p,encoding='utf-8').read()
try:
    ast.parse(text)
    print('No syntax error')
except SyntaxError as e:
    print('SyntaxError:', e)
    lines=text.splitlines()
    L=e.lineno
    for i in range(max(1,L-6), min(len(lines), L+6)+1):
        marker = '->' if i==L else '  '
        print(f"{marker} {i:4}: {lines[i-1]}")
