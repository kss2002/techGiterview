import React from 'react';
import { WORKFLOW_STEPS } from '../../constants/features';
import type { WorkflowStep } from '../../types/homePage';

export const WorkflowSection: React.FC = () => {
  return (
    <section className="section">
      <div className="container">
        <h2 className="heading-2 text-center">작동 원리</h2>
        <div className="flex justify-center items-center gap-lg flex-wrap">
          {WORKFLOW_STEPS.map((step: WorkflowStep, index) => (
            <React.Fragment key={step.id}>
              <div className="card hover-scale-sm animate-fade-in-up text-center position-relative">
                <div className="card-body">
                  <div className="badge badge-primary text-lg mb-4">
                    {step.step}
                  </div>
                  <h3 className="heading-4">{step.title}</h3>
                  <p className="text-body-sm">{step.description}</p>
                </div>
              </div>

              {index < WORKFLOW_STEPS.length - 1 && (
                <div className="step-arrow-new">→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
};
