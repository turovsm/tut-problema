import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { AuthService } from '../../core/auth/auth.service';
import { AuthComponent } from '../../features/auth/auth';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.html',
  styleUrls: ['./header.less'],
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatDividerModule,
    MatDialogModule
  ]
})
export class HeaderComponent {
  private readonly authService = inject(AuthService);
  private readonly dialog = inject(MatDialog);

  readonly isMobileMenuOpen = signal(false);

  readonly user = computed(() => {
    const currentUser = this.authService.currentUser();

    return {
      isAuthenticated: !!currentUser,
      name: currentUser?.user.username ?? currentUser?.user.email ?? '',
      role: currentUser?.user.role ?? null
    };
  });

  toggleMobileMenu(): void {
    this.isMobileMenuOpen.update(value => !value);
  }

  openLogin(): void {
    this.dialog.open(AuthComponent, {
      data: { mode: 'login' },
      width: '420px',
      maxWidth: 'calc(100vw - 32px)',
      panelClass: 'auth-dialog-panel'
    });
  }

  openRegister(): void {
    this.dialog.open(AuthComponent, {
      data: { mode: 'register' },
      width: '420px',
      maxWidth: 'calc(100vw - 32px)',
      panelClass: 'auth-dialog-panel'
    });
  }

  logout(): void {
    this.authService.logout().subscribe();
  }

  isGov(): boolean {
    return this.user().role === 'gov';
  }

  isModerator(): boolean {
    return this.user().role === 'moderator';
  }
}