import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { ReactiveFormsModule } from '@angular/forms';
import { RecomendacionesComponent } from './recomendaciones.component';

const routes: Routes = [
  {
    path: '',
    component: RecomendacionesComponent
  }
];

@NgModule({
  declarations: [
    RecomendacionesComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule.forChild(routes)
  ]
})
export class RecomendacionesModule { }