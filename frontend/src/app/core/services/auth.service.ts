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

  // TODO: replace stub with real authentication when backend is available
  isAuthenticated(): boolean {
    return true;
  }
}
