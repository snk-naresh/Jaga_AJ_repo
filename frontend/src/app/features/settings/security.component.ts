import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ApiService, apiMessage} from '../../core/api.service';

@Component({
  standalone: true,
  imports: [CommonModule],
  template: `
    <h1>Security access</h1>
    <p class="lead">Each sign-in is saved here, including when two browsers are used at the same time</p>
    <p class="muted" *ngIf="loading">Loading access records…</p>
    <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
    <article class="card" *ngIf="!loading && !error">
      <div class="empty" *ngIf="!signIns.length">No access records yet.</div>
      <div class="table-wrap" *ngIf="signIns.length">
        <table>
          <tr><th>When</th><th>Username</th><th>Role</th><th>Browser</th><th>Address</th></tr>
          <tr *ngFor="let row of signIns">
            <td>{{row.created_at | date:'short'}}</td>
            <td>{{row.username}}</td>
            <td>{{row.role}}</td>
            <td>{{row.browser}}</td>
            <td>{{row.ip || '—'}}</td>
          </tr>
        </table>
      </div>
    </article>
    <article class="card" style="margin-top:12px" *ngIf="!loading && !error">
      <h2>Edited records</h2>
      <div class="empty" *ngIf="!edits.length">No phone corrections yet.</div>
      <div class="table-wrap" *ngIf="edits.length">
        <table>
          <tr><th>When</th><th>Username</th><th>Role</th><th>Customer</th><th>Previous phone</th><th>Saved phone</th></tr>
          <tr *ngFor="let row of edits">
            <td>{{row.created_at | date:'short'}}</td>
            <td>{{row.username}}</td>
            <td>{{row.role}}</td>
            <td>{{row.customer}}</td>
            <td>{{row.previous_phone}}</td>
            <td>{{row.phone}}</td>
          </tr>
        </table>
      </div>
    </article>
  `
})
export class SecurityComponent {
  api = inject(ApiService);
  signIns: any[] = [];
  edits: any[] = [];
  loading = true;
  error = '';
  constructor() { this.load(); }
  load() {
    this.loading = true;
    this.error = '';
    this.api.get<any>('/access').subscribe({
      next: (page) => { this.signIns = page.sign_ins || []; this.edits = page.edits || []; this.loading = false; },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
}
