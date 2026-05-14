import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MapWidget } from './map-widget';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

describe('MapWidget', () => {
  let component: MapWidget;
  let fixture: ComponentFixture<MapWidget>;

  beforeEach(async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ type: 'FeatureCollection', features: [] }),
      })
    ) as jest.Mock;

    await TestBed.configureTestingModule({
      imports: [MapWidget],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideAnimationsAsync('noop')
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MapWidget);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});