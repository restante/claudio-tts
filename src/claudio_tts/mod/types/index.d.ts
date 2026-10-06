declare module 'claude-code' {
  interface PluginState {
    // `disabled`: this session is switched off completely (/tts disable).
    // Whether this session is muted; unset until the person mutes or unmutes it here.
    'claudio-tts': { muted: boolean; disabled: boolean }
  }
}
