#!/usr/bin/env bash
# The scripted session recorded into docs/demo*.gif (see scripts/make-demo.sh). Everything it runs is real.
# DEMO_LANG selects the captions and the spoken voices: en (default), it, pl, fr, de, ja, zh-CN, hi, ru, es, pt-BR.
set -u
export PS1='$ '
CY=$'\033[1;36m'; DIM=$'\033[2m'; RS=$'\033[0m'
LANG_CODE="${DEMO_LANG:-en}"

# T0..T5: captions. S1/V1: first spoken line + voice. S2/V2: second line + voice. X1/X2: extra flags.
case "$LANG_CODE" in
  it) T0="claudio-tts: Claude Code, adesso con una voce. Tutto gira in locale."
      T1="1. Un solo comando installa tutto (Python, dipendenze, modello vocale, mod)"
      T2="2. 54 voci in 9 lingue. Scegline una con /tts voice <nome>"
      T3="3. Fai parlare Claude (nessuna chiave API, nessun token, nessuna rete)"
      T4="4. Cambia voce e velocità al volo"
      T5="5. Qualcosa non va? Un comando scrive il tuo bug report"
      S1="Ciao! Giro interamente sul tuo computer, senza chiavi API e senza token."; V1=if_sara; X1=""
      S2="E questa è un'altra voce italiana, un po' più veloce."; V2=im_nicola; X2="--speed 1.1" ;;
  pl) T0="claudio-tts: Claude Code z głosem. Wszystko działa lokalnie."
      T1="1. Jedno polecenie instaluje wszystko (Python, zależności, model głosu, mod)"
      T2="2. 54 głosy w 9 językach. Wybierz głos: /tts voice <nazwa>"
      T3="3. Niech Claude przemówi (bez klucza API, bez tokenów, bez internetu)"
      T4="4. Zmień głos i tempo od ręki"
      T5="5. Coś nie działa? Jedno polecenie tworzy zgłoszenie błędu"
      S1="Cześć! Działam w całości na twoim komputerze, bez klucza API i bez tokenów."; V1=af_heart; X1="--lang pl"
      S2="A to drugi głos, trochę szybszy. Polski czytany z akcentem."; V2=am_michael; X2="--lang pl --speed 1.1" ;;
  fr) T0="claudio-tts : Claude Code a enfin une voix. Tout tourne en local."
      T1="1. Une seule commande installe tout (Python, dépendances, modèle vocal, mod)"
      T2="2. 54 voix dans 9 langues. Choisis-en une avec /tts voice <nom>"
      T3="3. Fais parler Claude (sans clé API, sans jetons, sans internet)"
      T4="4. Change de voix et de vitesse à la volée"
      T5="5. Un souci ? Une commande écrit ton rapport de bug"
      S1="Bonjour ! Je tourne entièrement sur votre machine, sans clé API et sans jetons."; V1=ff_siwis; X1=""
      S2="Et voici la même voix, un peu plus rapide."; V2=ff_siwis; X2="--speed 1.15" ;;
  de) T0="claudio-tts: Claude Code bekommt eine Stimme. Alles läuft lokal."
      T1="1. Ein Befehl installiert alles (Python, Abhängigkeiten, Sprachmodell, Mod)"
      T2="2. 54 Stimmen in 9 Sprachen. Wähle eine mit /tts voice <name>"
      T3="3. Lass Claude sprechen (kein API-Schlüssel, keine Tokens, kein Internet)"
      T4="4. Stimme und Tempo sofort wechseln"
      T5="5. Etwas kaputt? Ein Befehl schreibt deinen Fehlerbericht"
      S1="Hallo! Ich laufe komplett auf deinem Rechner, ohne API-Schlüssel und ohne Tokens."; V1=af_heart; X1="--lang de"
      S2="Und das ist eine zweite Stimme, ein bisschen schneller. Deutsch mit Akzent."; V2=am_michael; X2="--lang de --speed 1.1" ;;
  ja) T0="claudio-tts: Claude Code に声を。すべてローカルで動きます。"
      T1="1. コマンド1つで全部インストール（Python・依存関係・音声モデル・mod）"
      T2="2. 9言語・54種類の声。/tts voice <名前> で選べます"
      T3="3. Claude にしゃべらせよう（APIキー・トークン・ネット接続は不要）"
      T4="4. 声も速さもその場で切り替え"
      T5="5. 困ったら？1つのコマンドでバグ報告を作成"
      S1="こんにちは！APIキーもトークンも使わず、すべてあなたのパソコンで動いています。"; V1=jf_alpha; X1=""
      S2="こちらは別の声です。少し速めに話します。"; V2=jm_kumo; X2="--speed 1.1" ;;
  zh-CN) T0="claudio-tts：让 Claude Code 开口说话。全部在本地运行。"
      T1="1. 一条命令装好一切（Python、依赖、语音模型、mod）"
      T2="2. 9 种语言、54 种声音。用 /tts voice <名称> 选择"
      T3="3. 让 Claude 开口（无需 API 密钥、不消耗令牌、无需联网）"
      T4="4. 随时切换声音和语速"
      T5="5. 出问题了？一条命令生成错误报告"
      S1="你好！我完全在你的电脑上运行，不需要 API 密钥，也不消耗令牌。"; V1=zf_xiaoxiao; X1=""
      S2="这是另一种声音，语速稍快。"; V2=zm_yunxi; X2="--speed 1.1" ;;
  hi) T0="claudio-tts: Claude Code ko mili awaaz. Sab kuch local chalta hai."
      T1="1. Ek command se sab install (Python, dependencies, voice model, mod)"
      T2="2. 9 bhashaon mein 54 awaazen. /tts voice <naam> se chuniye"
      T3="3. Claude ko bulwaiye (na API key, na token, na internet) - Hindi voice hf_alpha"
      T4="4. Awaaz aur raftaar turant badlein"
      T5="5. Kuch gadbad? Ek command se bug report taiyaar"
      S1="नमस्ते! मैं पूरी तरह आपके कंप्यूटर पर चलता हूँ, बिना API key और बिना टोकन के।"; V1=hf_alpha; X1=""
      S2="और यह दूसरी आवाज़ है, थोड़ी तेज़।"; V2=hm_omega; X2="--speed 1.1"
      D1="Namaste! Main poori tarah aapke computer par chalta hoon, bina API key aur bina token ke."
      D2="Aur yeh doosri awaaz hai, thodi tez." ;;
  ru) T0="claudio-tts: у Claude Code появился голос. Всё работает локально."
      T1="1. Одна команда ставит всё (Python, зависимости, голосовая модель, мод)"
      T2="2. 54 голоса на 9 языках. Выбери голос: /tts voice <имя>"
      T3="3. Пусть Claude заговорит (без API-ключа, без токенов, без интернета)"
      T4="4. Меняй голос и скорость на лету"
      T5="5. Что-то не так? Одна команда напишет отчёт об ошибке"
      S1="Привет! Я работаю целиком на твоём компьютере, без API-ключа и без токенов."; V1=af_heart; X1="--lang ru"
      S2="А это второй голос, чуть быстрее. Русский с акцентом."; V2=am_michael; X2="--lang ru --speed 1.1" ;;
  es) T0="claudio-tts: Claude Code, ahora con voz. Todo funciona en local."
      T1="1. Un solo comando lo instala todo (Python, dependencias, modelo de voz, mod)"
      T2="2. 54 voces en 9 idiomas. Elige una con /tts voice <nombre>"
      T3="3. Haz hablar a Claude (sin clave de API, sin tokens, sin internet)"
      T4="4. Cambia de voz y de velocidad al instante"
      T5="5. ¿Algo falla? Un comando escribe tu informe de error"
      S1="¡Hola! Funciono por completo en tu equipo, sin clave de API y sin tokens."; V1=ef_dora; X1=""
      S2="Y esta es otra voz, un poco más rápida."; V2=em_alex; X2="--speed 1.1" ;;
  pt-BR) T0="claudio-tts: o Claude Code agora tem voz. Tudo roda localmente."
      T1="1. Um comando instala tudo (Python, dependências, modelo de voz, mod)"
      T2="2. 54 vozes em 9 idiomas. Escolha uma com /tts voice <nome>"
      T3="3. Faça o Claude falar (sem chave de API, sem tokens, sem internet)"
      T4="4. Troque de voz e de velocidade na hora"
      T5="5. Algo deu errado? Um comando escreve seu relatório de bug"
      S1="Olá! Eu rodo inteiramente no seu computador, sem chave de API e sem tokens."; V1=pf_dora; X1=""
      S2="E esta é outra voz, um pouco mais rápida."; V2=pm_alex; X2="--speed 1.1" ;;
  *)  T0="claudio-tts: Claude Code, now with a voice. Everything below runs locally."
      T1="1. One command installs everything (Python, dependencies, the voice model, the mod)"
      T2="2. 54 voices in 9 languages. Pick one with /tts voice <name>"
      T3="3. Say something (no API key, no tokens, no internet)"
      T4="4. Switch voice and speed, instantly"
      T5="5. Something wrong? One command writes your bug report"
      S1="Hello! I run entirely on your machine, with no API key and no tokens."; V1=af_heart; X1=""
      S2="And this is a different American voice, a bit faster."; V2=am_michael; X2="--speed 1.1" ;;
esac

type_cmd() {  # print a command as if typed (or its $3 display form), then run it
  printf '%s$ %s' "$RS" ""
  local text="${3:-$1}" i
  for ((i = 0; i < ${#text}; i++)); do printf '%s' "${text:$i:1}"; sleep 0.03; done
  sleep 0.5; printf '\n'
  eval "$1"
  sleep "${2:-1.2}"
}
say_title() { printf '%s# %s%s\n' "$DIM" "$1" "$RS"; sleep 0.9; }

clear
say_title "$T0"
say_title "$T1"
type_cmd "bash install.sh --local 2>&1 | grep -E '==>|ok |All good'" 2.0
say_title "$T2"
type_cmd "claudio-tts voices | head -7" 2.0
say_title "$T3"
type_cmd "claudio-tts say '$S1' --voice $V1 $X1" 0.8 "${D1:+claudio-tts say '$D1' --voice $V1 $X1}"
say_title "$T4"
type_cmd "claudio-tts say '$S2' --voice $V2 $X2" 0.8 "${D2:+claudio-tts say '$D2' --voice $V2 $X2}"
say_title "$T5"
type_cmd "claudio-tts doctor --report" 2.5
printf '%s# github.com/restante/claudio-tts%s\n' "$CY" "$RS"
sleep 2.5
