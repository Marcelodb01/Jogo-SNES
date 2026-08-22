# NÚCLEO — protótipo mobile em Python (Kivy)

Vertical slice de um action-RPG de masmorras: uma sala por tela, colisão livre
(não travada no grid), puzzle de bloco em placa de pressão, porta que reage ao
puzzle, um inimigo em patrulha e ataque corpo a corpo.

## 1. Testar no PC primeiro

Sempre valide no desktop antes de gastar 20 minutos num build Android.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install "kivy[base]==2.3.0"
python main.py
```

Controles no PC: **WASD/setas** movem, **espaço** ataca, **R** reinicia.
No celular: metade esquerda da tela vira analógico onde o dedo tocar, metade
direita é o botão de ataque.

## 2. Gerar o APK

O Buildozer **só roda em Linux**. Três caminhos, do mais simples ao mais controlado:

### a) GitHub Actions (recomendado se você está no Windows)

Suba a pasta como repositório. O workflow em `.github/workflows/build-apk.yml`
compila a cada push e deixa o `.apk` disponível em *Actions → artifacts*.
Zero configuração local.

### b) WSL2 ou Linux nativo

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
    pkg-config zlib1g-dev libncurses-dev libtinfo6 cmake libffi-dev libssl-dev

pip install --user buildozer cython==0.29.36

buildozer android debug          # primeira vez baixa SDK/NDK: 20-40 min
```

O APK sai em `bin/nucleo-0.1-arm64-v8a_armeabi-v7a-debug.apk`.
Com o celular plugado e depuração USB ativa:

```bash
buildozer android debug deploy run logcat
```

### c) Docker

```bash
docker run --rm -v "$PWD":/home/user/hostcwd kivy/buildozer android debug
```

### Erros comuns

| Sintoma | Causa |
|---|---|
| Build para em `Cython` | versão errada — fixe `cython==0.29.36` |
| `Aidl not found` | falta o build-tools; rode `buildozer android clean` e refaça |
| App abre e fecha na hora | traceback Python — leia com `buildozer android logcat` |
| APK não instala | é build *debug* não assinado; ative "fontes desconhecidas" |

Para publicar na Play Store depois: `buildozer android release`, e aí entram
keystore e assinatura.

## 3. Onde mexer no código

Tudo está em `main.py`, em blocos separados por comentário:

- `ROOM` — o mapa em texto. Editar aqui já cria salas novas.
  `#` parede, `.` chão, `B` bloco, `P` placa, `D` porta, `S` início,
  `E` inimigo, `X` saída.
- constantes no topo — velocidade, delay de empurrão, HP, cores.
- `move_axis()` — colisão eixo a eixo, é o que dá o "deslizar" na parede.
- `_attempt_push()` — regra de empurrar bloco (segurar `PUSH_DELAY` na direção).
- `check_puzzle()` — condição de abrir a porta.
- `draw()` — render por primitivas. Trocar `Rectangle` por `Rectangle(source=...)`
  é o caminho para entrar com sprites depois.

## 4. Próximos passos naturais

1. Múltiplas salas: transformar `ROOM` numa lista e trocar de sala ao pisar em `X`.
2. Carregar mapas de arquivo `.txt` externo em vez de constante no código.
3. Sprites e animação (Atlas do Kivy) no lugar dos retângulos.
4. Save de progresso com `JsonStore` do Kivy.
5. Áudio com `kivy.core.audio.SoundLoader`.
