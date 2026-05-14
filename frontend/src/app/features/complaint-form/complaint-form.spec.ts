import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ComplaintFormComponent } from './complaint-form';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

describe('ComplaintFormComponent', () => {
  let component: ComplaintFormComponent;
  let fixture: ComponentFixture<ComplaintFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComplaintFormComponent],
      providers: [provideAnimationsAsync('noop')]
    }).compileComponents();

    fixture = TestBed.createComponent(ComplaintFormComponent);
    component = fixture.componentInstance;

    component.lat = 58.0;
    component.lng = 56.25;

    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});