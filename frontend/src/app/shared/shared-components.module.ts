import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SiembraRecommendationDetailComponent } from './components/siembra-recommendation-detail/siembra-recommendation-detail.component';

@NgModule({
  declarations: [SiembraRecommendationDetailComponent],
  imports: [CommonModule],
  exports: [SiembraRecommendationDetailComponent],
})
export class SharedComponentsModule {}
