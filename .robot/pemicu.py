"""Penjaga: bandingkan isi terakhir repo privat dengan .robot/terakhir.json, picu robot yang perlu.
Tidak mencetak isi data; hanya sha pendek dan nama robot."""
import json, os, subprocess, urllib.request

P = 'CatatanSaham/catatan-saham-mtf'
ME = os.environ.get('GITHUB_REPOSITORY', 'CatatanSaham/catatan-saham-publik')
ST = '.robot/terakhir.json'


def api(path):
    rq = urllib.request.Request('https://api.github.com/repos/' + P + path, headers={
        'Authorization': 'Bearer ' + os.environ['PT'], 'Accept': 'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(rq, timeout=30))


def akhir(branch, path=None):
    q = '/commits?per_page=1&sha=' + branch + ('&path=' + path if path else '')
    j = api(q)
    return j[0]['sha'] if j else ''


now = {
    'harian': akhir('apk-data', 'apk-data/harian'),
    'kepemilikan': akhir('apk-data', 'apk-data/kepemilikan'),
    'apk-next': akhir('apk-next'),
    'apk-build': akhir('apk-build'),
}
try:
    old = json.load(open(ST))
except Exception:
    old = {}

picu = []
if not old:
    print('Penjaga pertama kali: hanya mencatat keadaan, tidak memicu.')
else:
    if now['harian'] != old.get('harian'):
        picu += [('cleanbuy-telegram.yml', {'dari': 'zip'}), ('apk-telegram-data.yml', {}),
                 ('publish-foreign-bot-data.yml', {}), ('publik.yml', {}), ('derive.yml', {}), ('api-data.yml', {})]
    if now['kepemilikan'] != old.get('kepemilikan') and not any(w == 'publik.yml' for w, _ in picu):
        picu.append(('publik.yml', {}))
    if now['apk-next'] != old.get('apk-next'):
        picu.append(('apk-nonadmin.yml', {}))
    if now['apk-build'] != old.get('apk-build') and old.get('apk-build'):
        picu.append(('apk.yml', {}))

for wf, inp in picu:
    cmd = ['gh', 'workflow', 'run', wf, '-R', ME, '--ref', 'main']
    for k, v in inp.items():
        cmd += ['-f', k + '=' + v]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print('picu', wf, 'ok' if r.returncode == 0 else 'GAGAL ' + r.stderr.strip()[:200])

print('keadaan:', {k: v[:7] for k, v in now.items()})
if now != old:
    json.dump(now, open(ST, 'w'), indent=1)
    subprocess.run(['git', 'config', 'user.name', 'Penjaga Catatan Saham'], check=True)
    subprocess.run(['git', 'config', 'user.email', 'noreply@github.com'], check=True)
    subprocess.run(['git', 'add', ST], check=True)
    subprocess.run(['git', 'commit', '-q', '-m', 'penjaga: catat keadaan repo privat'], check=True)
    for _ in range(3):
        if subprocess.run('git pull -q --rebase origin main && git push -q origin HEAD:main', shell=True).returncode == 0:
            break
