import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatDividerModule } from '@angular/material/divider';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatSidenavModule,
    MatDividerModule,
  ],
  templateUrl: './header.html',
  styleUrls: ['./header.less'],
})
export class HeaderComponent {
  isMobileMenuOpen = signal(false);

  user = signal({
    name: 'Анна',
    role: 'user',
    isAuthenticated: true,
  });

  isGov = computed(() => this.user().role === 'gov_org');
  isModerator = computed(() => this.user().role === 'moderator');

  toggleMobileMenu(): void {
    this.isMobileMenuOpen.update(v => !v);
  }

  logout(): void {
    console.log('logout');
  }
}