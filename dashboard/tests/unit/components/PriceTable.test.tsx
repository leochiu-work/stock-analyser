import { render, screen } from '@testing-library/react';
import { PriceTable } from '@/components/prices/PriceTable';
import { StockPriceItem } from '@/lib/types';

const mockData: StockPriceItem[] = [
  { ticker: 'AAPL', date: '2024-01-15', open: 185.0, high: 188.5, low: 184.0, close: 187.2 },
  { ticker: 'AAPL', date: '2024-01-16', open: 187.2, high: 190.0, low: 186.0, close: 185.5 },
];

describe('PriceTable', () => {
  it('renders OHLC column headers', () => {
    render(<PriceTable data={mockData} />);
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Open')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
    expect(screen.getByText('Close')).toBeInTheDocument();
  });

  it('renders correct number of rows (1 header + N data rows)', () => {
    render(<PriceTable data={mockData} />);
    const rows = screen.getAllByRole('row');
    // 1 header row + 2 data rows
    expect(rows).toHaveLength(3);
  });

  it('renders empty state text when data is empty', () => {
    render(<PriceTable data={[]} />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('renders loading skeleton instead of table when isLoading is true', () => {
    const { container } = render(<PriceTable data={[]} isLoading />);
    expect(container.querySelector('table')).not.toBeInTheDocument();
  });

  it('renders loading skeleton rows when isLoading is true', () => {
    const { container } = render(<PriceTable data={[]} isLoading />);
    // LoadingSkeleton renders divs, not table rows
    const skeletonDivs = container.querySelectorAll('[class*="skeleton"], [class*="animate"]');
    expect(skeletonDivs.length).toBeGreaterThan(0);
  });

  it('formats close price as currency', () => {
    render(<PriceTable data={mockData} />);
    // The close cell renders a <span> with the formatted value inside a <td>.
    // getAllByText returns both the span and the td (since the td's textContent
    // also matches). We verify at least one element contains the value.
    const matches = screen.getAllByText('$187.20');
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it('colors close green when close >= open (bullish row)', () => {
    render(<PriceTable data={mockData} />);
    // First row: open=185, close=187.2 → green
    // The span is the first element returned by getAllByText
    const allMatches = screen.getAllByText('$187.20');
    const coloredSpan = allMatches.find((el) => el.tagName === 'SPAN');
    expect(coloredSpan).toHaveClass('text-green-600');
  });

  it('colors close red when close < open (bearish row)', () => {
    render(<PriceTable data={mockData} />);
    // Second row: open=187.2, close=185.5 → red
    const allMatches = screen.getAllByText('$185.50');
    const coloredSpan = allMatches.find((el) => el.tagName === 'SPAN');
    expect(coloredSpan).toHaveClass('text-red-600');
  });

  it('formats open price as currency', () => {
    render(<PriceTable data={mockData} />);
    const matches = screen.getAllByText('$185.00');
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it('renders a table element when not loading', () => {
    const { container } = render(<PriceTable data={mockData} />);
    expect(container.querySelector('table')).toBeInTheDocument();
  });
});
