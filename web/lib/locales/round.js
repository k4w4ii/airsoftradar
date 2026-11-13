// Kerekített darabszám a főoldalon („30 000+”): a Google a szöveget hetekig gyorsítótárazza, a pontos szám hamar elavulna,
// a lefelé kerekített „+” viszont igaz marad, ahogy a katalógus nő.
export const roundDown = (n) => (n >= 10000 ? Math.floor(n / 1000) * 1000 : n >= 1000 ? Math.floor(n / 100) * 100 : n);
