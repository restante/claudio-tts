declare module 'claude-code' {
  interface PluginState {
    // Whether this session is muted; unset until the person mutes or unmutes it here.
    'claudio-tts': { muted: boolean }
  }
}
