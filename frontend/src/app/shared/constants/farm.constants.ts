export interface LoteOption {
  label: string;
  value: string;
}

export const CULTIVOS_DISPONIBLES: readonly string[] = [
  'trigo',
  'soja',
  'maiz',
  'cebada',
] as const;

export const LOTES_DISPONIBLES: readonly LoteOption[] = [
  { label: 'lote-001', value: 'c3f2f1ab-ca2e-4f8b-9819-377102c4d889' },
  { label: 'lote-002', value: 'f6c1d3e9-4aa7-4b24-8b1c-65f06e3f4d30' },
] as const;

export const CAMPANAS_DISPONIBLES: readonly string[] = [
  '2025/2026',
  '2026/2027',
  '2027/2028',
] as const;
