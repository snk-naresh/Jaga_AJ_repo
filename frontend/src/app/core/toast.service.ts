import {Injectable, signal} from '@angular/core';

@Injectable({providedIn: 'root'})
export class ToastService {
  text = signal('');
  private timer: any;
  show(message: string) {
    this.text.set(message);
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.text.set(''), 3200);
  }
}
