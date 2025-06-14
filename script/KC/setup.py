from IPython.display import display, Image, HTML, clear_output
from IPython import get_ipython
from ipywidgets import widgets
from pathlib import Path
import subprocess
import argparse
import shlex
import json
import sys
import os
import re

# --- Function Definitions (Moved up for better structure) ---

def parse_arguments():
    """Parses command-line arguments for the script."""
    parser = argparse.ArgumentParser(description='Universal WebUI Installer Script for Cloud Notebooks')
    # --- Core Arguments ---
    parser.add_argument('--webui', required=True, help='Available webui: A1111, Forge, ComfyUI, ReForge, SwarmUI')
    parser.add_argument('--civitai_key', required=True, help='Your CivitAI API key')
    parser.add_argument('--hf_read_token', default=None, help='Your Hugging Face READ Token (optional)')
    parser.add_argument('--bgm', default='dQw4w9WgXcQ', help='Play a YouTube video ID in the background during setup.')
    
    # --- New Arguments for Environment Flexibility ---
    parser.add_argument('--base_dir', type=str, default=None, help='(Optional) Override the base directory (e.g., for temp files). For generic environments.')
    parser.add_argument('--home_dir', type=str, default=None, help='(Optional) Override the home/working directory (where repos are cloned). For generic environments.')

    return parser.parse_known_args()

def detect_and_configure_environment(args):
    """Detects the cloud environment or uses user-provided paths."""
    env_list = {
        'Colab': ('/content', '/content', 'COLAB_JUPYTER_TOKEN'),
        'Kaggle': ('/kaggle', '/kaggle/working', 'KAGGLE_DATA_PROXY_TOKEN')
    }
    
    # Priority 1: User-defined paths via arguments
    if args.base_dir and args.home_dir:
        print("Using user-defined paths.")
        envname = 'Custom'
        envbase = Path(args.base_dir)
        envhome = Path(args.home_dir)
        return envname, envbase, envhome

    # Priority 2: Auto-detection of known environments
    for envname, (envbase, envhome, envvar) in env_list.items():
        if envvar in os.environ:
            print(f"Detected {envname} environment.")
            return envname, Path(envbase), Path(envhome)
            
    # Priority 3: Fallback to a generic setup
    print("No known cloud environment detected. Using generic setup.")
    print(f"Defaulting to current working directory: {Path.cwd()}")
    print("You can override this with --base_dir and --home_dir arguments.")
    envname = 'Generic'
    envbase = Path.cwd()
    envhome = Path.cwd()
    return envname, envbase, envhome

def validate_inputs(args, webui_list):
    """Validates the parsed arguments and returns clean values."""
    arg1 = args.webui.lower()
    arg2 = args.civitai_key.strip() if args.civitai_key else ''
    arg3 = args.hf_read_token.strip() if args.hf_read_token else ''
    arg4 = args.bgm.strip() if args.bgm else ''

    if not any(arg1 == option.lower() for option in webui_list):
        print(f'{ERR}: Invalid webui option: "{args.webui}"')
        print(f'Available webui options: {", ".join(webui_list)}')
        return None, None, None, None

    if not arg2:
        print(f'{ERR}: CivitAI API key is missing.')
        return None, None, None, None
    if re.search(r'\s+', arg2):
        print(f'{ERR}: CivitAI API key contains spaces "{arg2}" - not allowed.')
        return None, None, None, None
    if len(arg2) < 32:
        print(f'{ERR}: CivitAI API key must be at least 32 characters long.')
        return None, None, None, None

    if not arg3 or re.search(r'\s+', arg3):
        arg3 = ''
        
    rr = 'dQw4w9WgXcQ' # Default background music
    if not arg4 or re.search(r'\s+', arg4):
        arg4 = rr
        
    muzik = f"""
    <iframe width="640" height="360"
      src="https://www.youtube.com/embed/{arg4}?autoplay=1"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen>
    </iframe>
    """
    
    webui_webui = next(option for option in webui_list if arg1 == option.lower())
    return webui_webui, arg2, arg3, muzik

# --- Original Script Functions (largely unchanged, but now rely on globally set paths) ---

def PythonPortable():
    BIN = str(PY / 'bin')
    PKG = str(PY / 'lib/python3.10/site-packages')

    if webui in ['ComfyUI', 'SwarmUI']:
        url = 'https://huggingface.co/gutris1/webui/resolve/main/env/ComfyUI-python310-torch251-cu121.tar.lz4'
    else:
        url = 'https://huggingface.co/gutris1/webui/resolve/main/env/python310-torch251-cu121.tar.lz4'

    fn = Path(url).name

    CD('/')
    print(f'\n{AR} installing Python Portable 3.10.15')
    SyS('sudo apt-get -qq -y install aria2 pv lz4 >/dev/null 2>&1')
    aria = f'aria2c --console-log-level=error --stderr=true -c -x16 -s16 -k1M -j5 {url} -o {fn}'
    pv = f'pv {fn} | lz4 -d | tar -xf -'

    # Using subprocess.run for better error handling and clarity
    subprocess.run(shlex.split(aria), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    subprocess.run(pv, shell=True, check=True)

    Path(f'/{fn}').unlink()

    sys.path.insert(0, PKG)
    os.environ['PATH'] = f"{BIN}:{os.environ['PATH']}"
    os.environ['PYTHONPATH'] = f"{PKG}:{os.environ.get('PYTHONPATH', '')}"

    if ENVNAME == 'Kaggle':
        for cmd in [
            'pip install ipywidgets jupyterlab_widgets --upgrade',
            'rm -f /usr/lib/python3.10/sitecustomize.py'
        ]: SyS(f'{cmd} >/dev/null 2>&1')

def install_tunnel():
    SyS(f'wget -qO {USR}/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64')
    SyS(f'chmod +x {USR}/cl')

    path = PY / 'lib/python3.10/site-packages/gradio_tunneling/main.py'
    SyS(f'pip install -q gradio-tunneling && wget -qO {path} https://github.com/gutris1/segsmaker/raw/main/script/gradio-tunnel.py')

    bins = {
        'zrok': {
            'bin': USR / 'zrok',
            'url': 'https://github.com/openziti/zrok/releases/download/v1.0.2/zrok_1.0.2_linux_amd64.tar.gz'
        },
        'ngrok': {
            'bin': USR / 'ngrok',
            'url': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz'
        }
    }

    for n, b in bins.items():
        if b['bin'].exists():
            continue
        url = b['url']
        name = Path(url).name
        SyS(f'wget -qO {name} {url} && tar -xzf {name} -C {USR} && rm -f {name}')

def saving():
    j = {
        'ENVNAME': ENVNAME,
        'HOMEPATH': str(HOME),
        'TEMPPATH': str(TMP),
        'BASEPATH': str(BASEPATH)
    }
    text = '\n'.join(f"{k} = '{v}'" for k, v in j.items())
    Path(KANDANG).write_text(text)

def marking(p, n, u):
    t = p / n
    v = {'ui': u, 'launch_args': '', 'tunnel': ''}
    
    d = json.loads(t.read_text()) if t.exists() else {}
    d.update(v)
    t.write_text(json.dumps(d, indent=4))

def key_inject(C, H):
    p = Path(nenen)
    v = p.read_text()
    v = v.replace("TOKET = ''", f"TOKET = '{C}'")
    v = v.replace("TOBRUT = ''", f"TOBRUT = '{H}'")
    p.write_text(v)

def sym_link(U, M):
    configs = {
        'A1111': {'sym': [f"rm -rf {M / 'Stable-diffusion/tmp_ckpt'} {M / 'Lora/tmp_lora'} {M / 'ControlNet'} {TMP}/*"], 'links': [(TMP / 'ckpt', M / 'Stable-diffusion/tmp_ckpt'), (TMP / 'lora', M / 'Lora/tmp_lora'), (TMP / 'controlnet', M / 'ControlNet')]},
        'ReForge': {'sym': [f"rm -rf {M / 'Stable-diffusion/tmp_ckpt'} {M / 'Lora/tmp_lora'} {M / 'ControlNet'}", f"rm -rf {M / 'svd'} {M / 'z123'} {TMP}/*"], 'links': [(TMP / 'ckpt', M / 'Stable-diffusion/tmp_ckpt'), (TMP / 'lora', M / 'Lora/tmp_lora'), (TMP / 'controlnet', M / 'ControlNet'), (TMP / 'z123', M / 'z123'), (TMP / 'svd', M / 'svd')]},
        'Forge': {'sym': [f"rm -rf {M / 'Stable-diffusion/tmp_ckpt'} {M / 'Lora/tmp_lora'} {M / 'ControlNet'}", f"rm -rf {M / 'svd'} {M / 'z123'} {M / 'clip'} {M / 'clip_vision'} {M / 'diffusers'}", f"rm -rf {M / 'diffusion_models'} {M / 'text_encoder'} {M / 'unet'} {TMP}/*"], 'links': [(TMP / 'ckpt', M / 'Stable-diffusion/tmp_ckpt'), (TMP / 'lora', M / 'Lora/tmp_lora'), (TMP / 'controlnet', M / 'ControlNet'), (TMP / 'z123', M / 'z123'), (TMP / 'svd', M / 'svd'), (TMP / 'clip', M / 'clip'), (TMP / 'clip_vision', M / 'clip_vision'), (TMP / 'diffusers', M / 'diffusers'), (TMP / 'diffusion_models', M / 'diffusion_models'), (TMP / 'text_encoders', M / 'text_encoder'), (TMP / 'unet', M / 'unet')]},
        'ComfyUI': {'sym': [f"rm -rf {M / 'checkpoints/tmp_ckpt'} {M / 'loras/tmp_lora'} {M / 'controlnet'}", f"rm -rf {M / 'clip'} {M / 'clip_vision'} {M / 'diffusers'} {M / 'diffusion_models'}", f"rm -rf {M / 'text_encoders'} {M / 'unet'} {TMP}/*"], 'links': [(TMP / 'ckpt', M / 'checkpoints/tmp_ckpt'), (TMP / 'lora', M / 'loras/tmp_lora'), (TMP / 'controlnet', M / 'controlnet'), (TMP / 'clip', M / 'clip'), (TMP / 'clip_vision', M / 'clip_vision'), (TMP / 'diffusers', M / 'diffusers'), (TMP / 'diffusion_models', M / 'diffusion_models'), (TMP / 'text_encoders', M / 'text_encoders'), (TMP / 'unet', M / 'unet')]},
        'SwarmUI': {'sym': [f"rm -rf {M / 'Stable-Diffusion/tmp_ckpt'} {M / 'Lora/tmp_lora'} {M / 'controlnet'}", f"rm -rf {M / 'clip'} {M / 'unet'} {TMP}/*"], 'links': [(TMP / 'ckpt', M / 'Stable-Diffusion/tmp_ckpt'), (TMP / 'lora', M / 'Lora/tmp_lora'), (TMP / 'controlnet', M / 'controlnet'), (TMP / 'clip', M / 'clip'), (TMP / 'unet', M / 'unet')]}
    }
    cfg = configs.get(U)
    for cmd in cfg['sym']: SyS(cmd)
    if U in ['A1111', 'Forge', 'ReForge']:
        for d in ['Lora', 'ESRGAN']: (M / d).mkdir(parents=True, exist_ok=True)
    for src, tg in cfg['links']: SyS(f'ln -s {src} {tg}')

def webui_req(U, W, M):
    CD(W)
    if U in ['A1111', 'Forge', 'ComfyUI', 'ReForge']:
        pull(f'https://github.com/gutris1/segsmaker {U.lower()} {W}')
    elif U == 'SwarmUI':
        M.mkdir(parents=True, exist_ok=True)
        for sub in ['Stable-Diffusion', 'Lora', 'Embeddings', 'VAE', 'upscale_models']: (M / sub).mkdir(parents=True, exist_ok=True)
        download(f'https://dot.net/v1/dotnet-install.sh {W}')
        dotnet = W / 'dotnet-install.sh'
        dotnet.chmod(0o755)
        SyS('bash ./dotnet-install.sh --channel 8.0')
    sym_link(U, M)
    install_tunnel()
    scripts = [f'https://github.com/gutris1/segsmaker/raw/main/script/controlnet.py {W}/asd', f'https://github.com/gutris1/segsmaker/raw/main/script/KC/segsmaker.py {W}']
    u = M / 'upscale_models' if U in ['ComfyUI', 'SwarmUI'] else M / 'ESRGAN'
    upscalers = [f'https://huggingface.co/gutris1/webui/resolve/main/misc/4x-UltraSharp.pth {u}', f'https://huggingface.co/gutris1/webui/resolve/main/misc/4x-AnimeSharp.pth {u}', f'https://huggingface.co/gutris1/webui/resolve/main/misc/4x_NMKD-Superscale-SP_178000_G.pth {u}', f'https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/8x_NMKD-Superscale_150000_G.pth {u}', f'https://huggingface.co/gutris1/webui/resolve/main/misc/4x_RealisticRescaler_100000_G.pth {u}', f'https://huggingface.co/gutris1/webui/resolve/main/misc/8x_RealESRGAN.pth {u}', f'https://huggingface.co/gutris1/webui/resolve/main/misc/4x_foolhardy_Remacri.pth {u}', f'https://huggingface.co/subby2006/NMKD-YandereNeoXL/resolve/main/4x_NMKD-YandereNeoXL_200k.pth {u}', f'https://huggingface.co/subby2006/NMKD-UltraYandere/resolve/main/4x_NMKD-UltraYandere_300k.pth {u}']
    for item in scripts + upscalers: download(item)
    if U not in ['SwarmUI', 'ComfyUI']:
        SyS(f'rm -f {W}/html/card-no-preview.png')
        download(f'https://huggingface.co/gutris1/webui/resolve/main/misc/card-no-preview.png {W}/html')

def webui_extension(U, W, M):
    EXT = W / 'custom_nodes' if U == 'ComfyUI' else W / 'extensions'
    CD(EXT)
    if U == 'ComfyUI':
        say('<br><b>【{red} Installing Custom Nodes{d} 】{red}</b>')
        clone(str(W / 'asd/custom_nodes.txt'))
        print()
        for faces in [f'https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth {M}/facerestore_models', f'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth {M}/facerestore_models']: download(faces)
    else:
        say('<br><b>【{red} Installing Extensions{d} 】{red}</b>')
        clone(str(W / 'asd/extension.txt'))
        clone('https://github.com/gutris1/sd-civitai-browser-plus-plus' if ENVNAME == 'Kaggle' else 'https://github.com/BlafKing/sd-civitai-browser-plus')

def webui_installation(U, W, M, E, V):
    webui_req(U, W, M)
    extras = [f'https://huggingface.co/gutris1/webui/resolve/main/misc/embeddings.zip {W}', f'https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors {V}', f'https://huggingface.co/gutris1/webui/resolve/main/misc/embeddingsXL.zip {W}', f'https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl.vae.safetensors {V} sdxl_vae.safetensors']
    for i in extras: download(i)
    SyS(f'unzip -qo {W / "embeddings.zip"} -d {E} && rm {W / "embeddings.zip"}')
    SyS(f'unzip -qo {W / "embeddingsXL.zip"} -d {E} && rm {W / "embeddingsXL.zip"}')
    if U != 'SwarmUI': webui_extension(U, W, M)

def webui_selection(ui):
    with output:
        output.clear_output(wait=True)
        repo_url = {'A1111': 'https://github.com/AUTOMATIC1111/stable-diffusion-webui A1111', 'Forge': 'https://github.com/lllyasviel/stable-diffusion-webui-forge Forge', 'ComfyUI': 'https://github.com/comfyanonymous/ComfyUI', 'ReForge': 'https://github.com/Panchovix/stable-diffusion-webui-reForge ReForge', 'SwarmUI': 'https://github.com/mcmonkeyprojects/SwarmUI'}
        if ui in repo_url: (WEBUI, repo) = (HOME / ui, repo_url[ui])
        MODELS = WEBUI / 'Models' if ui == 'SwarmUI' else WEBUI / 'models'
        EMB = MODELS / 'Embeddings' if ui == 'SwarmUI' else (MODELS / 'embeddings' if ui == 'ComfyUI' else WEBUI / 'embeddings')
        VAE = MODELS / 'vae' if ui == 'ComfyUI' else MODELS / 'VAE'
        say(f'<b>【{{red}} Installing {WEBUI.name}{{d}} 】{{red}}</b>')
        clone(repo)
        webui_installation(ui, WEBUI, MODELS, EMB, VAE)
        with loading:
            loading.clear_output(wait=True)
            say('<br><b>【{red} Done{d} 】{red}</b>')
            tempe()
            CD(HOME)

def webui_installer():
    CD(HOME)
    ui = (json.load(MARKED.open('r')) if MARKED.exists() else {}).get('ui')
    WEBUI = HOME / ui if ui else None
    if WEBUI is not None and WEBUI.exists() and (WEBUI / '.git').exists():
        CD(WEBUI)
        with output:
            output.clear_output(wait=True)
            pull_branch = 'master' if ui in ['A1111', 'ComfyUI', 'SwarmUI'] else 'main'
            SyS(f'git pull origin {pull_branch}')
        with loading: loading.clear_output()
    else:
        try:
            webui_selection(webui)
        except KeyboardInterrupt:
            with loading: loading.clear_output()
            with output: print('\nCanceled.')
        except Exception as e:
            with loading: loading.clear_output()
            with output: print(f'\n{ERR}: {e}')

def notebook_scripts():
    z = [(STR / '00-startup.py', f'wget -qO {STR}/00-startup.py https://github.com/gutris1/segsmaker/raw/main/script/KC/00-startup.py'), (nenen, f'wget -qO {nenen} https://github.com/gutris1/segsmaker/raw/main/script/nenen88.py'), (STR / 'cupang.py', f'wget -qO {STR}/cupang.py https://github.com/gutris1/segsmaker/raw/main/script/cupang.py'), (MRK, f'wget -qO {MRK} https://github.com/gutris1/segsmaker/raw/main/script/marking.py')]
    for x, y in z:
        if not x.exists(): SyS(y)
    saving()
    key_inject(civitai_key, hf_read_token)
    marking(SRC, 'marking.json', webui)
    sys.path.append(str(STR))
    for script_path in [nenen, KANDANG, MRK]:
        if script_path.exists(): get_ipython().run_line_magic('run', str(script_path))

# --- Main Execution Block ---

# 1. Initialize Widgets and IPython helpers
output = widgets.Output()
loading = widgets.Output()
SyS = get_ipython().system
CD = os.chdir

# 2. Parse Arguments and Configure Environment
args, unknown = parse_arguments()
ENVNAME, ENVBASE, ENVHOME = detect_and_configure_environment(args)

# 3. Define Constants and Paths
RST, R, P, ORANGE = '\033[0m', '\033[31m', '\033[38;5;135m', '\033[38;5;208m'
AR, ERR = f'{ORANGE}▶{RST}', f'{P}[{RST}{R}ERROR{RST}{P}]{RST}'
IMG = 'https://github.com/gutris1/segsmaker/raw/main/script/loading.png'
WEBUI_LIST = ['A1111', 'Forge', 'ComfyUI', 'ReForge', 'SwarmUI']

HOME = Path(ENVHOME)
BASEPATH = Path(ENVBASE)
TMP = BASEPATH / 'temp'
PY = Path('/GUTRIS1')
SRC = HOME / 'gutris1'
MRK = SRC / 'marking.py' # This is a script, not the json file
MARKED = SRC / 'marking.json' # The actual json file
KEY = SRC / 'api-key.json'
USR = Path('/usr/bin')
STR = Path.home() / '.ipython/profile_default/startup'
nenen = STR / 'nenen88.py'
KANDANG = STR / 'KANDANG.py'

# 4. Create necessary directories
TMP.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)
STR.mkdir(parents=True, exist_ok=True)

# 5. Validate User Inputs
webui, civitai_key, hf_read_token, bgm = validate_inputs(args, WEBUI_LIST)
if civitai_key is None:
    sys.exit() # Exit if validation fails

# 6. Start Installation Process
display(output, loading)
with loading:
    display(HTML(bgm))
    display(Image(url=IMG))

with output:
    if not PY.exists():
        PythonPortable()

notebook_scripts()

# 7. Import late-stage dependencies and run installer
try:
    from nenen88 import clone, say, download, tempe, pull
    webui_installer()
except ImportError:
    print(f"{ERR}: Could not import helper scripts. Please check the 'notebook_scripts' function and paths.")
    with loading: loading.clear_output()
