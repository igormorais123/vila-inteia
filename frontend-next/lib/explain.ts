export function pct(value: number | null | undefined, digits = 1): string {
  const n = typeof value === "number" && Number.isFinite(value) ? value : 0;
  return `${(n * 100).toFixed(digits)}%`;
}

export function shortName(name: string): string {
  const aliases: Array<[string, string]> = [
    ["Luiz Inácio Lula", "Lula"],
    ["Lula", "Lula"],
    ["Tarcísio", "Tarcísio"],
    ["Ratinho", "Ratinho Jr."],
    ["Romeu Zema", "Zema"],
    ["Guilherme Boulos", "Boulos"],
    ["Boulos", "Boulos"],
  ];
  const found = aliases.find(([needle]) => name.includes(needle));
  if (found) return found[1];
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return parts.length ? parts[0] : name;
}

export function chanceBand(value: number): string {
  if (value >= 0.75) return "favorito forte";
  if (value >= 0.6) return "favorito";
  if (value >= 0.5) return "leve vantagem";
  if (value >= 0.35) return "disputa equilibrada";
  if (value >= 0.2) return "lidera em campo dividido";
  if (value >= 0.1) return "ainda competitivo";
  return "chance baixa";
}

export function marginReading(pp: number): string {
  const gap = Math.abs(pp);
  if (gap < 3) return "vantagem pequena, cenário muito sensível a novas pesquisas";
  if (gap < 10) return "vantagem clara, mas ainda reversível";
  return "vantagem larga no retrato atual";
}

export function plainStatusNote(note?: string): string {
  return (note || "")
    .replaceAll("SP gov", "governo de SP")
    .replaceAll("def federal", "deputado federal")
    .replaceAll(" vs ", " contra ")
    .replaceAll("=", "é");
}
