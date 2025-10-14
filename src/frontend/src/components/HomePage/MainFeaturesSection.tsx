import React from 'react';
import { MAIN_FEATURES } from '../../constants/features';
import type { FeatureItem } from '../../types/homePage';

export const MainFeaturesSection: React.FC = () => {
  return (
    <section className="section">
      <div className="container">
        <h2 className="heading-2 text-center">주요 기능</h2>
        <div className="grid grid-auto-fit gap-lg">
          {MAIN_FEATURES.map((feature: FeatureItem) => (
            <div
              key={feature.id}
              className="card hover-lift-sm animate-fade-in text-center"
            >
              <div className="card-body">
                <div className="text-5xl mb-4">{feature.icon}</div>
                <h3 className="heading-3">{feature.title}</h3>
                <p className="text-body">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
