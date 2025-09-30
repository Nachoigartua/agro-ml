import { Injectable } from '@angular/core';
import { environment } from '@environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiKey = environment.apiKey;

  constructor() {}

  getApiKey(): string {
    return this.apiKey;
  }

  // En una implementación real, aquí manejarías autenticación con tokens JWT
  isAuthenticated(): boolean {
    return true; // Por ahora siempre autenticado
  }
}