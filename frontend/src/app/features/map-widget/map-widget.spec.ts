import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MapWidget } from './map-widget';

describe('MapWidget', () => {
  let component: MapWidget;
  let fixture: ComponentFixture<MapWidget>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MapWidget],
    }).compileComponents();

    fixture = TestBed.createComponent(MapWidget);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
