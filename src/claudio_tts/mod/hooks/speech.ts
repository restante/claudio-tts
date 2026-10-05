const OPEN = '<!-- TTS_SUMMARY'
const CLOSE = 'TTS_SUMMARY -->'

/** The text to read aloud for a reply: the TTS_SUMMARY block if present, else the whole text. */
export const speechText = (text: string): string => {
  const start = text.indexOf(OPEN)
  if (start !== -1) {
    const rest = text.slice(start + OPEN.length)
    const end = rest.indexOf(CLOSE)
    const summary = end === -1 ? '' : rest.slice(0, end).trim()
    if (summary) return summary
  }
  return text.trim().slice(0, 5000)
}

/** Narration before a tool call is skipped when it carries a summary block; the final answer reads that. */
export const hasSummary = (text: string): boolean => text.includes(OPEN)

export type TtsCommand =
  | { kind: 'toggle' | 'mute' | 'unmute' | 'status' }
  | { kind: 'volume'; value?: number }
  | { kind: 'device'; value?: string }
  | { kind: 'mic'; value?: string }
  | { kind: 'speed'; value?: number }
  | { kind: 'default'; value?: 'on' | 'off' }

export const DEFAULT_VOLUME = 10
export const DEFAULT_SPEED = 1
export const MIN_SPEED = 0.5
export const MAX_SPEED = 1.5

/** Parses `/tts` arguments; undefined when they make no sense. Volume is a whole number 1-10. */
export const parseTtsArgs = (args: string): TtsCommand | undefined => {
  const trimmed = args.trim()
  const [word = '', ...restWords] = trimmed.toLowerCase().split(/\s+/)
  const rest = restWords.join(' ')
  if (word === '') return { kind: 'toggle' }
  if (word === 'mute' || word === 'off') return { kind: 'mute' }
  if (word === 'unmute' || word === 'on') return { kind: 'unmute' }
  if (word === 'status') return { kind: 'status' }
  if (word === 'volume' || word === 'vol') {
    if (rest === '') return { kind: 'volume' }
    const value = Number(rest)
    return Number.isInteger(value) && value >= 1 && value <= 10 ? { kind: 'volume', value } : undefined
  }
  if (word === 'device' || word === 'devices' || word === 'output') {
    return rest === '' ? { kind: 'device' } : { kind: 'device', value: rest.replace(/\s*,\s*/g, ',') }
  }
  if (word === 'mic' || word === 'microphone') {
    const name = rest.replace(/\s*\(default\)\s*$/, '').trim()
    return name === '' ? { kind: 'mic' } : { kind: 'mic', value: name }
  }
  if (word === 'speed' || word === 'pace') {
    if (rest === '') return { kind: 'speed' }
    const value = Number(rest)
    return Number.isFinite(value) && value >= MIN_SPEED && value <= MAX_SPEED ? { kind: 'speed', value } : undefined
  }
  if (word === 'default' || word === 'startup') {
    if (rest === '') return { kind: 'default' }
    if (rest === 'on' || rest === 'off') return { kind: 'default', value: rest }
  }
  return undefined
}
