
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import CodeGraphViewer from '../CodeGraphViewer';

// Mock react-force-graph-2d
vi.mock('react-force-graph-2d', () => ({
    default: () => <div data-testid="force-graph">Graph</div>
}));

describe('CodeGraphViewer', () => {
    const mockData = {
        nodes: [
            { id: '1', label: 'Main', type: 'entry_point', density: 0.8 },
            { id: '2', label: 'Utils', type: 'logic', density: 0.2 }
        ],
        edges: [
            { source: '1', target: '2', weight: 1 }
        ]
    };

    it('renders the graph container', () => {
        render(<CodeGraphViewer graphData={mockData} />);
        expect(screen.getByTestId('force-graph')).toBeInTheDocument();
    });

    it('displays loading state when no data', () => {
        render(<CodeGraphViewer graphData={null} />);
        expect(screen.getByText(/Loading Graph/i)).toBeInTheDocument();
    });
});
