import { HttpInterceptorFn } from '@angular/common/http';

export const apiKeyInterceptor: HttpInterceptorFn = (req, next) => {
  const cloned = req.clone({ setHeaders: { 'x-api-key': 'dev-local-key' } });
  return next(cloned);
};
