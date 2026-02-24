import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders homepage title', () => {
  render(<App />);
  expect(
    screen.getByText(/분석할 GitHub 저장소를 입력하세요/i)
  ).toBeInTheDocument();
});
