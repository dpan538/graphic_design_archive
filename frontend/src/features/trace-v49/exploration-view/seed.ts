/* the presentation seed: FNV-1a over the state identity and a salt — pure,
   shared by the skeleton, the templates and the fingerprint */
export function presentationSeed(stateHash: string, salt: string): number {
  let hash = 0x811c9dc5;
  for (const character of `${stateHash}|${salt}`) {
    hash ^= character.codePointAt(0) ?? 0;
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash >>> 0;
}
