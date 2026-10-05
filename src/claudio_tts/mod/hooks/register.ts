import type { Hook, Register } from 'claude-code'

import {
  DEFAULT_SPEED,
  DEFAULT_VOLUME,
  MAX_SPEED,
  MIN_SPEED,
  hasSummary,
  parseTtsArgs,
  speechText,
} from './speech'

const MIN_NARRATION = 10
const USAGE =
  'Usage: /tts [mute|unmute|status|default on|off|volume 1-10|speed 0.5-1.5|device <names|all|default>|mic <name|default>]'

type Dollar = Parameters<Hook<'turn.start'>>[0]

// Every OS-specific job (audio, process control, music ducking) lives in the `claudio-tts` Python
// package; this mod only decides what to say and when. CLAUDIO_TTS_PYTHON is set by `install-mod`.
async function python($: Dollar) {
  try {
    return (await $.env.get('CLAUDIO_TTS_PYTHON')) ?? 'python'
  } catch {
    return 'python'
  }
}

async function cli($: Dollar, args: string[], stdin?: string) {
  const exe = await python($)
  try {
    return await $.process.run([exe, '-m', 'claudio_tts', ...args], { stdin, timeoutMs: 15000 })
  } catch (error) {
    $.ui.log(`claudio-tts: ${String(error)}`, { to: 'debug' })
    return undefined
  }
}

async function sessionId($: Dollar) {
  try {
    return await $.session.id()
  } catch {
    return 'default' // only when the engine cannot name the session (tests); speech still works
  }
}

async function stop($: Dollar) {
  await cli($, ['stop', '--session', await sessionId($)])
}

async function speak($: Dollar, text: string) {
  if (await isMuted($)) return
  const volume = Number((await $.store.get('volume')) ?? DEFAULT_VOLUME)
  const speed = Number((await $.store.get('speed')) ?? DEFAULT_SPEED)
  const devices = String((await $.store.get('devices')) ?? 'default')
  await cli(
    $,
    [
      'speak',
      '--session', await sessionId($),
      '--volume', String(volume),
      '--speed', String(speed),
      '--devices', devices,
    ],
    text,
  )
}

const MUTED = { plugin: 'claudio-tts', key: 'muted' } as const

// This session's switch if it was ever set here, else the startup default (muted unless `/tts default on`).
async function isMuted($: Dollar) {
  const { value } = await $.state.get(MUTED)
  if (value !== undefined) return value
  return ((await $.store.get('defaultMuted')) ?? true) === true
}

async function showStatus($: Dollar) {
  $.ui.status((await isMuted($)) ? 'TTS muted' : 'TTS on')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'tts',
      description: 'Spoken replies (per session): /tts [mute|unmute|status|default on|off|volume|speed|device|mic]',
    })
    await showStatus($)
    return next(e)
  })

  on('command.run', { command: 'tts' }, async ($, e) => {
    const cmd = parseTtsArgs(e.args)
    if (!cmd) return { text: USAGE }
    const volume = Number((await $.store.get('volume')) ?? DEFAULT_VOLUME)

    if (cmd.kind === 'device') {
      const current = String((await $.store.get('devices')) ?? 'default')
      if (cmd.value === undefined) {
        const listed = await cli($, ['devices'])
        return {
          text: `TTS output: ${current}\nAvailable:\n${listed?.stdout.trim() ?? '(could not list devices)'}\nUse /tts device <name,name|all|default>`,
        }
      }
      await $.store.set('devices', cmd.value)
      await speak($, 'Speech output changed.')
      return { text: `TTS output: ${cmd.value}` }
    }

    if (cmd.kind === 'mic') {
      const current = String((await $.store.get('mic')) ?? 'default')
      if (cmd.value === undefined) {
        const inputs = await cli($, ['devices', '--inputs'])
        return {
          text: `Microphone: ${current}\nAvailable:\n${inputs?.stdout.trim() ?? '(could not list devices)'}\nUse /tts mic <name|default>`,
        }
      }
      await $.store.set('mic', cmd.value)
      return { text: `Microphone: ${cmd.value}` }
    }

    if (cmd.kind === 'default') {
      const startMuted = ((await $.store.get('defaultMuted')) ?? true) === true
      if (cmd.value === undefined) {
        return { text: `New sessions start ${startMuted ? 'muted' : 'speaking'} (/tts default on|off to change)` }
      }
      await $.store.set('defaultMuted', cmd.value === 'off')
      return { text: `New sessions will start ${cmd.value === 'off' ? 'muted' : 'speaking'}` }
    }

    if (cmd.kind === 'speed') {
      const speed = Number((await $.store.get('speed')) ?? DEFAULT_SPEED)
      if (cmd.value === undefined) {
        return { text: `TTS speed ${speed} (${MIN_SPEED} slow to ${MAX_SPEED} fast, 1 normal)` }
      }
      await $.store.set('speed', cmd.value)
      await speak($, `Speed ${cmd.value}`)
      return { text: `TTS speed ${cmd.value}` }
    }

    if (cmd.kind === 'volume') {
      if (cmd.value === undefined) return { text: `TTS volume ${volume}/10` }
      await $.store.set('volume', cmd.value)
      await speak($, `Volume ${cmd.value}`)
      return { text: `TTS volume ${cmd.value}/10` }
    }

    const muted = await isMuted($)
    const next =
      cmd.kind === 'toggle' ? !muted : cmd.kind === 'mute' ? true : cmd.kind === 'unmute' ? false : muted
    if (cmd.kind !== 'status') {
      await $.state.set(MUTED, next)
      await showStatus($)
      if (next) await stop($)
    }
    const where = String((await $.store.get('devices')) ?? 'default')
    const pace = Number((await $.store.get('speed')) ?? DEFAULT_SPEED)
    return {
      text: `${next ? 'TTS muted' : 'TTS on'} (this session), volume ${volume}/10, speed ${pace}, output ${where}`,
    }
  })

  // New prompt: cut off whatever this session is still saying.
  on('turn.start', async ($, e, next) => {
    await stop($)
    return next(e)
  })

  let narratedTurn: string | undefined

  // Before the first tool call of a turn, read the narration that came ahead of it.
  on('turn.step', async function* ($, e, next) {
    let narration = ''
    for await (const chunk of next(e)) {
      if (chunk.kind === 'text') narration += chunk.text
      if (
        chunk.kind === 'tool' &&
        e.agentId === undefined &&
        narratedTurn !== e.turnId &&
        narration.trim().length > MIN_NARRATION &&
        !hasSummary(narration)
      ) {
        narratedTurn = e.turnId
        await speak($, speechText(narration))
      }
      yield chunk
    }
  })

  // The final answer comes from the event itself, so it is always the latest one.
  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined && e.reason === 'answer' && e.answer.trim()) {
      await speak($, speechText(e.answer))
    }
    return next(e)
  })

  on('session.end', async ($, e, next) => {
    await stop($)
    return next(e)
  })
}
