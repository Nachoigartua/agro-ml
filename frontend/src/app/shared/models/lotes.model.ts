export interface LoteItem {
  lote_id: string;
  nombre: string;
  latitud: number;
  longitud: number;
}

export interface LotesListResponse {
  total: number;
  items: LoteItem[];
}

