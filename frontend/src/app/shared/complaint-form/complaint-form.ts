import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

export interface ComplaintFormValue {
  type: string;
  description: string;
  photos: File[];
  lat: number;
  lng: number;
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
    MatSelectModule
  ]
})
export class ComplaintFormComponent {
  private readonly fb = inject(FormBuilder);

  @Input({ required: true }) types: string[] = [];
  @Input({ required: true }) lat!: number;
  @Input({ required: true }) lng!: number;
  @Input() address?: string;

  @Output() formSubmit = new EventEmitter<ComplaintFormValue>();
  @Output() cancel = new EventEmitter<void>();

  selectedFiles: File[] = [];

  complaintForm = this.fb.group({
    type: ['', Validators.required],
    description: ['', [Validators.required, Validators.minLength(10)]],
    photos: [[] as File[]]
  });

  onFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (!input.files?.length) {
      this.selectedFiles = [];
      this.complaintForm.patchValue({ photos: [] });
      return;
    }

    this.selectedFiles = Array.from(input.files);

    this.complaintForm.patchValue({
      photos: this.selectedFiles
    });
  }

  submit(): void {
    if (this.complaintForm.invalid) {
      this.complaintForm.markAllAsTouched();
      return;
    }

    this.formSubmit.emit({
      type: this.complaintForm.value.type ?? '',
      description: this.complaintForm.value.description ?? '',
      photos: this.selectedFiles,
      lat: this.lat,
      lng: this.lng
    });
  }

  close(): void {
    this.cancel.emit();
  }
}