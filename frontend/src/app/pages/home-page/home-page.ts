import { Component } from '@angular/core';
import { MapWidget } from '../../shared/map-widget/map-widget';

@Component({
  selector: 'app-home-page',
  imports: [MapWidget],
  templateUrl: './home-page.html',
  styleUrl: './home-page.less',
})
export class HomePage {}
