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
    },
    {
    path: 'reports/:report_id',
    loadComponent: () =>
      import('./features/report-details/report-details')
        .then(m => m.ReportDetailsComponent)
    },
    {
        path: 'reports/:report_id/edit',
        loadComponent: () =>
            import('./features/report-details/report-edit/report-edit')
            .then(m => m.ReportEditComponent)
    }
];
