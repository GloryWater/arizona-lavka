const CP1251_EXTRA: Record<number, number> = {
  0x0401: 0xa8,
  0x0451: 0xb8,
  0x0404: 0xaa,
  0x0454: 0xba,
  0x0406: 0xb2,
  0x0456: 0xb3,
  0x0407: 0xaf,
  0x0457: 0xbf,
};

function encodeCP1251(input: string) {
  const bytes: number[] = [];

  for (const char of input) {
    const code = char.charCodeAt(0);

    if (code < 0x80) {
      bytes.push(code);
    } else if (code >= 0x0410 && code <= 0x044f) {
      bytes.push(code - 0x350);
    } else {
      bytes.push(CP1251_EXTRA[code] ?? 0x3f);
    }
  }

  return new Uint8Array(bytes);
}

export function createCP1251Blob(input: string) {
  return new Blob([encodeCP1251(input)], {
    type: 'application/json;charset=windows-1251',
  });
}
