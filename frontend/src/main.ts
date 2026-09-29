import {bootstrapApplication} from '@angular/platform-browser';
import {provideRouter, Routes} from '@angular/router';
import {provideHttpClient, withInterceptors} from '@angular/common/http';
import {AppComponent} from './app/app.component';
import {authInterceptor} from './app/core/auth.interceptor';
import {LoginComponent} from './app/features/dashboard/login.component';
import {DashboardComponent} from './app/features/dashboard/dashboard.component';
import {CustomersComponent} from './app/features/customers/customers.component';
import {CustomerDetailComponent} from './app/features/customers/customer-detail.component';
import {OrdersComponent} from './app/features/orders/orders.component';
import {OrderFormComponent} from './app/features/orders/order-form.component';
import {OrderDetailComponent} from './app/features/orders/order-detail.component';
import {InventoryComponent} from './app/features/inventory/inventory.component';
import {NotificationsComponent} from './app/features/notifications/notifications.component';
import {ReportsComponent} from './app/features/reports/reports.component';
import {SettingsComponent} from './app/features/settings/settings.component';
import {SecurityComponent} from './app/features/settings/security.component';
import {adminGuard, authGuard} from './app/core/auth.guard';

const guard = {canActivate: [authGuard]};
const routes: Routes = [
  {path: 'login', component: LoginComponent},
  {path: '', component: DashboardComponent, ...guard},
  {path: 'customers', component: CustomersComponent, ...guard},
  {path: 'customers/:id', component: CustomerDetailComponent, ...guard},
  {path: 'orders', component: OrdersComponent, ...guard},
  {path: 'orders/new', component: OrderFormComponent, ...guard},
  {path: 'orders/:id', component: OrderDetailComponent, ...guard},
  {path: 'inventory', component: InventoryComponent, ...guard},
  {path: 'notifications', component: NotificationsComponent, ...guard},
  {path: 'reports', component: ReportsComponent, ...guard},
  {path: 'settings', component: SettingsComponent, ...guard},
  {path: 'security', component: SecurityComponent, canActivate: [adminGuard]},
  {path: '**', redirectTo: ''}
];

bootstrapApplication(AppComponent, {providers: [provideRouter(routes), provideHttpClient(withInterceptors([authInterceptor]))]}).catch(console.error);
