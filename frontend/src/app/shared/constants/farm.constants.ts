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
  { label: 'Pergamino Norte', value: 'c3f2f1ab-ca2e-4f8b-9819-377102c4d889' },
  { label: 'Sur Córdoba', value: 'f6c1d3e9-4aa7-4b24-8b1c-65f06e3f4d30' },
  { label: 'Cordillera Neuquén', value: 'a17c9db2-5588-4b71-8f8a-6a54b1ad7eaa' },
  { label: 'Entre Ríos Norte', value: 'd5bf2bcd-9289-4bb0-9c35-5c3750086511' }
] as const;

export const CAMPANAS_DISPONIBLES: readonly string[] = [
  '2025/2026',
  '2026/2027',
  '2027/2028',
] as const;
