import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Agregar API key a todas las peticiones
    const apiKey = this.authService.getApiKey();
    
    const modifiedRequest = request.clone({
      setHeaders: {
        'x-api-key': apiKey,
        'Content-Type': 'application/json'
      }
    });

    return next.handle(modifiedRequest).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          console.error('No autorizado - API key inválida');
        } else if (error.status === 429) {
          console.error('Demasiadas peticiones - rate limit excedido');
        } else if (error.status >= 500) {
          console.error('Error del servidor');
        }
        
        return throwError(() => error);
      })
    );
  }
}