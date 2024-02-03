import os

exclude = ['out', 'build.py']

for i in os.listdir('./'):
    if i in exclude:
        continue
    p = f'./{i}/'
    os.system(f'cd {p} && ./build.sh')
    os.system(f'mv {p}*.tar.zst ./out/')