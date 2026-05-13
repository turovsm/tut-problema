import { Route } from '@angular/router';
import { HomePage } from './pages/home-page/home-page';
import { VerifyEmailPage } from './pages/verify-email/verify-email';

export const appRoutes: Route[] = [
    {
        path: '',
        component: HomePage,
    },
    {
        path: 'auth/verify-email',
        component: VerifyEmailPage
    },
    {
        path: 'profile',
        loadComponent: () =>
            import('./pages/profile-page/profile')
            .then(m => m.ProfilePageComponent)
    }
];
