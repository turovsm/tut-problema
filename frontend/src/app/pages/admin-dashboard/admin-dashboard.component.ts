import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AdminApiService } from './admin-dashboard-api.service';
import { UserProfile } from '../../core/models/report.models';

@Component({
    selector: 'app-admin-dashboard',
    standalone: true,
    imports: [
        CommonModule,
        DatePipe,
        MatButtonModule,
        MatCardModule,
        MatChipsModule,
        MatProgressSpinnerModule
    ],
    templateUrl: './admin-dashboard.component.html',
    styleUrl: './admin-dashboard.component.less'
})
export class AdminDashboardComponent implements OnInit {
    private readonly adminApiService = inject(AdminApiService);

    readonly users = signal<UserProfile[]>([]);
    readonly isLoading = signal(false);
    readonly isLoadingMore = signal(false);
    readonly errorMessage = signal('');

    readonly page = signal(1);
    readonly limit = 20;
    readonly total = signal(0);
    readonly hasNext = signal(false);

    ngOnInit(): void {
        this.loadUsers();
    }

    loadUsers(page = 1): void {
        const isFirstPage = page === 1;

        if (isFirstPage) {
            this.isLoading.set(true);
            this.errorMessage.set('');
            this.users.set([]);
        } else {
            this.isLoadingMore.set(true);
        }

        this.adminApiService.getUsers(page, this.limit).subscribe({
            next: response => {
                this.users.set(isFirstPage ? response.items : [...this.users(), ...response.items]);
                this.page.set(response.page);
                this.total.set(response.total);
                this.hasNext.set(response.has_next);

                this.isLoading.set(false);
                this.isLoadingMore.set(false);
            },
            error: error => {
                console.error('Ошибка загрузки пользователей:', error);
                this.errorMessage.set('Не удалось загрузить список пользователей');
                this.isLoading.set(false);
                this.isLoadingMore.set(false);
            }
        });
    }

    loadMore(): void {
        if (this.isLoadingMore() || !this.hasNext()) return;
        this.loadUsers(this.page() + 1);
    }

    toggleUserStatus(user: UserProfile): void {
        if (user.role === 'moderator') {
            alert('Нельзя изменить статус модератора.');
            return;
        }

        const newStatus = !user.is_active;
        const actionText = newStatus ? 'разблокировать' : 'заблокировать';

        if (!confirm(`Вы уверены, что хотите ${actionText} пользователя ${user.username}?`)) {
            return;
        }

        this.adminApiService.toggleUserStatus(user.id, newStatus).subscribe({
            next: (updatedUser) => {
                this.users.update(users =>
                    users.map(u => u.id === updatedUser.id ? updatedUser : u)
                );
            },
            error: error => {
                console.error('Ошибка изменения статуса:', error);
                alert(error.error?.message || 'Не удалось изменить статус пользователя');
            }
        });
    }
}