import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

export interface ComplaintFormValue {
  title: string;
  description: string | null;
  issue_type: string;
  files: File[];
  location_lat: number;
  location_lng: number;
}

@Component({
  selector: 'app-complaint-form',
  standalone: true,
  templateUrl: './complaint-form.html',
  styleUrls: ['./complaint-form.less'],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
})
export class ComplaintFormComponent {
  private readonly fb = inject(FormBuilder);

  types = [
    { value: 'snow', label: 'Снег' },
    { value: 'pothole', label: 'Яма' },
    { value: 'road_obstruction', label: 'Препятствие на дороге' },
    { value: 'flooding', label: 'Подтопление' },
    { value: 'broken_streetlight', label: 'Неисправное освещение' },
    { value: 'broken_sidewalk', label: 'Сломанный тротуар' },
    { value: 'water_leak', label: 'Утечка воды' },
    { value: 'sewer_overflow', label: 'Проблема с канализацией' },
    { value: 'illegal_dumping', label: 'Незаконная свалка' },
    { value: 'other', label: 'Другое' },
  ];
  @Input({ required: true }) lat!: number;
  @Input({ required: true }) lng!: number;
  @Input() address?: string;

  @Output() formSubmit = new EventEmitter<ComplaintFormValue>();
  @Output() formCancel = new EventEmitter<void>();

  selectedFiles: File[] = [];

  complaintForm = this.fb.group({
    title: [
      '',
      [Validators.required, Validators.minLength(5), Validators.maxLength(200)],
    ],
    type: ['', Validators.required],
    description: ['', [Validators.required, Validators.minLength(10)]],
    files: [[] as File[]],
  });

  onFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (!input.files?.length) {
      this.selectedFiles = [];
      this.complaintForm.patchValue({ files: [] });
      return;
    }

    this.selectedFiles = Array.from(input.files);

    this.complaintForm.patchValue({
      files: this.selectedFiles,
    });
  }

  submit(): void {
    if (this.complaintForm.invalid) {
      this.complaintForm.markAllAsTouched();
      return;
    }

    this.formSubmit.emit({
      title: this.complaintForm.value.title ?? '',
      description: this.complaintForm.value.description || null,
      issue_type: this.complaintForm.value.type ?? '',
      files: this.selectedFiles,
      location_lat: this.lat,
      location_lng: this.lng,
    });
  }

  close(): void {
    this.formCancel.emit();
  }
}
