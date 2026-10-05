import { expect, mock, test } from 'claude-code/testing'

import { hasSummary, parseTtsArgs, speechText } from './speech'

test('speechText prefers the TTS_SUMMARY block', () => {
  const text = 'Long answer.\n<!-- TTS_SUMMARY Short version. TTS_SUMMARY -->'
  expect(speechText(text)).toBe('Short version.')
  expect(hasSummary(text)).toBe(true)
})

test('speechText falls back to the whole text when the block is empty or open', () => {
  expect(speechText('Plain reply.')).toBe('Plain reply.')
  expect(speechText('Hi <!-- TTS_SUMMARY never closed')).toBe('Hi <!-- TTS_SUMMARY never closed')
  expect(speechText('A <!-- TTS_SUMMARY  TTS_SUMMARY -->')).toContain('A')
})

test('parseTtsArgs', () => {
  expect(parseTtsArgs('')).toEqual({ kind: 'toggle' })
  expect(parseTtsArgs(' Mute ')).toEqual({ kind: 'mute' })
  expect(parseTtsArgs('unmute')).toEqual({ kind: 'unmute' })
  expect(parseTtsArgs('status')).toEqual({ kind: 'status' })
  expect(parseTtsArgs('volume')).toEqual({ kind: 'volume' })
  expect(parseTtsArgs('volume 7')).toEqual({ kind: 'volume', value: 7 })
  expect(parseTtsArgs('volume 0')).toBeUndefined()
  expect(parseTtsArgs('volume 11')).toBeUndefined()
  expect(parseTtsArgs('volume 2.5')).toBeUndefined()
  expect(parseTtsArgs('device')).toEqual({ kind: 'device' })
  expect(parseTtsArgs('device AirPods , MacBook')).toEqual({ kind: 'device', value: 'airpods,macbook' })
  expect(parseTtsArgs('device all')).toEqual({ kind: 'device', value: 'all' })
  expect(parseTtsArgs('mic')).toEqual({ kind: 'mic' })
  expect(parseTtsArgs('mic MacBook Pro Microphone (default)')).toEqual({ kind: 'mic', value: 'macbook pro microphone' })
  expect(parseTtsArgs('speed')).toEqual({ kind: 'speed' })
  expect(parseTtsArgs('speed 0.8')).toEqual({ kind: 'speed', value: 0.8 })
  expect(parseTtsArgs('pace 1.25')).toEqual({ kind: 'speed', value: 1.25 })
  expect(parseTtsArgs('speed 2')).toBeUndefined()
  expect(parseTtsArgs('speed 0.2')).toBeUndefined()
  expect(parseTtsArgs('speed fast')).toBeUndefined()
  expect(parseTtsArgs('default')).toEqual({ kind: 'default' })
  expect(parseTtsArgs('default on')).toEqual({ kind: 'default', value: 'on' })
  expect(parseTtsArgs('default off')).toEqual({ kind: 'default', value: 'off' })
  expect(parseTtsArgs('default maybe')).toBeUndefined()
  expect(parseTtsArgs('voice')).toEqual({ kind: 'voice' })
  expect(parseTtsArgs('voices')).toEqual({ kind: 'voice' })
  expect(parseTtsArgs('voice af_bella')).toEqual({ kind: 'voice', value: 'af_bella' })
  expect(parseTtsArgs('voice DEFAULT')).toEqual({ kind: 'voice', value: 'default' })
  expect(parseTtsArgs('lang')).toEqual({ kind: 'lang' })
  expect(parseTtsArgs('lang DE')).toEqual({ kind: 'lang', value: 'de' })
  expect(parseTtsArgs('language auto')).toEqual({ kind: 'lang', value: 'auto' })
  expect(parseTtsArgs('nope')).toBeUndefined()
})

test('/tts mutes, persists and unmutes', async ($, on) => {
  mock.store(on)
  const run = (args: string) =>
    $.command.run({ command: 'tts', args, origin: { kind: 'composer' }, presentation: { layout: 'main', columns: 80 } } as never)
  expect(((await run('mute')) as { text: string }).text).toContain('TTS muted')
  expect(((await run('status')) as { text: string }).text).toContain('TTS muted')
  expect(((await run('')) as { text: string }).text).toContain('TTS on')
})

test('/tts volume persists and reports', async ($, on) => {
  mock.store(on)
  const run = (args: string) =>
    $.command.run({ command: 'tts', args, origin: { kind: 'composer' }, presentation: { layout: 'main', columns: 80 } } as never)
  expect(((await run('volume')) as { text: string }).text).toBe('TTS volume 10/10')
  expect(((await run('volume 4')) as { text: string }).text).toBe('TTS volume 4/10')
  expect(((await run('volume')) as { text: string }).text).toBe('TTS volume 4/10')
  expect(((await run('volume 99')) as { text: string }).text).toContain('Usage')
})

test('/tts speed persists and reports', async ($, on) => {
  mock.store(on)
  const run = (args: string) =>
    $.command.run({ command: 'tts', args, origin: { kind: 'composer' }, presentation: { layout: 'main', columns: 80 } } as never)
  expect(((await run('speed')) as { text: string }).text).toContain('TTS speed 1')
  expect(((await run('speed 0.8')) as { text: string }).text).toBe('TTS speed 0.8')
  expect(((await run('speed')) as { text: string }).text).toContain('TTS speed 0.8')
  expect(((await run('speed 3')) as { text: string }).text).toContain('Usage')
})

test('a new session starts muted until it is unmuted or the default changes', async ($, on) => {
  mock.store(on)
  const run = (args: string) =>
    $.command.run({ command: 'tts', args, origin: { kind: 'composer' }, presentation: { layout: 'main', columns: 80 } } as never)
  expect(((await run('status')) as { text: string }).text).toContain('TTS muted')
  expect(((await run('default')) as { text: string }).text).toContain('muted')
  expect(((await run('default on')) as { text: string }).text).toContain('speaking')
  expect(((await run('status')) as { text: string }).text).toContain('TTS on')
  expect(((await run('mute')) as { text: string }).text).toContain('TTS muted')
})

test('a finished answer is handed to the speak command on stdin', async ($, on) => {
  mock.store(on)
  mock.env(on, { CLAUDIO_TTS_PYTHON: '/py' })
  const calls: { argv: readonly string[]; stdin?: string }[] = []
  on('process.run', async (_$, e) => {
    calls.push({ argv: e.argv, stdin: e.init?.stdin })
    return {
      value: { exitCode: 0, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false },
    }
  })
  on('turn.complete', (_$, e) => ({ text: e.answer }))
  const run = (args: string) =>
    $.command.run({ command: 'tts', args, origin: { kind: 'composer' }, presentation: { layout: 'main', columns: 80 } } as never)
  await run('unmute')
  await $.turn.complete({ answer: 'Hello **world**', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' } as never)
  const spoke = calls.find(c => c.argv.includes('speak'))
  expect(spoke?.argv.slice(0, 3)).toEqual(['/py', '-m', 'claudio_tts'])
  expect(spoke?.stdin).toBe('Hello **world**')
})

test('/tts voice validates through the CLI, stores the choice and passes it to speak', async ($, on) => {
  mock.store(on)
  mock.env(on, { CLAUDIO_TTS_PYTHON: '/py' })
  const calls: { argv: readonly string[]; stdin?: string }[] = []
  on('process.run', async (_$, e) => {
    calls.push({ argv: e.argv, stdin: e.init?.stdin })
    const isBad = e.argv.includes('--check') && e.argv.includes('af_nope')
    return {
      value: {
        exitCode: isBad ? 1 : 0,
        stdout: isBad ? "unknown voice 'af_nope'" : '',
        stderr: '',
        isStdoutTruncated: false,
        isStderrTruncated: false,
      },
    }
  })
  on('turn.complete', (_$, e) => ({ text: e.answer }))
  const run = (args: string) =>
    $.command.run({ command: 'tts', args, origin: { kind: 'composer' }, presentation: { layout: 'main', columns: 80 } } as never)
  await run('unmute')
  expect(((await run('voice af_nope')) as { text: string }).text).toContain('unknown voice')
  expect(((await run('voice af_bella')) as { text: string }).text).toBe('Voice: af_bella')
  calls.length = 0
  await $.turn.complete({ answer: 'Hi there', durationMs: 1, isAborted: false, turnId: 't2', reason: 'answer' } as never)
  const spoke = calls.find(c => c.argv.includes('speak'))
  expect(spoke?.argv).toContain('--voice')
  expect(spoke?.argv[spoke.argv.indexOf('--voice') + 1]).toBe('af_bella')
  expect(((await run('voice default')) as { text: string }).text).toContain('reset')
})

test('/tts lang validates through the CLI, stores the code and passes it to speak', async ($, on) => {
  mock.store(on)
  mock.env(on, { CLAUDIO_TTS_PYTHON: '/py' })
  const calls: { argv: readonly string[] }[] = []
  on('process.run', async (_$, e) => {
    calls.push({ argv: e.argv })
    const isBad = e.argv.includes('--check') && e.argv.includes('zz')
    return {
      value: {
        exitCode: isBad ? 1 : 0,
        stdout: isBad ? "unknown language 'zz'" : '',
        stderr: '',
        isStdoutTruncated: false,
        isStderrTruncated: false,
      },
    }
  })
  on('turn.complete', (_$, e) => ({ text: e.answer }))
  const run = (args: string) =>
    $.command.run({ command: 'tts', args, origin: { kind: 'composer' }, presentation: { layout: 'main', columns: 80 } } as never)
  await run('unmute')
  expect(((await run('lang zz')) as { text: string }).text).toContain('unknown language')
  expect(((await run('lang DE')) as { text: string }).text).toContain('Language: de')
  calls.length = 0
  await $.turn.complete({ answer: 'Guten Tag', durationMs: 1, isAborted: false, turnId: 't3', reason: 'answer' } as never)
  const spoke = calls.find(c => c.argv.includes('speak'))
  expect(spoke?.argv[spoke.argv.indexOf('--lang') + 1]).toBe('de')
  expect(((await run('lang auto')) as { text: string }).text).toContain('auto')
})
