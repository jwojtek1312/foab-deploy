import { Component, ElementRef } from '@angular/core';
import { RouterOutlet } from '@angular/router';
declare const M:any;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})

export class AppComponent {
  title = 'foab-webpages';

}
