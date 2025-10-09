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

  // Returns the Authorization header value expected by backend middleware
  getAuthToken(): string | null {
    if (!this.apiKey) {
      return null;
    }
    // Use Bearer scheme for future compatibility
    return `Bearer ${this.apiKey}`;
  }

  // TODO: replace stub with real authentication when backend is available
  isAuthenticated(): boolean {
    return true;
  }
}
