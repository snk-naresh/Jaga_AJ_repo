import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ApiService, apiMessage} from '../../core/api.service';

@Component({
  standalone: true,
  imports: [CommonModule],
  template: `
    <h1>Settings</h1>
    <p class="lead">Account, WhatsApp mode, and the audit trail</p>
    <p class="muted" *ngIf="loading">Loading settings…</p>
    <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
    <section class="split" *ngIf="me">
      <article class="card">
        <h2>Signed in</h2>
        <p><b>{{me.username}}</b></p>
        <p>Role {{me.role}}</p>
        <p *ngIf="status">WhatsApp mode: {{status.whatsapp_mode}}</p>
        <p *ngIf="status">Photo storage: {{status.storage_configured ? 'configured' : 'not configured'}}</p>
        <div class="empty" *ngIf="!users.length && me.role==='ADMIN'">No other staff accounts are listed.</div>
        <table *ngIf="users.length">
          <tr><th>Username</th><th>Role</th><th>Active</th></tr>
          <tr *ngFor="let user of users"><td>{{user.username}}</td><td>{{user.role}}</td><td>{{user.is_active ? 'Yes' : 'No'}}</td></tr>
        </table>
      </article>
      <article class="card">
        <h2>Recent audit</h2>
        <div class="empty" *ngIf="!audit.length">No audit events yet.</div>
        <p *ngFor="let event of audit"><b>{{event.event_type}}</b> · {{event.entity}} {{event.entity_id}}<br><span class="muted">{{event.user || 'system'}} · {{event.created_at | date:'short'}}</span></p>
      </article>
    </section>
  `
})
export class SettingsComponent {
  api = inject(ApiService);
  me: any = null;
  status: any = null;
  users: any[] = [];
  audit: any[] = [];
  loading = true;
  error = '';
  constructor() { this.load(); }
  load() {
    this.loading = true;
    this.error = '';
    this.api.get<any>('/auth/me').subscribe({
      next: (me) => {
        this.me = me;
        this.api.get<any>('/system/status').subscribe({next: (status) => this.status = status});
        this.api.get<any[]>('/audit').subscribe({next: (rows) => this.audit = rows});
        if (me.role === 'ADMIN') this.api.get<any[]>('/users').subscribe({next: (rows) => this.users = rows});
        this.loading = false;
      },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
}
